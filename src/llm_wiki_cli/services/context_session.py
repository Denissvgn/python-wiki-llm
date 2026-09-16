"""Explicit bounded sessions with authoritative validation and portable deltas."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
import hashlib
import math
import os
from pathlib import Path
import subprocess
import sys
import shutil
from threading import RLock
import time
from typing import Any

from .. import __version__
from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from . import context_packet as packets
from .immutable import freeze
from .io import first_unsafe_path_component
from .task_contract import TaskContext, normalize_task_request, TASK_REQUEST_SCHEMA_V2, TASK_RESULT_SCHEMA_V2
from .task_context import TaskCancelledError, TaskRead, _counter, build_task_read, plan_source_read, validate_task_context
from .workflow_profile import WorkflowRequestError, bounded_int, canonical_json, content_id, exact_fields

SESSION_SCHEMA = "llm-wiki-context-session/v1"
DELTA_SCHEMA = "llm-wiki-task-delta/v1"
DELTA_SCHEMA_V2 = "llm-wiki-task-delta/v2"


def _memory_size(value, seen=None):
    seen = set() if seen is None else seen
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, Mapping):
        size += sum(_memory_size(k, seen) + _memory_size(v, seen) for k, v in value.items())
    elif isinstance(value, (tuple, list, set, frozenset)):
        size += sum(_memory_size(item, seen) for item in value)
    elif is_dataclass(value) and not isinstance(value, type):
        size += sum(_memory_size(getattr(value, field.name), seen) for field in fields(value))
    return size


def _root_stamp(path):
    if first_unsafe_path_component(path) is not None:
        raise WorkflowRequestError("workspace", "session roots cannot follow symlinks or reparse points")
    try:
        info = path.stat()
    except FileNotFoundError:
        return None
    if not info.st_ino or not info.st_dev:
        raise WorkflowRequestError("workspace", "stable filesystem identity is unavailable")
    return info.st_dev, info.st_ino


def _git_identity(root, metrics=None):
    """Hash local branch/index metadata; commands are fixed read-only Git queries."""
    if shutil.which("git") is None:
        return None

    def git(*args):
        if metrics is not None:
            metrics["git_queries"] = metrics.get("git_queries", 0) + 1
        try:
            result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                    timeout=5, check=False, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None
    git_dir = git("rev-parse", "--absolute-git-dir")
    if git_dir is None:
        return {"state": "no-git"}
    index_name = git("rev-parse", "--git-path", "index")
    if index_name is None:
        return None
    path = Path(os.fsdecode(index_name))
    if not path.is_absolute():
        path = root / path
    if path.exists():
        if path.is_symlink() or path.stat().st_size > 16_777_216:
            return None
        with path.open("rb") as stream:
            data = stream.read(16_777_217)
        if metrics is not None:
            metrics["git_index_bytes"] = metrics.get("git_index_bytes", 0) + len(data)
        if len(data) > 16_777_216:
            return None
        index = hashlib.sha256(data).hexdigest()
    else:
        index = None
    head, branch = git("rev-parse", "--verify", "HEAD"), git("symbolic-ref", "-q", "HEAD")
    return {"head": head.hex() if head else None, "branch": branch.hex() if branch else None, "index": index}


def _producer_identity(metrics=None):
    # Package sources are immutable installed inputs in normal use; detect an
    # editable provider changing under an existing session as well.
    root = Path(__file__).parent.parent
    files = {}
    used = 0
    for path in sorted(root.rglob("*.py")):
        with path.open("rb") as stream:
            raw = stream.read(16_777_217 - used)
        used += len(raw)
        if used > 16_777_216:
            return None
        files[path.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
        if metrics is not None:
            metrics["producer_files"] = metrics.get("producer_files", 0) + 1
            metrics["producer_bytes"] = metrics.get("producer_bytes", 0) + len(raw)
    environment = {key: value for key, value in os.environ.items() if key.startswith("LLM_WIKI_")}
    return content_id("llm-wiki-workflow-producer/v1", {"provider": __version__, "python": sys.version,
                                                       "files": files, "environment": environment})


@dataclass(frozen=True)
class SessionReply:
    """Portable content and separate non-identity session work telemetry."""

    state: str
    result_id: str | None
    context: TaskContext | None
    delta: Mapping[str, Any] | None
    _metadata: Mapping[str, Any]

    def metadata(self) -> dict[str, Any]:
        return json_detach(self._metadata)


def json_detach(value):
    import json
    return json.loads(canonical_json(value))


@dataclass(frozen=True)
class _Entry:
    read: TaskRead
    environment: str | None
    expires: float
    size: int
    owner: object


def build_delta(base: TaskContext, current: TaskContext) -> dict[str, Any]:
    before, after = base.to_payload(), current.to_payload()
    if (before.get("request_id") != after.get("request_id") or before.get("schema_version") != after.get("schema_version")
            or not base.ok or not current.ok):
        raise WorkflowRequestError("delta", "base and result requests must match")
    return {"schema_version": DELTA_SCHEMA_V2 if after.get("schema_version") == TASK_RESULT_SCHEMA_V2 else DELTA_SCHEMA,
            "base_id": base.result_id, "result_id": current.result_id,
            "request_id": after["request_id"],
            "updates": {key: value for key, value in after.items() if before.get(key) != value},
            "removals": sorted(set(before) - set(after))}


def apply_task_delta(base: str, delta: Mapping[str, Any], request: Mapping[str, Any], **options) -> TaskContext:
    data = exact_fields(delta, {"schema_version", "base_id", "result_id", "request_id", "updates", "removals"}, "delta")
    expected_schema = DELTA_SCHEMA_V2 if request.get("schema_version") == TASK_REQUEST_SCHEMA_V2 else DELTA_SCHEMA
    if set(data) != {"schema_version", "base_id", "result_id", "request_id", "updates", "removals"} or data["schema_version"] != expected_schema:
        raise WorkflowRequestError("delta", "unsupported delta schema")
    payload = validate_task_context(base, request, **options)
    if data["base_id"] != payload["result_id"] or data["request_id"] != payload["request_id"]:
        raise WorkflowRequestError("delta", "wrong or out-of-order delta base")
    updates = exact_fields(data["updates"], set(payload), "updates")
    removals = data["removals"]
    if (not isinstance(removals, list) or any(not isinstance(key, str) for key in removals)
            or len(removals) != len(set(removals)) or set(removals) & set(updates)
            or any(key not in payload for key in removals)):
        raise WorkflowRequestError("delta", "invalid or conflicting removals")
    for key in removals:
        del payload[key]
    payload.update(json_detach(updates))
    rendered = canonical_json(payload).decode("utf-8")
    validated = validate_task_context(rendered, request, **options)
    if validated["result_id"] != data["result_id"]:
        raise WorkflowRequestError("delta", "reconstructed result identity mismatch")
    return TaskContext(True, rendered, validated["accounting"], schema_version=validated["schema_version"])


class ContextSession:
    """A single trusted workspace. Methods serialize; events are hints only."""

    def __init__(self, *, src_dir=".", wiki_dir=DEFAULT_WIKI_DIR, profile=None, policy=None,
                 counter=None, source_selection=None, helper_cache_dir=None, allow_external_src=False,
                 max_entries=8, max_bytes=16_777_216, ttl_seconds: float = 300):
        bounded_int(max_entries, "max_entries", 128, minimum=0)
        bounded_int(max_bytes, "max_bytes", 268_435_456, minimum=0)
        if (isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, (int, float))
                or not math.isfinite(ttl_seconds) or not 0 < ttl_seconds <= 86400):
            raise WorkflowRequestError("ttl_seconds", "must be finite and between 0 and 86400")
        self._cwd = Path.cwd().resolve()
        self._source = validate_source_root(src_dir, "--src-dir", allow_external=allow_external_src)
        self._wiki = validate_path(wiki_dir, "--wiki-dir")
        self._source_stamp = _root_stamp(self._source)
        self._wiki_stamp = _root_stamp(self._wiki)
        self._options = {"src_dir": str(self._source), "wiki_dir": str(self._wiki), "profile": profile,
                         "policy": policy, "counter": counter, "source_selection": source_selection,
                         "helper_cache_dir": helper_cache_dir, "allow_external_src": allow_external_src}
        # Normalize once to detach caller-owned profile dictionaries.
        _, effective = normalize_task_request({"schema_version": "llm-wiki-task-request/v1"}, profile=profile, policy=policy)
        self._options["profile"] = effective
        self._limit, self._max_bytes, self._ttl = max_entries, max_bytes, ttl_seconds
        self._entries: OrderedDict[str, _Entry] = OrderedDict()
        self._owner = object()
        self._bytes = 0
        self._closed = False
        self._lock = RLock()
        self._dirty = False
        self._unsaved = False
        self._validation_work = {}

    def _roots_current(self):
        if Path.cwd().resolve() != self._cwd:
            raise WorkflowRequestError("workspace", "session cannot follow a changed working directory")
        if _root_stamp(self._source) != self._source_stamp:
            raise WorkflowRequestError("workspace", "source root object changed; create a new session")
        wiki_stamp = _root_stamp(self._wiki)
        if self._wiki_stamp != wiki_stamp:
            self._clear()
            self._wiki_stamp = wiki_stamp

    def _environment(self):
        git = _git_identity(self._source, self._validation_work)
        producer = _producer_identity(self._validation_work)
        if git is None or producer is None:
            return None
        return content_id("llm-wiki-session-environment/v1", {"git": git, "producer": producer})

    def _clear(self):
        self._entries.clear()
        self._bytes = 0

    def _drop(self, key):
        entry = self._entries.pop(key, None)
        if entry is not None:
            self._bytes -= entry.size

    def _owns(self, entry):
        read = entry.read
        captured = read.captured
        if entry.owner is not self._owner or read.wiki_root != self._wiki:
            return False
        if read.source_root is not None and read.source_root != self._source:
            return False
        if captured is not None and (captured.source_root != self._source or captured.wiki_root != self._wiki
                                     or captured.source_snapshot.root != self._source):
            return False
        return True

    def _validate(self, entry, environment, request, profile, counter, *, cold=False):
        if not self._owns(entry) or entry.environment != environment or (environment is None and not cold):
            return False
        read = entry.read
        captured = read.captured
        if not cold and captured is not None and any(module.get("language") != "python" for module in captured.inventory.values()):
            return False  # No implicit helper preparation or incomplete producer identity.
        source_work, wiki_work = {}, {}
        try:
            validate_task_context(read.result.rendered, request, profile=self._options["profile"],
                                  policy=self._options["policy"], counter=counter)
            self._validation_work["passes"] = self._validation_work.get("passes", 0) + 1
            if read.scoped_state is not None:
                from .task_context_v2 import ScopedTaskState
                state = read.scoped_state
                if (not isinstance(state, ScopedTaskState) or state.source_root != self._source
                        or state.wiki_root != self._wiki or (not cold and not state.cacheable)):
                    return False
                settings = dict(profile.settings)
                settings["max_wiki_bytes"] -= self._validation_work.get("wiki_bytes", 0)
                if settings["max_wiki_bytes"] <= 0:
                    return False
                state.revalidate(settings, source_metrics=source_work, wiki_metrics=wiki_work)
                return True
            if captured is not None:
                packets._assert_source_unchanged(captured.source_snapshot, captured.source_anchor, metrics=source_work)
                packets._assert_selection_unchanged(captured)
            packets._assert_wiki_unchanged(self._wiki, read.wiki_anchor, reject_all_symlinks=True,
                                         max_bytes=profile.settings["max_wiki_bytes"], metrics=wiki_work,
                                         expected_integrity=read.wiki_integrity)
        except (ValueError, OSError, RuntimeError):
            return False
        finally:
            for prefix, values in (("source", source_work), ("wiki", wiki_work)):
                for metric in ("files", "bytes"):
                    key = f"{prefix}_{metric}"
                    self._validation_work[key] = self._validation_work.get(key, 0) + values.get(metric, 0)
        return True

    def _build(self, request, *, cancelled, shared=None):
        try:
            scoped = request.get("schema_version") == TASK_REQUEST_SCHEMA_V2
            budget = None
            if scoped:
                _, profile = normalize_task_request(request, profile=self._options["profile"], policy=self._options["policy"])
                budget = profile.settings["max_wiki_bytes"] - self._validation_work.get("wiki_bytes", 0)
            read = build_task_read(request, **self._options, cancelled=cancelled, _reused_capture=shared,
                _defer_scoped_validation=scoped, _wiki_byte_budget=budget)
            if scoped and read.scoped_state is not None:
                initial_bytes = sum(len(item.content) for item in read.scoped_state.wiki_inputs.values())
                initial_bytes += sum(len(item.content) for item in read.scoped_state.wiki_ranges.values())
                self._validation_work["wiki_bytes"] = self._validation_work.get("wiki_bytes", 0) + initial_bytes
            return read
        except TaskCancelledError:
            self._clear()
            raise

    def _compatible_capture(self, normalized, profile, environment):
        if normalized["schema_version"] == TASK_REQUEST_SCHEMA_V2:
            return None
        paths, _, live, scope = plan_source_read(normalized, profile.settings, self._source)
        if not live:
            return None
        for entry in reversed(self._entries.values()):
            read = entry.read
            captured = read.captured
            if captured is None or read.result.to_payload()["basis"]["scope"] != scope:
                continue
            expected_paths = None if scope == "full-inventory" else frozenset(paths)
            if captured.source_snapshot.only_files != expected_paths:
                continue
            snapshot = captured.source_snapshot
            if (len(snapshot.captured_content_hashes) > profile.settings["max_files"] or
                    sum(item.size for item in snapshot.captured_file_integrity.values()) > profile.settings["max_source_bytes"]):
                continue
            if snapshot.capture_scan_limit is not None and snapshot.capture_scan_limit > min(100_000, max(4096, profile.settings["max_files"] * 128)):
                continue
            original = {key: read.normalized[key] for key in ("schema_version", "text", "kind", "anchors", "requirements")}
            if read.normalized["task_ref"] is not None:
                original["task_ref"] = read.normalized["task_ref"]
            if read.normalized["changes"] is not None:
                original["changes"] = read.normalized["changes"]
            original["options"] = read.profile.settings
            try:
                old_counter = _counter(read.profile.settings, self._options["counter"])
            except WorkflowRequestError:
                continue
            if self._validate(entry, environment, original, read.profile, old_counter):
                return captured
        return None

    def read(self, request, *, if_result_id=None, delta=False, reuse=True,
             cancelled: Callable[[], bool] | None = None) -> SessionReply:
        with self._lock:
            if self._closed:
                raise WorkflowRequestError("session", "session is closed")
            if type(delta) is not bool or type(reuse) is not bool:
                raise WorkflowRequestError("session", "delta and reuse must be booleans")
            if if_result_id is not None and (not isinstance(if_result_id, str) or
                    len(if_result_id) != 71 or not if_result_id.startswith("sha256:") or
                    any(c not in "0123456789abcdef" for c in if_result_id[7:])):
                raise WorkflowRequestError("if_result_id", "must be a canonical result identity")
            normalized, profile = normalize_task_request(request, profile=self._options["profile"], policy=self._options["policy"])
            counter = _counter(profile.settings, self._options["counter"])
            if self._unsaved:
                raise WorkflowRequestError("unsaved_buffers", "save or explicitly defer unsaved buffers before reading on-disk evidence")
            if cancelled is not None and (not callable(cancelled) or cancelled()):
                self._clear()
                raise WorkflowRequestError("cancelled", "session read cancelled")
            started = time.perf_counter_ns()
            self._validation_work = {}
            self._roots_current()
            now = time.monotonic()
            for key in list(self._entries):
                if self._entries[key].expires <= now:
                    self._drop(key)
            environment = self._environment()
            key = content_id("llm-wiki-session-request/v1", {"request": normalized,
                "counter": counter.identity, "counter_exact": counter.exact})
            entry = self._entries.get(key)
            base = next((item.read.result for item in self._entries.values()
                         if self._owns(item) and item.read.result.result_id == if_result_id), None) if if_result_id else None
            reused = bool(reuse and not self._dirty and entry is not None
                          and self._validate(entry, environment, request, profile, counter))
            if reused:
                assert entry is not None
                read = entry.read
                self._entries.move_to_end(key)
                capture_reused = True
            else:
                if entry is not None:
                    self._drop(key)
                shared = self._compatible_capture(normalized, profile, environment) if reuse and not self._dirty else None
                capture_reused = shared is not None
                read = self._build(request, cancelled=cancelled, shared=shared)
            self._dirty = False
            # A second independent validation guards the interval between a hit
            # check and publication. Failure discards state and performs one cold read.
            if reused and read.scoped_state is None and not self._validate(entry, self._environment(), request, profile, counter):
                self._drop(key)
                read = self._build(request, cancelled=cancelled)
                reused = False
                capture_reused = False
            self._roots_current()
            if cancelled is not None and cancelled():
                self._clear()
                raise WorkflowRequestError("cancelled", "session read cancelled")
            if read.result.ok and environment is not None and reuse and not reused and self._limit and self._max_bytes:
                detached = freeze(read)
                size = _memory_size(detached)
                if size <= self._max_bytes:
                    while self._entries and (len(self._entries) >= self._limit or self._bytes + size > self._max_bytes):
                        self._drop(next(iter(self._entries)))
                    self._entries[key] = _Entry(detached, environment, time.monotonic() + self._ttl, size, self._owner)
                    self._bytes += size
            current = read.result
            state, delta_payload = "full", None
            if current.ok and environment is not None and current.result_id == if_result_id:
                state = "unchanged"
            elif delta and base is not None and current.ok and base.to_payload().get("request_id") == normalized["request_id"]:
                candidate = build_delta(base, current)
                try:
                    reconstructed = apply_task_delta(base.rendered, candidate, request,
                        profile=self._options["profile"], policy=self._options["policy"], counter=counter)
                except ValueError:
                    reconstructed = None
                if reconstructed is not None and len(canonical_json(candidate)) < len(current.rendered.encode("utf-8")):
                    state, delta_payload = "delta", candidate
            snapshot = read.captured.source_snapshot if read.captured else None
            original_work = (read.scoped_state.original_work if read.scoped_state is not None
                             else current.to_payload().get("work", {})) or {}
            metadata = {"schema_version": SESSION_SCHEMA, "state": state, "result_id": current.result_id,
                        "request_id": normalized["request_id"], "base_id": if_result_id,
                        "reuse": {"capture": capture_reused, "selection": reused, "rendering": reused},
                        "work": {"captures": 0 if capture_reused else original_work.get("captures", 0),
                                 "validation_passes": self._validation_work.get("passes", 0),
                                 "validation_observed": dict(self._validation_work),
                                 "validation_source_files_per_pass": len(snapshot.captured_content_hashes) if snapshot else 0,
                                 "validation_source_bytes_per_pass": sum(item.size for item in snapshot.captured_file_integrity.values()) if snapshot else 0,
                                 "retained_bytes": self._bytes, "entries": len(self._entries),
                                 "elapsed_ns": time.perf_counter_ns() - started},
                        "accounting_scope": "context is canonical task text; session metadata and MCP/host framing are separate",
                        "reconstructed_context_bytes": len(current.rendered.encode("utf-8")),
                        "emitted_context_bytes": len(current.rendered.encode("utf-8")) if state == "full" else
                            len(canonical_json(delta_payload)) if delta_payload else 0,
                        "emitted_context_tokens": counter.count(current.rendered) if state == "full" else
                            counter.count(canonical_json(delta_payload).decode("utf-8")) if delta_payload else 0,
                        "delta_bytes": len(canonical_json(delta_payload)) if delta_payload else 0,
                        "environment_validation": "available" if environment is not None else "unavailable; cold read only",
                        "limitations": ["events are hints; on-disk inputs were validated", "unsaved buffers are excluded",
                                        "embedded task work describes its originating read", "helper-backed captures use cold reads"]}
            # Counter callbacks and delta reconstruction happen before this final
            # check, so neither can mutate inputs and leave a false live claim.
            if current.ok and not self._validate(_Entry(read, environment, 0, 0, self._owner), self._environment(),
                                                request, profile, counter, cold=True):
                self._clear()
                raise packets.ContextPacketSourceMutationError("session-inputs")
            self._roots_current()
            metadata["work"].update(validation_passes=self._validation_work.get("passes", 0),
                                    validation_observed=dict(self._validation_work),
                                    elapsed_ns=time.perf_counter_ns() - started)
            return SessionReply(state, current.result_id, current if state == "full" else None,
                                freeze(delta_payload) if delta_payload else None, freeze(metadata))

    def hint(self, *, unsaved_buffers=False):
        with self._lock:
            if self._closed or type(unsaved_buffers) is not bool:
                raise WorkflowRequestError("session", "invalid event or closed session")
            self._dirty = True
            self._unsaved = unsaved_buffers

    def close(self):
        with self._lock:
            self._clear()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
