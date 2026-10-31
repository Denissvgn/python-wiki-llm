"""Read-only storage size and explicit outgoing Git object checks."""

from __future__ import annotations

import json
import base64
import binascii
import heapq
import os
from pathlib import Path
import re
import subprocess
from threading import Event, Thread
from typing import Any

from .knowledge_artifacts import validated_artifact_bytes
from .knowledge_loader import load_knowledge_state
from .knowledge_index import _model_to_payload
from .contracts import TYPED_GRAPH_EXTENSION_KEY, SECTION_OWNERSHIP_EXTENSION_KEY
from .knowledge_storage import (
    GIT_FAILURE_BYTES, GIT_WARNING_BYTES, MAX_EXPANDED_BYTES, MAX_OBJECT_BYTES,
    MAX_ROOT_BYTES, ROOT_FILENAME, STORE_SCHEMA, KnowledgeStorageError,
    canonical_bytes, parse_store_root,
)
from .knowledge_storage_io import _absolute_path, read_guarded
from .knowledge_packs import (
    PACKED_SCHEMAS, packed_format, PACK_NAME, INDEX_NAME, INDEX_PAGE_NAME, INDEX_PAGE_BYTES, MAX_PACK_BYTES, MAX_INDEX_BYTES,
    parse_packed_root,
)
from .knowledge_storage_lifecycle import stored_object_paths
from .sync_manifest import MANIFEST_FILENAME
from .manifest_storage import OBJECT_NAME as MANIFEST_OBJECT_NAME, OBJECT_LIMIT as MANIFEST_OBJECT_LIMIT
from .wiki_surface_index import SURFACE_INDEX_FILENAME


def _git(root: Path, arguments: list[str], *, input_bytes: bytes | None = None,
         maximum: int = 16_777_216, environment: dict[str, str] | None = None) -> tuple[int, bytes]:
    """Drain both pipes with hard byte/time bounds; never invoke a shell."""
    env = {**(os.environ if environment is None else environment), "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
           "GIT_NO_LAZY_FETCH": "1", "GIT_PAGER": "cat"}
    command = ["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", str(root), *arguments]
    buffers = [bytearray(), bytearray()]
    exceeded = Event()
    try:
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=env) as process:
            assert process.stdout is not None and process.stderr is not None and process.stdin is not None
            stdin = process.stdin

            def drain(stream, buffer):
                try:
                    while True:
                        chunk = stream.read(65_536)
                        if not chunk:
                            return
                        if len(buffer) + len(chunk) > maximum:
                            exceeded.set()
                            process.kill()
                            return
                        buffer.extend(chunk)
                except (OSError, ValueError):
                    exceeded.set()

            def feed():
                try:
                    if input_bytes:
                        stdin.write(input_bytes)
                    stdin.close()
                except (BrokenPipeError, OSError, ValueError):
                    pass

            workers = [Thread(target=drain, args=(process.stdout, buffers[0]), daemon=True),
                       Thread(target=drain, args=(process.stderr, buffers[1]), daemon=True),
                       Thread(target=feed, daemon=True)]
            for worker in workers:
                worker.start()
            try:
                code = process.wait(timeout=30)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                process.wait()
                raise KnowledgeStorageError("git", "range inspection timed out", code="git-check-incomplete") from exc
            finally:
                for worker in workers:
                    worker.join(timeout=2)
            if exceeded.is_set() or any(worker.is_alive() for worker in workers):
                raise KnowledgeStorageError("git", "range inspection exceeded its output bound", code="git-check-incomplete")
            return code, bytes(buffers[0])
    except OSError as exc:
        raise KnowledgeStorageError("git", "Git is unavailable", code="git-check-incomplete") from exc


def inspect_git_range(project: str | Path, *, base: str, head: str) -> dict[str, Any]:
    """Inspect every blob in head minus base, including subsequently deleted files."""
    for name, ref in (("base", base), ("head", head)):
        if not isinstance(ref, str) or not ref or len(ref.encode("utf-8")) > 1024 or "\0" in ref:
            raise KnowledgeStorageError(name, "an explicit bounded Git reference is required")
    root = _absolute_path(Path(project))
    report: dict[str, Any] = {"base": base, "head": head, "complete": False,
                              "warnings": [], "failures": [], "objects": 0, "blobs": 0,
                              "git_history_changed": False, "network_used": False}
    try:
        code, shallow = _git(root, ["rev-parse", "--is-shallow-repository"])
        if code or shallow.strip() != b"false":
            raise KnowledgeStorageError("git", "a complete local Git repository is required", code="git-check-incomplete")
        code, promisor = _git(root, ["config", "--local", "--name-only", "--get-regexp",
                                    r"(^extensions\.partialclone$|^remote\..*\.promisor$)"])
        if code not in {0, 1} or promisor.strip():
            raise KnowledgeStorageError("git", "partial/promisor repositories require a separately completed local object database",
                                        code="git-check-incomplete")
        revisions = []
        for ref in (base, head):
            code, output = _git(root, ["rev-parse", "--verify", "--end-of-options", ref + "^{commit}"])
            if code or not re.fullmatch(rb"[0-9a-f]{40}(?:[0-9a-f]{24})?\n", output):
                raise KnowledgeStorageError("git", "base/head does not resolve to a local commit", code="git-check-incomplete")
            revisions.append(output.strip().decode("ascii"))
        code, listed = _git(root, ["rev-list", "--objects", "--no-object-names", "--missing=print",
                                  revisions[1], "^" + revisions[0], "--"])
        object_ids = listed.splitlines()
        if code or len(object_ids) > 100_000 or any(not re.fullmatch(rb"[0-9a-f]{40}(?:[0-9a-f]{24})?", oid) for oid in object_ids):
            raise KnowledgeStorageError("git", "range traversal is missing objects or exceeds its bound", code="git-check-incomplete")
        object_ids = sorted(set(object_ids))
        report["objects"] = len(object_ids)
        if object_ids:
            code, output = _git(root, ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
                                input_bytes=b"\n".join(object_ids) + b"\n")
            lines = output.splitlines()
            if code or len(lines) != len(object_ids):
                raise KnowledgeStorageError("git", "object metadata check is incomplete", code="git-check-incomplete")
            for expected, line in zip(object_ids, lines):
                parts = line.split()
                if len(parts) != 3 or parts[0] != expected or not parts[2].isdigit():
                    raise KnowledgeStorageError("git", "an object is missing or has invalid metadata", code="git-check-incomplete")
                if parts[1] != b"blob":
                    continue
                report["blobs"] += 1
                size = int(parts[2])
                item = {"object_id": expected.decode("ascii"), "bytes": size}
                if size >= GIT_FAILURE_BYTES:
                    report["failures"].append(item)
                elif size > GIT_WARNING_BYTES:
                    report["warnings"].append(item)
        report.update(complete=True, base_commit=revisions[0], head_commit=revisions[1])
    except KnowledgeStorageError as exc:
        report["error"] = {"code": exc.code, "message": exc.message}
    report["ok"] = report["complete"] and not report["failures"]
    return report


def storage_report(wiki_dir: str | Path, *, full: bool = False,
                   git_base: str | None = None, git_head: str | None = None) -> dict[str, Any]:
    if type(full) is not bool or (git_base is None) != (git_head is None):
        raise KnowledgeStorageError("request", "use a boolean full flag and both explicit Git range endpoints")
    root = _absolute_path(Path(wiki_dir))
    report: dict[str, Any] = {"schema_version": "llm-wiki-storage-report/v1", "format": "absent",
                              "integrity": "not-audited", "artifacts": [], "warnings": [], "failures": [],
                              "objects": 0, "object_bytes": 0, "unreferenced_objects": None,
                              "unknown_entries": [], "git_history_changed": False}
    report["retention"] = {
        "namespace_complete": False, "size_inspection_complete": False,
        "max_inspection_bytes": MAX_EXPANDED_BYTES,
        "referenced_objects": None, "referenced_bytes": None,
        "unreferenced_candidates": None, "unreferenced_candidate_bytes": None,
        "candidate_validation": "not-performed",
        "qualification": "Sizes and reachability are separate; only prune preview validates cleanup candidates. Incomplete inspection is not a deletion decision.",
    }
    try:
        return _storage_report(root, report, full=full, git_base=git_base, git_head=git_head)
    except KnowledgeStorageError as exc:
        if exc.code != "storage-limit":
            raise
        # Preserve failure and bounded partial size observations without running
        # another audit, reading orphan payloads or changing the inspection limit.
        report["error"] = {"code": exc.code, "message": str(exc)}
        report["failures"].append({"path": exc.field, "reason": exc.code, "message": exc.message})
        report["next_action"] = _retention_recovery(root)
        report["ok"] = False
        return report


def _retention_recovery(root: Path) -> dict[str, Any]:
    """Offer the maintained preview route, never a size-based cleanup decision."""
    return {
        "operation": "prune-storage", "dry_run": True,
        "argv": ["llm-wiki", "knowledge", "prune-storage", "--wiki-dir", str(root)],
        "instructions": [
            "Preview requires a valid committed indexed knowledge or manifest store; it can remain unavailable or budget-exhausted.",
            "Review validated candidates, retained unknown files and budget_exhausted; save the exact plan outside the wiki with --save-plan.",
            "Apply only explicitly approved candidates using --plan and --apply, with --recovery-dir outside the wiki; verified recovery copies precede deletion.",
            "Repeat storage-check --full before release capture. Keep inspection and capture limits unchanged; preserve active anchors and Git history.",
        ],
    }


def _storage_report(root: Path, report: dict[str, Any], *, full: bool,
                    git_base: str | None, git_head: str | None) -> dict[str, Any]:
    """Inspect within existing bounds; the caller retains storage-limit gaps."""
    for name in (ROOT_FILENAME, SURFACE_INDEX_FILENAME, MANIFEST_FILENAME):
        path = _absolute_path(root / name)
        if not path.exists():
            report["failures"].append({"path": name, "reason": "missing"})
            continue
        size = path.stat().st_size
        report["artifacts"].append({"path": name, "bytes": size})
        if size >= GIT_FAILURE_BYTES:
            report["failures"].append({"path": name, "bytes": size, "reason": "git-file-policy"})
        elif size > GIT_WARNING_BYTES:
            report["warnings"].append({"path": name, "bytes": size, "reason": "large-git-file"})
    root_path = root / ROOT_FILENAME
    if root_path.exists():
        # Quick reporting never allocates an oversized legacy monolith just to
        # explain why it cannot be pushed. Full inspection is explicitly selected.
        if root_path.stat().st_size > MAX_ROOT_BYTES and not full:
            report["format"] = "large-root; full inspection required"
        else:
            raw = read_guarded(root_path, MAX_EXPANDED_BYTES).content
            if raw.startswith(b"version https://git-lfs.github.com/spec/v1"):
                report["format"] = "lfs-pointer"
                report["failures"].append({"path": ROOT_FILENAME, "reason": "lfs-content-not-hydrated"})
            else:
                try:
                    data = json.loads(raw)
                    version = data.get("schema_version")
                    if version == STORE_SCHEMA:
                        parsed = parse_store_root(raw)
                        report["format"] = "sharded-v2"
                        report["declared_records"] = {k: v["count"] for k, v in parsed["collections"].items()}
                    elif version in PACKED_SCHEMAS:
                        parsed = parse_packed_root(raw)
                        report["format"] = packed_format(parsed)
                        report["packing"] = parsed["packing"]
                        report["declared_records"] = {k: v["count"] for k, v in parsed["store"]["collections"].items()}
                    elif version == "llm-wiki-knowledge/v1":
                        report["format"] = "v1"
                        report["compact_bytes_by_kind"] = {k: len(canonical_bytes(v)) for k, v in data.items()}
                    else:
                        raise KnowledgeStorageError("schema_version", "unsupported storage schema")
                except (ValueError, AttributeError, UnicodeError) as exc:
                    report["failures"].append({"path": ROOT_FILENAME, "reason": "invalid-root", "message": str(exc)})
    owned, unknown = stored_object_paths(root)
    report["unknown_entries"] = unknown
    report["retention"]["namespace_complete"] = True
    largest = []
    object_sizes = {}
    for name in owned:
        size = (root / name).stat().st_size
        object_sizes[name] = size
        report["objects"] += 1
        report["object_bytes"] += size
        if report["object_bytes"] > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("objects", "size inspection exceeds its total byte bound", code="storage-limit")
        ceiling = (MANIFEST_OBJECT_LIMIT if MANIFEST_OBJECT_NAME.fullmatch(name) else MAX_PACK_BYTES if PACK_NAME.fullmatch(name)
                   else INDEX_PAGE_BYTES if INDEX_PAGE_NAME.fullmatch(name) else MAX_INDEX_BYTES if INDEX_NAME.fullmatch(name) else MAX_OBJECT_BYTES)
        if size > ceiling:
            report["failures"].append({"path": name, "bytes": size, "reason": "object-ceiling"})
        largest.append({"path": name, "bytes": size})
    report["retention"]["size_inspection_complete"] = True
    report["largest_objects"] = sorted(largest, key=lambda item: (-item["bytes"], item["path"]))[:10]
    if full and report["format"] != "lfs-pointer":
        try:
            state = load_knowledge_state(root)
            if state.validated_artifacts is None or state.knowledge is None:
                raise KnowledgeStorageError("knowledge", "committed native artifacts are absent")
            artifacts = state.validated_artifacts
            report["integrity"] = "valid-committed-snapshot"
            report["unreferenced_objects"] = sorted(set(owned) - set(artifacts.storage_objects))
            report["logical_records"] = {"concepts": len(state.knowledge.concepts), "relationships": len(state.knowledge.relationships)}
            report["referenced_object_bytes"] = sum(map(len, artifacts.storage_objects.values()))
            report["retention"].update(
                referenced_objects=len(artifacts.storage_objects),
                referenced_bytes=report["referenced_object_bytes"],
                unreferenced_candidates=len(report["unreferenced_objects"]),
                unreferenced_candidate_bytes=sum(object_sizes[name] for name in report["unreferenced_objects"]),
            )
            if report["unreferenced_objects"]:
                report["next_action"] = _retention_recovery(root)
            _, raw = validated_artifact_bytes(artifacts)
            report["root_bytes"] = len(raw)
            from .knowledge_model import _concept_to_payload, _relationship_to_payload
            extensions = state.knowledge.extensions
            groups = {"concepts": (_concept_to_payload(c) for c in state.knowledge.concepts),
                      "relationships": (_relationship_to_payload(r) for r in state.knowledge.relationships),
                      "edges": extensions.get(TYPED_GRAPH_EXTENSION_KEY, {}).get("edges", []),
                      "sections": extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY, {}).get("pages", [])}
            sizes: dict[str, int] = {}
            largest_records = []
            for kind, records in groups.items():
                sizes[kind] = 0
                for index, record in enumerate(records):
                    size = len(canonical_bytes(record))
                    sizes[kind] += size
                    identity = str(record.get("locator") or record.get("key") or record.get("page_locator") or index)
                    item = (size, kind, identity)
                    if len(largest_records) < 10:
                        heapq.heappush(largest_records, item)
                    elif item > largest_records[0]:
                        heapq.heapreplace(largest_records, item)
            sizes["extensions"] = 0
            for key, value in extensions.items():
                if key in {TYPED_GRAPH_EXTENSION_KEY, SECTION_OWNERSHIP_EXTENSION_KEY}:
                    continue
                size = len(canonical_bytes(value))
                sizes["extensions"] += size
                item = (size, "extensions", key)
                if len(largest_records) < 10:
                    heapq.heappush(largest_records, item)
                elif item > largest_records[0]:
                    heapq.heapreplace(largest_records, item)
            report["logical_record_bytes_by_kind"] = sizes
            report["largest_records"] = [{"bytes": n, "kind": k, "id": i} for n, k, i in sorted(largest_records, reverse=True)]
            if artifacts.storage_statistics:
                report.update(artifacts.storage_statistics)
        except ValueError as exc:
            report["integrity"] = "invalid"
            report["failures"].append({"reason": "full-audit-failed", "message": str(exc)})
    if git_base is not None and git_head is not None:
        report["git"] = inspect_git_range(root, base=git_base, head=git_head)
    report["ok"] = not report["failures"] and report.get("git", {"ok": True})["ok"]
    return report


def _review_records(wiki_dir: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Logical review keys preserve duplicates and avoid physical pack identities."""
    state = load_knowledge_state(wiki_dir)
    if state.knowledge is None or state.validated_artifacts is None:
        raise KnowledgeStorageError("knowledge", "a fully valid committed snapshot is required")
    data = _model_to_payload(state.knowledge)
    rows = {"bundle": data["bundle"]}
    for concept in data["concepts"]:
        rows["concept:" + concept["locator"]] = concept
    occurrences: dict[str, int] = {}
    from .knowledge_storage import digest
    for relationship in data["relationships"]:
        key = digest(canonical_bytes(relationship))
        index = occurrences.get(key, 0)
        occurrences[key] = index + 1
        rows[f"relationship:{key}:{index}"] = relationship
    for key, value in data.get("extensions", {}).items():
        if key in {TYPED_GRAPH_EXTENSION_KEY, SECTION_OWNERSHIP_EXTENSION_KEY}:
            field = "edges" if key == TYPED_GRAPH_EXTENSION_KEY else "pages"
            identity = "key" if field == "edges" else "page_locator"
            rows["extension:" + key] = {k: v for k, v in value.items() if k != field}
            for item in value[field]:
                rows[f"{field}:{item[identity]}"] = item
        else:
            rows["extension:" + key] = value
    artifacts = state.validated_artifacts
    return rows, {"root": str(_absolute_path(Path(wiki_dir))),
                  "knowledge": artifacts.knowledge_index_hash, "surface": artifacts.surface_index_hash,
                  "envelope": artifacts.evaluated_envelope_hash, "governance": artifacts.governance_hash,
                  "manifest": state.manifest_basis.to_payload() if state.manifest_basis is not None else None}


def _review_cursor(review_id: str, offset: int) -> str:
    return base64.urlsafe_b64encode(canonical_bytes({"v": 1, "id": review_id, "offset": offset})).decode("ascii")


def _review_position(cursor: str, review_id: str, total: int) -> int:
    try:
        data = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
        valid = (isinstance(data, dict) and set(data) == {"v", "id", "offset"}
                 and type(data["v"]) is int and data["v"] == 1 and data["id"] == review_id
                 and type(data["offset"]) is int and 0 < data["offset"] < total)
    except (ValueError, UnicodeError, binascii.Error):
        valid = False
    if not valid:
        raise KnowledgeStorageError("cursor", "invalid continuation or changed snapshot/scope; restart review")
    return data["offset"]


def _review_row(key: str, index: int, current: dict, previous: dict, diff: bool) -> dict[str, Any]:
    from .knowledge_storage import digest
    row: dict[str, Any] = {"key": key, "record_index": index,
        "change": "present" if not diff else "added" if key not in previous else "removed" if key not in current else "modified"}
    values = {}
    for label, records in (("before", previous), ("after", current)):
        if key in records:
            raw = canonical_bytes(records[key])
            row[label] = {"hash": digest(raw), "bytes": len(raw)}
            values[label] = records[key]
    return {**row, "values": values}


def _review_record_chunk(row: dict, *, review_id: str, offset: int, max_bytes: int,
                         validation_scope: str) -> dict[str, Any]:
    """Deliver exact canonical row bytes, including identities too large for one page."""
    from .knowledge_storage import digest
    raw = canonical_bytes(row)
    if offset >= len(raw):
        raise KnowledgeStorageError("record_offset", "must be within the canonical record bytes")
    result: dict[str, Any] = {"schema_version": "llm-wiki-storage-record/v1", "ok": True,
        "review_id": review_id, "record_index": row["record_index"], "validation_scope": validation_scope,
        "whole_snapshot_validated": validation_scope == "full-committed-snapshots",
        "hash": digest(raw), "bytes": len(raw), "offset": offset, "data_base64": "",
        "next_offset": None, "complete": False}
    # Reserve the largest next-offset spelling and include the CLI newline.
    result["next_offset"] = max(9999, len(raw))
    capacity = (max_bytes - len(canonical_bytes(result))) // 4 * 3
    if capacity <= 0:
        raise KnowledgeStorageError("review", "record envelope cannot fit the output bound")
    end = min(len(raw), offset + capacity)
    result.update(data_base64=base64.b64encode(raw[offset:end]).decode("ascii"),
                  next_offset=end if end < len(raw) else None, complete=offset == 0 and end == len(raw))
    return result


def review_storage(wiki_dir: str | Path, *, against: str | Path | None = None,
                   limit: int = 100, max_bytes: int = 262_144, selectors=None,
                   cursor: str | None = None, record_index: int | None = None,
                   review_id: str | None = None, record_offset: int = 0) -> dict[str, Any]:
    """Page logical snapshots or recover an exact row under the same output bounds.

    Each call repeats its original validation/materialization scope. Continuations
    bind snapshot commitments, native locations, operation and canonical ordering;
    they are consistency checks, not authorization or live-source freshness proof.
    """
    if type(limit) is not int or not 1 <= limit <= 10_000 or type(max_bytes) is not int or not 1024 <= max_bytes <= MAX_OBJECT_BYTES:
        raise KnowledgeStorageError("review", "limit must be 1..10000 and max_bytes 1024..8388608")
    if (cursor is not None and (not isinstance(cursor, str) or not 1 <= len(cursor) <= 1024)
            or type(record_offset) is not int or record_offset < 0
            or record_index is None and (review_id is not None or record_offset != 0)
            or record_index is not None and (type(record_index) is not int or record_index < 0
                or not isinstance(review_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", review_id)
                or cursor is not None)):
        raise KnowledgeStorageError("review", "use a bounded cursor or a record_index/review_id with a nonnegative byte offset")
    from .knowledge_storage import digest
    capture = None
    if selectors is None:
        current, current_basis = _review_records(wiki_dir)
    else:
        if against is not None:
            raise KnowledgeStorageError("selectors", "scoped comparison is not supported")
        from .knowledge_storage_access import capture_knowledge_slice
        capture = capture_knowledge_slice(wiki_dir, selectors, max_records=10_000)
        current = {f"{kind}:{row['owner']}:{row['id']}": row["value"]
                   for kind, rows in capture.slice.to_payload()["records"].items() for row in rows}
        current_basis = {"root": str(_absolute_path(Path(wiki_dir))), "selection": capture.slice.to_payload(),
                         "commit": capture.manifest.artifact_hashes.to_payload() if capture.manifest.artifact_hashes else None,
                         "generation_inputs": dict(capture.manifest.generation_inputs),
                         "maintenance": capture.manifest.maintenance_state_hash, "adoption": capture.manifest.adoption_id}
    previous, previous_basis = ({}, None) if against is None else _review_records(against)
    result: dict[str, Any] = {"schema_version": "llm-wiki-storage-review/v1", "ok": True,
        "operation": "inspect" if against is None else "diff", "validation_scope": "full-committed-snapshots",
        "records": [], "total": 0, "omitted": 0, "values_omitted": 0, "complete": True}
    if capture is not None:
        result.update(schema_version="llm-wiki-storage-review/v2", validation_scope="selected-records-and-policy",
                      whole_snapshot_validated=False)
    keys = [key for key in sorted(current.keys() | previous.keys())
            if against is None or (key in current) != (key in previous)
            or canonical_bytes(current.get(key)) != canonical_bytes(previous.get(key))]
    binding = digest(canonical_bytes({"contract": "storage-review-order/v1", "operation": result["operation"],
        "scope": result["validation_scope"], "after": current_basis, "before": previous_basis}))
    if record_index is not None:
        if review_id != binding:
            raise KnowledgeStorageError("review_id", "changed snapshot/scope; restart review")
        if record_index >= len(keys):
            raise KnowledgeStorageError("record_index", "outside this review's ordered records")
        chunk = _review_record_chunk(_review_row(keys[record_index], record_index, current, previous, against is not None),
                                    review_id=binding, offset=record_offset, max_bytes=max_bytes,
                                    validation_scope=result["validation_scope"])
        if capture is not None:
            capture.finish()
        return chunk
    start = 0 if cursor is None else _review_position(cursor, binding, len(keys))
    result.update(review_id=binding, offset=start, total=len(keys), next_cursor=None, remaining=len(keys) - start,
                  enumeration_complete=False)
    records = result["records"]
    used = 0

    def envelope(count: int, omitted_values: int) -> dict[str, Any]:
        end = start + count
        return {**result, "records": [], "omitted": len(keys) - count, "remaining": len(keys) - end,
                "values_omitted": omitted_values, "enumeration_complete": end == len(keys),
                "complete": start == 0 and end == len(keys) and omitted_values == 0,
                "next_cursor": _review_cursor(binding, end) if end < len(keys) else None}

    omitted_values = 0
    for index in range(start, min(len(keys), start + limit)):
        expanded = _review_row(keys[index], index, current, previous, against is not None)
        raw = canonical_bytes(expanded)
        candidates = [expanded, {k: v for k, v in expanded.items() if k != "values"}]
        candidates[1]["values_omitted"] = True
        candidates.append({"record_index": index, "key_omitted": True, "values_omitted": True,
                           "record_hash": digest(raw), "record_bytes": len(raw)})
        for row in candidates:
            count = len(records) + 1
            omissions = omitted_values + bool(row.get("values_omitted"))
            size = len(canonical_bytes(row)) - 1
            # Empty-array envelope plus comma-separated rows, including CLI newline.
            if len(canonical_bytes(envelope(count, omissions))) + used + size + count - 1 <= max_bytes:
                records.append(row)
                used += size
                omitted_values = omissions
                break
        else:
            if not records:
                raise KnowledgeStorageError("review", "record envelope cannot fit the output bound")
            break
    result = {**envelope(len(records), omitted_values), "records": records}
    if capture is not None:
        capture.finish()
    return result
