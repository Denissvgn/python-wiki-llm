"""Local maintenance adoption and captured authority operations."""

from __future__ import annotations

from contextlib import contextmanager
import json
from dataclasses import replace

from .knowledge_artifacts import build_knowledge_commit_plan, commit_knowledge_artifacts, validated_artifact_bytes
from .knowledge_storage import canonical_bytes, digest, MAX_EXPANDED_BYTES
from .knowledge_storage_io import read_guarded, _absolute_path
from .filesystem_guard import ensure_guarded_directory, atomic_write_guarded_bytes, unlink_guarded_bytes
from .maintenance_protocol import (
    ADOPTION_FILENAME, MaintenanceProtocolError, WikiWriteBasis,
    governance_writer_lock, storage_writer_lock, guard_maintenance_owner,
    load_adoption_marker, snapshot_wiki, save_recovery_snapshot,
)
from .wiki_write_basis import ACTIVE_WRITE_BASIS


def _capture(src_dir, wiki_dir, **options):
    from .context_packet import capture_context_read

    captured = capture_context_read(src_dir, str(wiki_dir), read_only=True,
        capture_implementation_observations=True, **options)
    if not captured.knowledge_view.ready or captured.knowledge_view.knowledge is None:
        raise MaintenanceProtocolError("knowledge-unavailable", "Maintenance requires a coherent native snapshot; recover adopted authority before ordinary repair")
    return captured


def capture_maintenance_observations(captured, state=None, *, raw_pages=None):
    from .maintenance_evidence import captured_observations_from_knowledge
    from .python_implementation import analysis_identity
    from .source_snapshot import confirmed_missing_source_paths

    old = state["observations"].values() if state is not None else ()
    paths = {row["coordinate"]["source_path"] for row in old}
    missing = confirmed_missing_source_paths(captured.source_snapshot, paths)
    hashes = captured.source_snapshot.captured_content_hashes
    old_targets = {row["target"]["canonical_path"] for row in (state["observations"].values() if state is not None else ())}
    absent = {p for p in old_targets if not (captured.wiki_root / p).exists() and not (captured.wiki_root / p).is_symlink()}
    return captured_observations_from_knowledge(
        captured.knowledge_view.knowledge,
        content_by_page=captured.surface_evaluation.content_by_path,
        raw_content_by_page=raw_pages,
        page_source_mappings=captured.knowledge_view.manifest_basis.page_source_mappings,
        captures=captured.inventory_result.implementation_observations,
        source_content_hashes=hashes, captured_paths=set(hashes) | set(missing),
        missing_source_paths=missing,
        analysis_compatibility_hash=analysis_identity(captured.inventory_result.analysis_components),
        previous_state=state, known_absent_pages=absent,
    )


@contextmanager
def _capture_basis(root, files):
    basis = WikiWriteBasis(root, dict(files))
    token = ACTIVE_WRITE_BASIS.set(basis)
    try:
        yield basis
        basis.assert_current()
    finally:
        ACTIVE_WRITE_BASIS.reset(token)


def _outside_recovery(directory, root, source):
    path = _absolute_path(directory)
    if path == root or path.is_relative_to(root) or root.is_relative_to(path):
        raise MaintenanceProtocolError("recovery-path", "Recovery directory must be outside the wiki and its ancestors")
    if path == source or path.is_relative_to(source):
        raise MaintenanceProtocolError("recovery-path", "Recovery directory must not become a source input")
    return path


def adopt_maintenance_authority(src_dir, wiki_dir, *, recovery_dir, manifest_format=None,
                                fault_injector=None, **capture_options):
    """Explicitly adopt durable unreviewed authority without editing Markdown."""
    from .maintenance_state import new_identity
    from .maintenance_evidence import reconcile_pending_maintenance
    from .maintenance_projection import project_maintenance_knowledge
    from .source_snapshot import source_snapshot_matches_current_files

    root = _absolute_path(wiki_dir)
    source = _absolute_path(src_dir)
    recovery = _outside_recovery(recovery_dir, root, source)
    with governance_writer_lock(root), storage_writer_lock(root):
        existing = load_adoption_marker(root)
        if existing is not None:
            guard_maintenance_owner(root)
            return {"adoption_id": existing["adoption_id"], "changed": False, "already_adopted": True}
        guard_maintenance_owner(root)
        files = snapshot_wiki(root)
        with _capture_basis(root, files) as basis:
            captured = _capture(str(source), root, **capture_options)
            basis.source_snapshot = captured.source_snapshot
            marker = {"schema_version": "llm-wiki-maintenance-adoption/v1", "adoption_id": new_identity(),
                      "min_manifest_version": 7, "features": {"implementation_evidence": 1, "maintenance_state": 1, "ordinary_acknowledgment": 1}}
            observations = capture_maintenance_observations(captured, raw_pages=files)
            state = reconcile_pending_maintenance(None, marker, observations)
            view = captured.knowledge_view
            assert view.manifest_basis is not None and view.knowledge is not None
            manifest = view.manifest_basis.with_maintenance_state(state)
            knowledge = project_maintenance_knowledge(view.knowledge, state, marker)
            from .knowledge_reuse import REUSE_INPUT_KEY, REUSE_EXTENSION_KEY

            generation_inputs = dict(manifest.generation_inputs)
            generation_inputs.pop(REUSE_INPUT_KEY, None)
            manifest = manifest.with_generation_state(surfaces=manifest.surfaces, generation_inputs=generation_inputs)
            extensions = dict(knowledge.extensions)
            extensions.pop(REUSE_EXTENSION_KEY, None)
            knowledge = replace(knowledge, extensions=extensions)
            surface, _ = validated_artifact_bytes(view.validated_artifacts)
            plan = build_knowledge_commit_plan(root, surface_index_bytes=surface,
                knowledge_index=knowledge, manifest=manifest, prior=view.validated_artifacts,
                manifest_format=manifest_format, maintenance_adoption=marker)
            save_recovery_snapshot(recovery / "before", files, marker=marker, kind="legacy-preimage")
            after = dict(files)
            for artifact in (*plan.storage_objects, plan.surface_index, plan.knowledge_index, plan.manifest, plan.maintenance_adoption):
                if artifact is not None:
                    after[artifact.relative_path] = artifact.content
            save_recovery_snapshot(recovery / "prepared", after, marker=marker, kind="prepared-adoption")
            snapshot = captured.source_snapshot
            intent = {"schema_version": "llm-wiki-maintenance-adoption-intent/v1", "adoption_id": marker["adoption_id"],
                      "source_capture": {"only_files": sorted(snapshot.only_files) if snapshot.only_files is not None else None,
                                         "include_tests": sorted(snapshot.include_tests), "respect_ignores": snapshot.respect_ignores,
                                         "source_selection": snapshot.source_selection_path,
                                         "max_files": snapshot.capture_scan_limit, "max_bytes": snapshot.capture_byte_limit},
                      "source_inputs": [{"path": i.path, "content_hash": i.content_hash, "kind": i.kind_value}
                                        for i in captured.source_snapshot.to_consumed_inputs()]}
            ensure_guarded_directory(recovery)
            atomic_write_guarded_bytes(recovery / "adoption-intent.json", canonical_bytes(intent), expected_existing=None)
            basis.assert_current()
            if not source_snapshot_matches_current_files(captured.source_snapshot):
                raise MaintenanceProtocolError("source-changed", "Source changed before adoption")
            result = commit_knowledge_artifacts(plan, fault_injector=fault_injector)
            return {"adoption_id": marker["adoption_id"], "changed": result.changed,
                    "records": len(state["records"]), "state_hash": digest(canonical_bytes(state)),
                    "coverage": {"source_backed_semantic_total": observations.source_backed_semantic_total,
                                 "tracked_semantic_total": observations.tracked_semantic_total,
                                 "issues": observations.to_payload()["issues"]}, "recovery_dir": str(recovery)}


def load_recovery_snapshot(directory, *, allow_captured_preimage=False):
    try:
        return _load_recovery_snapshot(directory, allow_captured_preimage=allow_captured_preimage)
    except MaintenanceProtocolError:
        raise
    except (ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
        raise MaintenanceProtocolError("recovery-invalid", f"Complete recovery snapshot is invalid: {exc}") from exc


def _load_recovery_snapshot(directory, *, allow_captured_preimage=False):
    from .request_json import _pairs, _constant
    from .validation import is_portable_relative_path
    from .sync_manifest import SyncManifest, MANIFEST_FILENAME
    from .knowledge_artifacts import validate_knowledge_artifacts

    root = _absolute_path(directory)
    raw = read_guarded(root / "maintenance-recovery.json", 8_388_608).content
    metadata = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    if not isinstance(metadata, dict) or set(metadata) != {"schema_version", "marker", "files", "kind"} or metadata["schema_version"] != "llm-wiki-maintenance-recovery/v1" or metadata["kind"] not in {"committed", "captured-preimage", "prepared-adoption"}:
        raise MaintenanceProtocolError("recovery-invalid", "Unsupported complete maintenance recovery snapshot")
    if metadata["kind"] == "captured-preimage" and not allow_captured_preimage:
        raise MaintenanceProtocolError("recovery-intent", "Captured input preimages require explicit restoration and subsequent sync")
    if not isinstance(metadata["files"], dict) or len(metadata["files"]) > 100_000:
        raise MaintenanceProtocolError("recovery-invalid", "Invalid recovery file inventory")
    files = {}
    for name, info in metadata["files"].items():
        if not is_portable_relative_path(name) or not isinstance(info, dict) or set(info) != {"hash", "bytes"} or type(info["bytes"]) is not int or not 0 <= info["bytes"] <= MAX_EXPANDED_BYTES:
            raise MaintenanceProtocolError("recovery-invalid", "Invalid recovery file manifest")
        content = read_guarded(root / name, max(1, info["bytes"])).content
        if len(content) != info["bytes"] or digest(content) != info["hash"]:
            raise MaintenanceProtocolError("recovery-invalid", "Recovery bytes differ from their commitments")
        files[name] = content
    if ADOPTION_FILENAME not in files:
        raise MaintenanceProtocolError("recovery-invalid", "A committed maintenance recovery requires its immutable marker")
    from .maintenance_state import validate_maintenance_adoption

    marker = validate_maintenance_adoption(json.loads(files[ADOPTION_FILENAME], object_pairs_hook=_pairs, parse_constant=_constant))
    if files[ADOPTION_FILENAME] != canonical_bytes(marker):
        raise MaintenanceProtocolError("recovery-invalid", "Recovery marker is not canonical")
    if marker != metadata["marker"]:
        raise MaintenanceProtocolError("recovery-invalid", "Recovery marker commitment disagrees")
    manifest = SyncManifest.from_payload(json.loads(files[MANIFEST_FILENAME], object_pairs_hook=_pairs, parse_constant=_constant), object_reader=lambda name, maximum: files[name])
    validated = validate_knowledge_artifacts(surface_index_bytes=files[".llm-wiki-surface.json"],
        knowledge_index_bytes=files[".llm-wiki-knowledge.json"], manifest=manifest,
        object_reader=lambda name, maximum: files[name])
    from .maintenance_projection import validate_maintenance_projection

    validate_maintenance_projection(validated.knowledge, state=manifest.maintenance_state, marker=marker,
        raw_content_by_page=None if metadata["kind"] == "captured-preimage" else files)
    if manifest.artifact_hashes is None or manifest.artifact_hashes.maintenance_adoption_hash != digest(files[ADOPTION_FILENAME]):
        raise MaintenanceProtocolError("recovery-invalid", "Recovery manifest does not commit its adoption marker")
    from .knowledge_governance import GOVERNANCE_FILENAME
    if manifest.artifact_hashes.governance_hash is None and GOVERNANCE_FILENAME in files:
        raise MaintenanceProtocolError("recovery-invalid", "Recovery contains uncommitted governance authority")
    if manifest.artifact_hashes.governance_hash is not None:
        from .knowledge_governance import GOVERNANCE_FILENAME, parse_governance_ledger, validate_governance_projection

        governance_bytes = files[GOVERNANCE_FILENAME]
        if digest(governance_bytes) != manifest.artifact_hashes.governance_hash:
            raise MaintenanceProtocolError("recovery-invalid", "Recovery governance bytes disagree")
        validate_governance_projection(validated.knowledge, ledger=parse_governance_ledger(json.loads(governance_bytes, object_pairs_hook=_pairs, parse_constant=_constant)))
    from .io import decode_markdown_bytes

    for concept in validated.knowledge.concepts:
        if metadata["kind"] != "captured-preimage" and digest(decode_markdown_bytes(files[concept.document.canonical_path]).encode("utf-8")) != concept.facets.semantics.page_hash:
            raise MaintenanceProtocolError("recovery-invalid", "Recovery authored page differs from committed snapshot")
    return metadata, files, manifest


def recover_maintenance_authority(wiki_dir, *, recovery_dir, expected_adoption_id,
                                  allow_prepared_adoption=False, allow_captured_preimage=False, src_dir=None):
    """Restore one validated complete snapshot; never reconstruct review history."""
    from .source_snapshot import build_source_snapshot
    from .knowledge_envelope import hash_source_snapshot, ConsumedInput
    from .sync_manifest import MANIFEST_FILENAME, SyncManifest
    from .request_json import _pairs, _constant

    root = _absolute_path(wiki_dir)
    directory = _absolute_path(recovery_dir)
    metadata, files, manifest = load_recovery_snapshot(directory, allow_captured_preimage=allow_captured_preimage)
    if metadata["kind"] == "prepared-adoption" and not allow_prepared_adoption:
        raise MaintenanceProtocolError("recovery-intent", "Prepared adoption requires explicit retry and source-basis verification")
    marker = metadata["marker"]
    if marker["adoption_id"] != expected_adoption_id:
        raise MaintenanceProtocolError("recovery-mismatch", "Recovery snapshot belongs to another adoption identity")
    with governance_writer_lock(root), storage_writer_lock(root):
        present = load_adoption_marker(root)
        if present is not None and present != marker:
            raise MaintenanceProtocolError("recovery-mismatch", "Recovery cannot replace another adoption marker")
        try:
            current_manifest = SyncManifest.load(root)
        except (ValueError, OSError, TypeError):
            current_manifest = None
        if current_manifest is not None and current_manifest.maintenance_state is not None:
            from .maintenance_state import maintenance_state_hash

            if maintenance_state_hash(current_manifest.maintenance_state) != maintenance_state_hash(manifest.maintenance_state):
                raise MaintenanceProtocolError("recovery-newer-owner", "Recovery cannot replace another committed maintenance state")
        if metadata["kind"] == "prepared-adoption":
            if src_dir is None:
                raise MaintenanceProtocolError("recovery-source", "Adoption retry requires the original current source basis")
            intent = json.loads(read_guarded(directory.parent / "adoption-intent.json", 8_388_608).content, object_pairs_hook=_pairs, parse_constant=_constant)
            if not isinstance(intent, dict) or set(intent) != {"schema_version", "adoption_id", "source_inputs", "source_capture"} or intent["schema_version"] != "llm-wiki-maintenance-adoption-intent/v1" or intent.get("adoption_id") != expected_adoption_id:
                raise MaintenanceProtocolError("recovery-mismatch", "Adoption retry intent is from another identity")
            options = intent["source_capture"]
            if not isinstance(options, dict) or set(options) != {"only_files", "include_tests", "respect_ignores", "source_selection", "max_files", "max_bytes"}:
                raise MaintenanceProtocolError("recovery-invalid", "Adoption retry capture policy is invalid")
            current = build_source_snapshot(_absolute_path(src_dir), coherent=True, **options)
            expected = [ConsumedInput(**row) for row in intent["source_inputs"]]
            if hash_source_snapshot(current.to_consumed_inputs()) != hash_source_snapshot(expected):
                raise MaintenanceProtocolError("source-changed", "Prepared adoption cannot replace a changed source basis")
        current_files = snapshot_wiki(root)
        eligible: dict[str, list[str | None]] = {name: [digest(raw)] for name, raw in files.items()}
        if metadata["kind"] == "prepared-adoption":
            before = json.loads(read_guarded(directory.parent / "before" / "maintenance-recovery.json", 8_388_608).content,
                                object_pairs_hook=_pairs, parse_constant=_constant)
            if before.get("marker") != marker or before.get("kind") != "legacy-preimage":
                raise MaintenanceProtocolError("recovery-invalid", "Prepared transaction preimage differs")
            for name in set(files) | set(before["files"]):
                eligible.setdefault(name, [None]).append(before["files"][name]["hash"] if name in before["files"] else None)
        journal_path = directory / "publication-journal.json"
        if journal_path.exists() or journal_path.is_symlink():
            journal = json.loads(read_guarded(journal_path, MAX_EXPANDED_BYTES).content, object_pairs_hook=_pairs, parse_constant=_constant)
            if not isinstance(journal, dict) or set(journal) != {"schema_version", "preimage_metadata_hash", "eligible_images"} or journal["schema_version"] != "llm-wiki-maintenance-publication/v1" or not isinstance(journal["eligible_images"], dict):
                raise MaintenanceProtocolError("recovery-invalid", "Invalid publication preimage journal")
            if journal["preimage_metadata_hash"] != digest(read_guarded(directory / "maintenance-recovery.json", MAX_EXPANDED_BYTES).content):
                raise MaintenanceProtocolError("recovery-invalid", "Publication journal differs from its captured preimage")
            for name, images in journal["eligible_images"].items():
                from .validation import is_portable_relative_path
                from .knowledge_envelope import is_valid_sha256

                if not is_portable_relative_path(name) or not isinstance(images, list) or not images or any(v is not None and not is_valid_sha256(v) for v in images):
                    raise MaintenanceProtocolError("recovery-invalid", "Invalid eligible publication image")
                eligible.setdefault(name, []).extend(images)
        for name in {ADOPTION_FILENAME, MANIFEST_FILENAME}:
            eligible.setdefault(name, []).append(None)
        for name in set(current_files) | set(eligible):
            current_hash = digest(current_files[name]) if name in current_files else None
            if current_hash not in eligible.get(name, []):
                raise MaintenanceProtocolError("recovery-conflict", f"Recovery input changed outside the interrupted publication: {name}")
        with _capture_basis(root, current_files) as basis:
            if metadata["kind"] == "prepared-adoption":
                basis.source_snapshot = current
            if present is None:
                atomic_write_guarded_bytes(root / ADOPTION_FILENAME, files[ADOPTION_FILENAME], expected_existing=None)
            for name in sorted(set(current_files) - set(files)):
                unlink_guarded_bytes(root / name, expected=current_files[name])

            for name, content in sorted(files.items()):
                if name in {ADOPTION_FILENAME, MANIFEST_FILENAME}:
                    continue
                path = root / name
                ensure_guarded_directory(path.parent)
                previous = current_files.get(name)
                if previous != content:
                    atomic_write_guarded_bytes(path, content, expected_existing=previous)
            previous = current_files.get(MANIFEST_FILENAME)
            atomic_write_guarded_bytes(root / MANIFEST_FILENAME, files[MANIFEST_FILENAME], expected_existing=previous)
            guard_maintenance_owner(root)
    return {"adoption_id": expected_adoption_id, "restored": True, "state_hash": digest(canonical_bytes(manifest.maintenance_state)),
            "requires_sync": metadata["kind"] == "captured-preimage",
            "prose_basis_validated": metadata["kind"] != "captured-preimage"}
