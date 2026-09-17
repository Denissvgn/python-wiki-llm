"""Explicit migration, recovery, export and cleanup of generated knowledge."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from .filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory, unlink_guarded_bytes
from .knowledge_artifacts import (
    ArtifactWriteState, KnowledgeCommitPlan, PlannedArtifactWrite,
    build_knowledge_commit_plan, commit_knowledge_artifacts, current_knowledge_format,
    validate_knowledge_artifacts, validated_artifact_bytes, _commit_sharded,
)
from .knowledge_governance import GOVERNANCE_FILENAME, governance_lock
from .knowledge_index import serialize_knowledge_index
from .knowledge_loader import load_knowledge_state
from .knowledge_storage import (
    MAX_EXPANDED_BYTES, MAX_OBJECT_BYTES, OBJECT_DIRECTORY, ROOT_FILENAME,
    GIT_FAILURE_BYTES, KnowledgeStorageError, KnowledgeStoreReader, decode_bytes,
    canonical_bytes, digest, _hash,
)
from .knowledge_storage_io import StorageReadSession, read_guarded, _absolute_path
from .knowledge_packs import (
    PACKED_SCHEMA, LOCAL_PACKED_SCHEMA, PACKED_SCHEMAS, PACKED_FORMATS, packed_format,
    PACK_NAME, INDEX_NAME, PACK_DIRECTORY, PACK_INDEX_DIRECTORY,
    INDEX_PAGE_NAME, INDEX_PAGE_DIRECTORY, PackedKnowledgeStoreReader, inspect_pack, inspect_index_pages,
)
from .sync_manifest import MANIFEST_FILENAME, SyncManifest
from .manifest_storage import OBJECT_NAME as MANIFEST_OBJECT_NAME, DIRECTORY as MANIFEST_DIRECTORY, validate_catalog
from .wiki_surface_index import SURFACE_INDEX_FILENAME

RECOVERY_SCHEMA = "llm-wiki-knowledge-recovery/v2"
_OBJECT_NAME = re.compile(r"\.llm-wiki-knowledge/objects/([0-9a-f]{2})/\1[0-9a-f]{62}\.json\Z")


def _committed_inputs(wiki_dir: str | Path):
    state = load_knowledge_state(wiki_dir)
    if state.knowledge is None or state.manifest_basis is None or state.validated_artifacts is None:
        raise KnowledgeStorageError("knowledge", "a fully valid committed snapshot is required")
    session = StorageReadSession(wiki_dir)
    surface, knowledge = validated_artifact_bytes(state.validated_artifacts)
    expected = {SURFACE_INDEX_FILENAME: surface, ROOT_FILENAME: knowledge,
                **state.validated_artifacts.storage_objects}
    for name, content in expected.items():
        if session.read(name, len(content)) != content:
            raise KnowledgeStorageError(name, "changed after validation", code="storage-mutation")
    manifest_bytes = session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)
    if SyncManifest.from_payload(json.loads(manifest_bytes), object_reader=session.read).to_payload() != state.manifest_basis.to_payload():
        raise KnowledgeStorageError("manifest", "changed after validation", code="storage-mutation")
    expected[MANIFEST_FILENAME] = manifest_bytes
    for concept in state.knowledge.concepts:
        raw = session.read(concept.document.canonical_path, MAX_EXPANDED_BYTES)
        if digest(raw) != concept.facets.semantics.page_hash:
            raise KnowledgeStorageError(concept.document.canonical_path, "authored input changed", code="storage-mutation")
    marker = state.manifest_basis.artifact_hashes
    if marker is not None and marker.governance_hash is not None:
        if digest(session.read(GOVERNANCE_FILENAME, MAX_OBJECT_BYTES)) != marker.governance_hash:
            raise KnowledgeStorageError("governance", "ledger changed after validation", code="storage-mutation")
    return state, session, expected


def _default_recovery_directory(root: Path, root_hash: str) -> Path | None:
    try:
        result = subprocess.run(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"],
                                capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()) / "llm-wiki-storage-recovery" / root_hash[7:]


def _outside_tree(directory: Path, root: Path) -> Path:
    directory = _absolute_path(directory)
    root = _absolute_path(root)
    if directory == root or root in directory.parents or directory in root.parents:
        raise KnowledgeStorageError("recovery_dir", "must be outside the managed wiki and not one of its ancestors")
    return directory


def _backup(directory: Path, files: dict[str, bytes], target_hash: str, target_manifest_hash: str) -> None:
    record = {"schema_version": RECOVERY_SCHEMA, "original_root_hash": digest(files[ROOT_FILENAME]),
              "target_root_hash": target_hash,
              "original_manifest_hash": digest(files[MANIFEST_FILENAME]),
              "target_manifest_hash": target_manifest_hash,
              "files": {name: {"hash": digest(raw), "bytes": len(raw)} for name, raw in sorted(files.items())}}
    metadata = canonical_bytes(record)
    if len(metadata) > MAX_OBJECT_BYTES:
        raise KnowledgeStorageError("recovery", "recovery catalog exceeds its byte bound", code="storage-limit")
    if directory.exists() and any(directory.iterdir()):
        if not (directory / "recovery.json").exists():
            raise KnowledgeStorageError("recovery_dir", "must be empty or contain this exact recovery snapshot")
        if read_guarded(directory / "recovery.json", MAX_OBJECT_BYTES).content != metadata:
            raise KnowledgeStorageError("recovery_dir", "contains a different recovery snapshot")
    ensure_guarded_directory(directory, mode=0o700)
    for name, content in {**files, "recovery.json": metadata}.items():
        path = directory / name
        ensure_guarded_directory(path.parent, mode=0o700)
        existing = read_guarded(path, MAX_EXPANDED_BYTES).content if path.exists() or path.is_symlink() else None
        if existing is not None and existing != content:
            raise KnowledgeStorageError("recovery_dir", "existing recovery bytes differ")
        if existing is None:
            atomic_write_guarded_bytes(path, content, expected_existing=None)


def migrate_knowledge_storage(wiki_dir: str | Path, *, dry_run: bool = False,
                              recovery_dir: str | Path | None = None,
                              to: str = "sharded-v2") -> dict[str, Any]:
    """Explicitly adopt indexed storage, retaining verified recovery bytes outside the wiki."""
    if type(dry_run) is not bool:
        raise KnowledgeStorageError("dry_run", "must be boolean")
    if to not in {"sharded-v2", *PACKED_FORMATS, "indexed-v6"}:
        raise KnowledgeStorageError("to", "unsupported migration format")
    root = _absolute_path(Path(wiki_dir))
    state, session, previous = _committed_inputs(root)
    assert state.knowledge is not None and state.manifest_basis is not None
    plan = build_knowledge_commit_plan(root, surface_index_bytes=previous[SURFACE_INDEX_FILENAME],
        knowledge_index=state.knowledge, manifest=state.manifest_basis.without_artifact_hashes(),
        knowledge_format=None if to == "indexed-v6" else to,
        manifest_format="indexed-v6" if to == "indexed-v6" else None,
        prior=state.validated_artifacts)
    # The complete v1 logical model was validated before encoding; the plan's
    # v2 full reader independently reconstructed/validated it before publication.
    recovery = (Path(recovery_dir) if recovery_dir is not None
                else _default_recovery_directory(root, digest(previous[ROOT_FILENAME] + previous[MANIFEST_FILENAME])))
    if recovery is not None:
        recovery = _outside_tree(recovery, root)
    report = {"schema_version": "llm-wiki-storage-migration/v1", "dry_run": dry_run,
              "changed": plan.changed, "from": current_knowledge_format(root), "to": to,
              "previous_root_hash": digest(previous[ROOT_FILENAME]),
              "root_hash": plan.knowledge_index.content_hash,
              "root_bytes": len(plan.knowledge_index.content),
              "object_count": len(plan.storage_objects),
              "object_bytes": sum(len(a.content) for a in plan.storage_objects),
              "recovery_dir": None if recovery is None else str(recovery),
              "requires_recovery_dir": plan.changed and recovery is None,
              "minimum_reader": ("manifest/v6" if to == "indexed-v6" else LOCAL_PACKED_SCHEMA if to.startswith("packed-v4")
                                 else PACKED_SCHEMA if to in PACKED_FORMATS else "llm-wiki-knowledge/v2"),
              "authority_preserved": ["Markdown", "governance ledger", "review history"],
              "git_history_changed": False}
    if dry_run:
        session.recheck()
        return report
    if plan.changed:
        if recovery is None:
            raise KnowledgeStorageError("recovery_dir", "supply --recovery-dir outside the wiki for a non-Git project")
        _backup(recovery, previous, plan.knowledge_index.content_hash, plan.manifest.content_hash)
        session.recheck()
        commit_knowledge_artifacts(plan)
        # Authority is never replaced; recheck it even after generated commits.
        for name in tuple(session.observations):
            if name in previous:
                continue
            session.read(name, len(session.observations[name].content))
    return report


def _read_recovery(directory: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    from .knowledge_storage import decode_bytes
    metadata = decode_bytes(read_guarded(directory / "recovery.json", MAX_OBJECT_BYTES).content,
                            limit=MAX_OBJECT_BYTES, field="recovery")
    fields = {"schema_version", "original_root_hash", "target_root_hash", "files"}
    if metadata.get("schema_version") == RECOVERY_SCHEMA:
        fields |= {"original_manifest_hash", "target_manifest_hash"}
    if (set(metadata) != fields
            or metadata["schema_version"] not in (RECOVERY_SCHEMA, "llm-wiki-knowledge-recovery/v1")
            or not isinstance(metadata["files"], dict)):
        raise KnowledgeStorageError("recovery", "unsupported recovery record")
    _hash(metadata["original_root_hash"], "recovery.original_root_hash")
    _hash(metadata["target_root_hash"], "recovery.target_root_hash")
    if metadata["schema_version"] == RECOVERY_SCHEMA:
        _hash(metadata["original_manifest_hash"], "recovery.original_manifest_hash")
        _hash(metadata["target_manifest_hash"], "recovery.target_manifest_hash")
    if len(metadata["files"]) > 100_003:
        raise KnowledgeStorageError("recovery", "too many files", code="storage-limit")
    files = {}
    total = 0
    for name, info in metadata["files"].items():
        if name not in {ROOT_FILENAME, SURFACE_INDEX_FILENAME, MANIFEST_FILENAME} and not is_storage_path(name):
            raise KnowledgeStorageError("recovery", "contains a non-artifact path")
        if (not isinstance(info, dict) or set(info) != {"hash", "bytes"}
                or type(info["bytes"]) is not int or not 0 < info["bytes"] <= MAX_EXPANDED_BYTES):
            raise KnowledgeStorageError("recovery", "invalid file descriptor")
        total += info["bytes"]
        if total > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("recovery", "snapshot exceeds its aggregate byte bound", code="storage-limit")
        raw = read_guarded(directory / name, info["bytes"]).content
        if len(raw) != info["bytes"] or digest(raw) != info["hash"]:
            raise KnowledgeStorageError("recovery", "file commitment mismatch")
        files[name] = raw
    if not {ROOT_FILENAME, SURFACE_INDEX_FILENAME, MANIFEST_FILENAME} <= set(files):
        raise KnowledgeStorageError("recovery", "missing original artifacts")
    if digest(files[ROOT_FILENAME]) != metadata["original_root_hash"]:
        raise KnowledgeStorageError("recovery", "original root commitment mismatch")
    if metadata["schema_version"] == RECOVERY_SCHEMA and digest(files[MANIFEST_FILENAME]) != metadata["original_manifest_hash"]:
        raise KnowledgeStorageError("recovery", "original manifest commitment mismatch")
    return metadata, files


def recover_knowledge_storage(wiki_dir: str | Path, recovery_dir: str | Path, *,
                              dry_run: bool = False) -> dict[str, Any]:
    """Restore an exact interrupted migration; refuse unrelated newer roots."""
    if type(dry_run) is not bool:
        raise KnowledgeStorageError("dry_run", "must be boolean")
    root = _absolute_path(Path(wiki_dir))
    directory = _outside_tree(Path(recovery_dir), root)
    metadata, files = _read_recovery(directory)
    manifest = SyncManifest.from_payload(json.loads(files[MANIFEST_FILENAME]), object_reader=lambda path, _: files[path])
    validated = validate_knowledge_artifacts(surface_index_bytes=files[SURFACE_INDEX_FILENAME],
        knowledge_index_bytes=files[ROOT_FILENAME], manifest=manifest,
        object_reader=lambda path, _: files[path])
    marker = manifest.artifact_hashes
    if (marker is None or marker.knowledge_index_hash != validated.knowledge_index_hash
            or marker.surface_index_hash != validated.surface_index_hash
            or marker.evaluated_envelope_hash != validated.evaluated_envelope_hash
            or marker.governance_hash != validated.governance_hash):
        raise KnowledgeStorageError("recovery", "manifest does not commit the recovered root")
    session = StorageReadSession(root)
    existing_root = session.read(ROOT_FILENAME, MAX_EXPANDED_BYTES)
    if digest(existing_root) not in {metadata["original_root_hash"], metadata["target_root_hash"]}:
        raise KnowledgeStorageError("recovery", "current root is outside this migration; refusing to overwrite it")
    if metadata["schema_version"] == RECOVERY_SCHEMA:
        existing_manifest = session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)
        if digest(existing_manifest) not in {metadata["original_manifest_hash"], metadata["target_manifest_hash"]}:
            raise KnowledgeStorageError("recovery", "current manifest is outside this migration; refusing to overwrite it")
    for concept in validated.knowledge.concepts:
        if digest(session.read(concept.document.canonical_path, MAX_EXPANDED_BYTES)) != concept.facets.semantics.page_hash:
            raise KnowledgeStorageError("recovery", "current Markdown differs from the original generation")
    if marker.governance_hash is not None:
        if digest(session.read(GOVERNANCE_FILENAME, MAX_OBJECT_BYTES)) != marker.governance_hash:
            raise KnowledgeStorageError("recovery", "current governance differs from the original generation")
    writes = {}
    for name, content in files.items():
        path = root / name
        old = session.read(name, MAX_EXPANDED_BYTES) if path.exists() or path.is_symlink() else None
        writes[name] = PlannedArtifactWrite(path=path, relative_path=name,
            state=ArtifactWriteState.UNCHANGED if old == content else ArtifactWriteState.UPDATED,
            content_hash=digest(content), content=content, needs_write=old != content, previous_content=old)
    original_format = "sharded-v2" if json.loads(files[ROOT_FILENAME]).get("schema_version") == "llm-wiki-knowledge/v2" else "v1"
    original_root = json.loads(files[ROOT_FILENAME])
    if original_root.get("schema_version") in PACKED_SCHEMAS:
        original_format = packed_format(original_root)
    plan = KnowledgeCommitPlan(surface_index=writes[SURFACE_INDEX_FILENAME], knowledge_index=writes[ROOT_FILENAME],
        manifest=writes[MANIFEST_FILENAME], committed_manifest=manifest,
        evaluated_envelope_hash=validated.evaluated_envelope_hash,
        storage_objects=tuple(w for name, w in writes.items() if is_storage_path(name)),
        storage_format=original_format)
    session.recheck()
    if not dry_run:
        # Recovery restores already validated historical bytes, including an old
        # oversized v1 blob. It does not waive size checks for a subsequent push.
        _commit_sharded(plan, None)
    return {"schema_version": "llm-wiki-storage-recovery/v1", "dry_run": dry_run,
            "changed": plan.changed, "restored_format": original_format,
            "root_hash": validated.knowledge_index_hash, "git_history_changed": False}


def export_knowledge_v1(wiki_dir: str | Path, output: str | Path) -> dict[str, Any]:
    state, session, _ = _committed_inputs(wiki_dir)
    assert state.knowledge is not None
    raw = serialize_knowledge_index(state.knowledge).encode("utf-8")
    if len(raw) >= GIT_FAILURE_BYTES:
        raise KnowledgeStorageError("export", "complete v1 output exceeds the 95 MiB file policy", code="storage-limit")
    path = _absolute_path(Path(output))
    root = _absolute_path(Path(wiki_dir))
    if path == root or root in path.parents:
        raise KnowledgeStorageError("output", "export must be outside the managed wiki")
    if path.exists() or path.is_symlink():
        raise KnowledgeStorageError("output", "refusing to overwrite an existing export")
    session.recheck()
    ensure_guarded_directory(path.parent)
    atomic_write_guarded_bytes(path, raw, mode=0o644, expected_existing=None)
    return {"format": "v1", "bytes": len(raw), "hash": digest(raw), "output": str(path)}


def is_storage_path(relative: str) -> bool:
    return bool(_OBJECT_NAME.fullmatch(relative) or INDEX_NAME.fullmatch(relative) or PACK_NAME.fullmatch(relative) or INDEX_PAGE_NAME.fullmatch(relative)
                or MANIFEST_OBJECT_NAME.fullmatch(relative))


def stored_object_paths(wiki_dir: str | Path) -> tuple[list[str], list[str]]:
    """Bounded enumeration of the owned two-level object namespace, without links."""
    root = _absolute_path(Path(wiki_dir))
    owned, unknown = [], []
    entries = 0

    def bounded_entries(directory: Path) -> list[Path]:
        nonlocal entries
        paths = []
        with os.scandir(directory) as scan:
            for entry in scan:
                entries += 1
                if entries > 301_024:
                    raise KnowledgeStorageError("objects", "object discovery exceeds its entry limit", code="storage-limit")
                paths.append(Path(entry.path))
        return sorted(paths)

    for namespace in (OBJECT_DIRECTORY, PACK_INDEX_DIRECTORY, PACK_DIRECTORY, INDEX_PAGE_DIRECTORY, MANIFEST_DIRECTORY):
        objects = root / namespace
        if not objects.exists() and not objects.is_symlink():
            continue
        _absolute_path(objects)
        for directory in bounded_entries(objects):
            _absolute_path(directory)
            pattern = r"[0-9a-f]{2}"
            if not re.fullmatch(pattern, directory.name) or not directory.is_dir():
                unknown.append(directory.relative_to(root).as_posix())
                continue
            for path in bounded_entries(directory):
                _absolute_path(path)
                relative = path.relative_to(root).as_posix()
                (owned if path.is_file() and is_storage_path(relative) else unknown).append(relative)
    return owned, unknown


def _prune_plan(root, root_bytes, manifest_bytes, candidates):
    stamp = root.stat()
    body = {"schema_version": "llm-wiki-prune-plan/v1",
            "root_binding": digest(os.fsencode(str(root))), "root_identity": [stamp.st_dev, stamp.st_ino],
            "knowledge_hash": digest(root_bytes), "manifest_hash": digest(manifest_bytes),
            "candidates": []}
    for name in sorted(candidates):
        raw = candidates[name]
        body["candidates"].append({"path": name, "hash": digest(raw), "bytes": len(raw)})
    if len(body["candidates"]) > 100_000 or len(canonical_bytes(body)) > MAX_OBJECT_BYTES:
        raise KnowledgeStorageError("plan", "prune plan exceeds its bound", code="storage-limit")
    body["plan_id"] = digest(canonical_bytes(body))
    return body


def _prune_backup(root, directory, plan, candidates, cancelled):
    if directory is None:
        default = _default_recovery_directory(root, plan["knowledge_hash"])
        base = default.parent / "prune" if default is not None else root.parent / ".llm-wiki-storage-recovery"
        directory = base / plan["root_binding"][7:]
    directory = _outside_tree(Path(directory), root)
    ensure_guarded_directory(directory, mode=0o700)
    for row in plan["candidates"]:
        if cancelled is not None and cancelled():
            raise KnowledgeStorageError("prune", "cleanup cancelled", code="storage-cancelled")
        raw = candidates[row["path"]]
        target = directory / "objects" / row["hash"][7:9] / (row["hash"][7:] + ".bin")
        ensure_guarded_directory(target.parent, mode=0o700)
        if not target.exists():
            atomic_write_guarded_bytes(target, raw, mode=0o600, expected_existing=None)
        if read_guarded(target, len(raw)).content != raw:
            raise KnowledgeStorageError("recovery", "prune recovery preimage differs")
    target = directory / (plan["plan_id"][7:] + ".json")
    raw = canonical_bytes(plan)
    if not target.exists():
        atomic_write_guarded_bytes(target, raw, mode=0o600, expected_existing=None)
    if read_guarded(target, MAX_OBJECT_BYTES).content != raw:
        raise KnowledgeStorageError("recovery", "prune recovery plan differs")
    return str(target)


def prune_knowledge_storage(wiki_dir: str | Path, *, dry_run: bool = True, plan=None,
                            recovery_dir: str | Path | None = None, max_bytes: int = MAX_EXPANDED_BYTES,
                            cancelled=None) -> dict[str, Any]:
    """Preview or apply an exact generation-bound cleanup with verified recovery."""
    from .storage_spool import ByteSpool
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_EXPANDED_BYTES:
        raise KnowledgeStorageError("max_bytes", "invalid cleanup byte budget")
    if cancelled is not None and not callable(cancelled):
        raise KnowledgeStorageError("cancelled", "requires a trusted callback")
    with ByteSpool(max_bytes=max_bytes) as candidates:
        return _prune_storage(wiki_dir, dry_run=dry_run, plan=plan, recovery_dir=recovery_dir,
                              safe=candidates, cancelled=cancelled)


def _prune_storage(wiki_dir, *, dry_run, plan, recovery_dir, safe, cancelled):
    """Remove only valid content-addressed objects unreachable from a full audit."""
    if type(dry_run) is not bool:
        raise KnowledgeStorageError("dry_run", "must be boolean")
    root = _absolute_path(Path(wiki_dir))
    state, session, expected_inputs = _committed_inputs(root)
    assert state.validated_artifacts is not None and state.manifest_basis is not None
    if current_knowledge_format(root) not in {"sharded-v2", *PACKED_FORMATS} and state.manifest_basis.storage_version != 6:
        raise KnowledgeStorageError("format", "cleanup requires a committed indexed root")
    if plan is None:
        owned, unknown = stored_object_paths(root)
    else:
        if (not isinstance(plan, dict) or plan.get("schema_version") != "llm-wiki-prune-plan/v1"
                or not isinstance(plan.get("candidates"), list) or len(plan["candidates"]) > 100_000
                or len(canonical_bytes(plan)) > MAX_OBJECT_BYTES
                or plan.get("plan_id") != digest(canonical_bytes({k: v for k, v in plan.items() if k != "plan_id"}))):
            raise KnowledgeStorageError("plan", "invalid bounded cleanup plan")
        owned = []
        for row in plan["candidates"]:
            if (not isinstance(row, dict) or set(row) != {"path", "hash", "bytes"}
                    or not isinstance(row["path"], str) or not is_storage_path(row["path"])):
                raise KnowledgeStorageError("plan", "invalid cleanup candidate")
            owned.append(row["path"])
        if len(owned) != len(set(owned)):
            raise KnowledgeStorageError("plan", "duplicate cleanup candidates")
        unknown = []
    unused = sorted(set(owned) - set(state.validated_artifacts.storage_objects))
    retained = list(unknown)
    _, root_bytes = validated_artifact_bytes(state.validated_artifacts)
    def object_reader(relative: str, maximum: int) -> bytes:
        return read_guarded(root / relative, maximum).content
    parsed = json.loads(root_bytes)
    logical_root = parsed["store"] if parsed.get("schema_version") in PACKED_SCHEMAS else parsed
    inspector = KnowledgeStoreReader(canonical_bytes(logical_root), object_reader) if current_knowledge_format(root) != "v1" else None
    inspected_bytes = 0
    budget_exhausted = False
    for index, name in enumerate(unused):
        if cancelled is not None and cancelled():
            raise KnowledgeStorageError("prune", "cleanup cancelled", code="storage-cancelled")
        try:
            remaining = safe.maximum - inspected_bytes
            if remaining <= 0 or _absolute_path(root / name).stat().st_size > remaining:
                retained.extend(unused[index:])
                budget_exhausted = True
                break
            raw = read_guarded(root / name, min(MAX_OBJECT_BYTES, remaining)).content
            inspected_bytes += len(raw)
            if PACK_NAME.fullmatch(name):
                inspect_pack(raw, name)
                safe[name] = raw
                continue
            if INDEX_PAGE_NAME.fullmatch(name):
                inspect_index_pages(raw, name)
                safe[name] = raw
                continue
            if digest(raw)[7:] != Path(name).stem:
                raise KnowledgeStorageError(name, "unknown content identity")
            if MANIFEST_OBJECT_NAME.fullmatch(name):
                validate_catalog(raw)
                safe[name] = raw
                continue
            payload = decode_bytes(raw, limit=MAX_OBJECT_BYTES, field=name)
            if INDEX_NAME.fullmatch(name):
                kind = payload.get("kind")
                count = (len(payload[kind]) if kind in {"members", "packs"}
                         else sum(child["count"] for child in payload["children"].values()))
                desc = {"hash": digest(raw), "bytes": len(raw), "count": count}
                probe_root = canonical_bytes({"schema_version": PACKED_SCHEMA, "store": logical_root,
                    "packing": {"compression": "stored", "catalog": desc, "pack_catalog": desc, "objects": count, "packs": count}})
                PackedKnowledgeStoreReader(probe_root, object_reader)._index(desc, payload["prefix"], "packs" if kind == "packs" else "members")
                safe[name] = raw
                continue
            count = (len(payload["records"]) if payload.get("kind") == "records"
                     else sum(child["count"] for child in payload["children"].values()))
            if inspector is None:
                retained.append(name)
                continue
            inspector._node({"hash": digest(raw), "bytes": len(raw), "count": count},
                            payload["collection"], payload["prefix"])
        except (KnowledgeStorageError, OSError, KeyError, TypeError):
            retained.append(name)
            continue
        safe[name] = raw
    session.recheck()
    prepared = _prune_plan(root, root_bytes, expected_inputs[MANIFEST_FILENAME], safe)
    if plan is not None and canonical_bytes(plan) != canonical_bytes(prepared):
        raise KnowledgeStorageError("plan", "generation, root or candidate preimages changed", code="storage-mutation")
    removed = []
    recovery = None
    if not dry_run:
        with governance_lock(root, _lock_filename="llm-wiki-storage.lock"):
            session.recheck()
            if safe:
                recovery = _prune_backup(root, recovery_dir, prepared, safe, cancelled)
            for name, content in safe.items():
                if cancelled is not None and cancelled():
                    retained.extend(name for name in safe if name not in removed)
                    break
                # Recheck current authority before each deletion, without
                # rematerializing the model or trusting the preview as a lease.
                session.read(ROOT_FILENAME, len(root_bytes))
                session.read(MANIFEST_FILENAME, len(expected_inputs[MANIFEST_FILENAME]))
                try:
                    unlink_guarded_bytes(root / name, expected=content)
                    removed.append(name)
                except OSError:
                    retained.append(name)
    return {"dry_run": dry_run, "unreferenced_objects": sorted(safe), "removed": removed,
            "retained": sorted(set(retained)), "bytes": sum(map(len, safe.values())), "git_history_changed": False,
            "plan": prepared, "recovery_manifest": recovery, "inspection_bytes": inspected_bytes,
            "budget_exhausted": budget_exhausted,
            "scan_scope": "owned-namespace" if plan is None else "saved-plan-candidates"}


def restore_pruned_storage(wiki_dir: str | Path, recovery_manifest: str | Path, *, dry_run: bool = True,
                           cancelled=None) -> dict[str, Any]:
    """Restore cleanup preimages into their recorded generation without overwrites."""
    from .storage_spool import ByteSpool
    root = _absolute_path(Path(wiki_dir))
    record_path = _absolute_path(Path(recovery_manifest))
    stamp = root.stat()
    plan = decode_bytes(read_guarded(record_path, MAX_OBJECT_BYTES).content, limit=MAX_OBJECT_BYTES, field="prune plan")
    if (set(plan) != {"schema_version", "root_binding", "root_identity", "knowledge_hash", "manifest_hash", "candidates", "plan_id"}
            or plan["schema_version"] != "llm-wiki-prune-plan/v1"
            or plan["plan_id"] != digest(canonical_bytes({k: v for k, v in plan.items() if k != "plan_id"}))
            or plan["root_binding"] != digest(os.fsencode(str(root)))
            or plan["root_identity"] != [stamp.st_dev, stamp.st_ino]
            or not isinstance(plan["candidates"], list) or len(plan["candidates"]) > 100_000
            or type(dry_run) is not bool or (cancelled is not None and not callable(cancelled))):
        raise KnowledgeStorageError("recovery", "invalid cleanup recovery binding")
    _hash(plan["knowledge_hash"], "recovery.knowledge_hash")
    _hash(plan["manifest_hash"], "recovery.manifest_hash")
    generation = StorageReadSession(root, cancelled=cancelled)

    def check_generation():
        current = _absolute_path(root).stat()
        if [current.st_dev, current.st_ino] != plan["root_identity"]:
            raise KnowledgeStorageError("recovery", "wiki root changed after cleanup", code="storage-mutation")
        # Recovery may be needed because objects are missing. Bind to the two
        # commit headers without requiring the current store to pass a full audit.
        with generation.phase():
            for name, commitment in ((ROOT_FILENAME, plan["knowledge_hash"]),
                                     (MANIFEST_FILENAME, plan["manifest_hash"])):
                if digest(generation.read(name, MAX_EXPANDED_BYTES)) != commitment:
                    raise KnowledgeStorageError("recovery", "current generation differs from cleanup recovery",
                                                code="storage-mutation")

    check_generation()
    restored, retained = [], []
    with ByteSpool(max_bytes=MAX_EXPANDED_BYTES) as preimages:
        for row in plan["candidates"]:
            if (not isinstance(row, dict) or set(row) != {"path", "hash", "bytes"}
                    or not isinstance(row["path"], str) or not is_storage_path(row["path"])
                    or row["path"] in preimages or type(row["bytes"]) is not int or not 0 <= row["bytes"] <= MAX_OBJECT_BYTES):
                raise KnowledgeStorageError("recovery", "invalid cleanup preimage")
            _hash(row["hash"], "preimage.hash")
            pack = PACK_NAME.fullmatch(row["path"])
            if (pack[2] if pack is not None else Path(row["path"]).stem) != row["hash"][7:]:
                raise KnowledgeStorageError("recovery", "preimage hash differs from its content-addressed path")
            if cancelled is not None and cancelled():
                raise KnowledgeStorageError("recovery", "restore cancelled", code="storage-cancelled")
            raw = read_guarded(record_path.parent / "objects" / row["hash"][7:9] / (row["hash"][7:] + ".bin"), row["bytes"]).content
            if len(raw) != row["bytes"] or digest(raw) != row["hash"]:
                raise KnowledgeStorageError("recovery", "cleanup preimage changed")
            preimages[row["path"]] = raw
        check_generation()
        if not dry_run:
            with governance_lock(root, _lock_filename="llm-wiki-storage.lock"):
                check_generation()
                for name, raw in preimages.items():
                    if cancelled is not None and cancelled():
                        retained.extend(key for key in preimages if key not in restored)
                        break
                    target = _absolute_path(root / name)
                    if target.exists():
                        if read_guarded(target, MAX_OBJECT_BYTES).content != raw:
                            retained.append(name)
                        continue
                    ensure_guarded_directory(target.parent, mode=0o755)
                    check_generation()
                    atomic_write_guarded_bytes(target, raw, mode=0o644, expected_existing=None)
                    restored.append(name)
        return {"dry_run": dry_run, "plan_id": plan["plan_id"], "restored": restored,
                "retained": sorted(set(retained)), "preimages": len(preimages), "authority_changed": False}
