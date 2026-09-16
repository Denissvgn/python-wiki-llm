"""Read-only storage size and explicit outgoing Git object checks."""

from __future__ import annotations

import json
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
from .knowledge_storage_lifecycle import stored_object_paths
from .sync_manifest import MANIFEST_FILENAME
from .wiki_surface_index import SURFACE_INDEX_FILENAME


def _git(root: Path, arguments: list[str], *, input_bytes: bytes | None = None,
         maximum: int = 16_777_216) -> tuple[int, bytes]:
    """Drain both pipes with hard byte/time bounds; never invoke a shell."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
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
                    elif version == "llm-wiki-knowledge/v1":
                        report["format"] = "v1"
                        report["compact_bytes_by_kind"] = {k: len(canonical_bytes(v)) for k, v in data.items()}
                    else:
                        raise KnowledgeStorageError("schema_version", "unsupported storage schema")
                except (ValueError, AttributeError, UnicodeError) as exc:
                    report["failures"].append({"path": ROOT_FILENAME, "reason": "invalid-root", "message": str(exc)})
    owned, unknown = stored_object_paths(root)
    report["unknown_entries"] = unknown
    largest = []
    for name in owned:
        size = (root / name).stat().st_size
        report["objects"] += 1
        report["object_bytes"] += size
        if report["object_bytes"] > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("objects", "size inspection exceeds its total byte bound", code="storage-limit")
        if size > MAX_OBJECT_BYTES:
            report["failures"].append({"path": name, "bytes": size, "reason": "object-ceiling"})
        largest.append({"path": name, "bytes": size})
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
            _, raw = validated_artifact_bytes(artifacts)
            report["root_bytes"] = len(raw)
            logical = _model_to_payload(state.knowledge)
            extensions = logical.get("extensions", {})
            groups = {"concepts": logical["concepts"], "relationships": logical["relationships"],
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
            if artifacts.storage_objects:
                def reference_count(value):
                    if isinstance(value, dict):
                        return int(set(value) == {"$value"}) + sum(reference_count(v) for v in value.values())
                    if isinstance(value, list):
                        return sum(reference_count(v) for v in value)
                    return 0
                refs = sum(reference_count(json.loads(content)) for content in artifacts.storage_objects.values())
                descriptors = json.loads(raw)["collections"]["values"]["count"]
                report["deduplication"] = {"descriptor_references": refs, "unique_descriptors": descriptors,
                                           "repeated_references": max(0, refs - descriptors)}
        except ValueError as exc:
            report["integrity"] = "invalid"
            report["failures"].append({"reason": "full-audit-failed", "message": str(exc)})
    if git_base is not None and git_head is not None:
        report["git"] = inspect_git_range(root, base=git_base, head=git_head)
    report["ok"] = not report["failures"] and report.get("git", {"ok": True})["ok"]
    return report
