"""Durable external-host observations; never a runner or admission authority.

The host records bytes at its actual inclusion/call/edit boundaries. Structural
validation detects missing or altered evidence but cannot establish that a model
ran, that isolation was enforced, or that a host-supplied receipt is authentic.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from threading import RLock
import time
from typing import Any

from tests.provider_conformance.model import canonical_json

SCHEMA = "native-workflow-run-trace/v1"
MAX_EVENT_BYTES = 65_536
MAX_BLOB_BYTES = 16_777_216
MAX_TRACE_BYTES = 67_108_864
MAX_EVENTS = 10_000
OUTCOMES = {"passed", "failed", "cancelled", "timed-out", "unsupported", "unavailable", "integration-failed"}
_HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_BINDINGS = {"task", "protocol", "source", "wiki", "oracle", "provider", "profile", "original_roots"}
_FIELDS = {
    "context": {"context_id", "blob", "counter_id", "counter_mode", "canonical_tokens", "host_framing_tokens"},
    "model-start": {"call_id", "request", "context_ids"},
    "model-end": {"call_id", "response", "receipt", "outcome", "input_tokens", "output_tokens"},
    "tool-start": {"call_id", "name", "arguments"},
    "tool-end": {"call_id", "result", "outcome"},
    "source-read": {"path", "blob"},
    "edit": {"path", "before", "after"},
    "check-start": {"call_id", "argv", "cwd"},
    "check-end": {"call_id", "stdout", "stderr", "exit_code", "compilation", "oracle"},
    "resources": {"preparation_ns", "validation_bytes", "peak_memory_bytes"},
    "cleanup": {"original_before", "original_after", "workspace_removed", "receipt"},
    "finish": {"outcome", "exception_type"},
}
_BLOBS = {
    "context": ("blob",), "model-start": ("request",), "model-end": ("response", "receipt"),
    "tool-start": ("arguments",), "tool-end": ("result",), "source-read": ("blob",),
    "edit": ("before", "after"), "check-end": ("stdout", "stderr"), "cleanup": ("receipt",),
}


class TraceError(ValueError):
    """Trace evidence is incomplete, inconsistent, or outside its bounds."""


def identity(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _object(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise TraceError("Unexpected trace fields")
    return dict(value)


def _identifier(value: Any) -> None:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise TraceError("Invalid trace identifier")


def _label(value: Any) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 512 or "\0" in value:
        raise TraceError("Invalid host/model identity")


def _digest(value: Any, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        raise TraceError("Invalid content identity")


def _number(value: Any, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise TraceError("Invalid observation count")


def _path(value: Any, *, directory: bool = False) -> None:
    if directory and value == ".":
        return
    if (not isinstance(value, str) or not value or value == "." or len(value.encode("utf-8")) > 4096
            or "\\" in value or ":" in value or any(ord(char) < 32 for char in value)
            or PurePosixPath(value).is_absolute() or ".." in value.split("/")
            or str(PurePosixPath(value)) != value):
        raise TraceError("Observation path must be portable and workspace-relative")


def validate_manifest(value: Any) -> dict[str, Any]:
    data = _object(value, {"schema_version", "attempt_id", "task_id", "arm", "repetition",
                           "execution_kind", "host", "model", "settings", "admission", "bindings"})
    if data["schema_version"] != SCHEMA or data["arm"] not in {"A", "B", "C"}:
        raise TraceError("Unsupported run manifest")
    for field in ("attempt_id", "task_id"):
        _identifier(data[field])
    _label(data["host"])
    _number(data["repetition"])
    bindings = _object(data["bindings"], _BINDINGS)
    for field, digest in bindings.items():
        _digest(digest, optional=field in {"provider", "profile"} and data["arm"] == "A")
    _digest(data["settings"], optional=data["execution_kind"] == "replay")
    _digest(data["admission"], optional=data["execution_kind"] == "replay")
    if data["execution_kind"] == "external-host":
        _label(data["model"])
    elif data["execution_kind"] != "replay" or data["model"] is not None:
        raise TraceError("Replay must not claim a model identity")
    if len(canonical_json(data)) > MAX_EVENT_BYTES:
        raise TraceError("Manifest exceeds its byte bound")
    return json.loads(canonical_json(data))


def _validate_event(kind: str, value: Any) -> dict[str, Any]:
    if not isinstance(kind, str) or kind not in _FIELDS:
        raise TraceError("Unknown observation kind")
    data = _object(value, _FIELDS[kind])
    for field in _BLOBS.get(kind, ()):
        _digest(data[field], optional=kind in {"model-end", "tool-end", "edit"})
    if "call_id" in data:
        _identifier(data["call_id"])
    if "outcome" in data and data["outcome"] not in OUTCOMES:
        raise TraceError("Unknown attempt/call disposition")
    if kind == "context":
        _identifier(data["context_id"])
        if not isinstance(data["counter_id"], str) or not 1 <= len(data["counter_id"]) <= 512:
            raise TraceError("Missing context counter identity")
        if data["counter_mode"] not in {"exact", "estimated"}:
            raise TraceError("Missing context counting qualification")
        _number(data["canonical_tokens"], optional=True)
        _number(data["host_framing_tokens"], optional=True)
    elif kind == "model-start":
        ids = data["context_ids"]
        if not isinstance(ids, list) or len(ids) > 100:
            raise TraceError("Context inclusion list exceeds its bound")
        for context_id in ids:
            _identifier(context_id)
        if len(set(ids)) != len(ids):
            raise TraceError("Context cannot be included twice in one call")
    elif kind == "model-end":
        _number(data["input_tokens"], optional=True)
        _number(data["output_tokens"], optional=True)
        if data["outcome"] == "passed" and data["response"] is None:
            raise TraceError("Successful model call lacks response bytes")
    elif kind == "tool-start":
        _identifier(data["name"])
    elif kind in {"source-read", "edit"}:
        _path(data["path"])
        if kind == "edit" and data["before"] is None and data["after"] is None:
            raise TraceError("An edit must retain before or after bytes")
    elif kind == "check-start":
        _path(data["cwd"], directory=True)
        args = data["argv"]
        if not isinstance(args, list) or not 1 <= len(args) <= 128:
            raise TraceError("Check argv must be explicit and bounded")
        if any(not isinstance(arg, str) or len(arg) > 4096 or "\0" in arg for arg in args):
            raise TraceError("Invalid check argument")
    elif kind == "check-end":
        if data["exit_code"] is not None and (type(data["exit_code"]) is not int or not -255 <= data["exit_code"] <= 255):
            raise TraceError("Invalid process exit observation")
        if any(data[field] not in {"passed", "failed", "not-evaluated"} for field in ("compilation", "oracle")):
            raise TraceError("Compilation and oracle outcomes must be separate")
    elif kind == "resources":
        for amount in data.values():
            _number(amount, optional=True)
    elif kind == "cleanup":
        _digest(data["original_before"])
        _digest(data["original_after"])
        if type(data["workspace_removed"]) is not bool:
            raise TraceError("Cleanup observation must be explicit")
    elif kind == "finish" and data["exception_type"] is not None:
        _identifier(data["exception_type"])
    return data


class _TraceState:
    def __init__(self, manifest: dict[str, Any]):
        self.manifest = manifest
        self.contexts: dict[str, dict[str, Any]] = {}
        self.calls: dict[str, str] = {}
        self.pending: dict[str, str] = {}
        self.outcome: str | None = None
        self.cleanup: dict[str, Any] | None = None
        self.model_responses = 0
        self.metrics: Counter[str] = Counter()
        self.oracle_outcomes: Counter[str] = Counter()

    def accept(self, kind: str, data: dict[str, Any]) -> None:
        if self.outcome is not None:
            raise TraceError("Observation follows the terminal event")
        if self.cleanup is not None and kind != "finish":
            raise TraceError("Activity follows cleanup")
        if kind == "context":
            if data["context_id"] in self.contexts:
                raise TraceError("Duplicate context observation")
            self.contexts[data["context_id"]] = data
        elif kind.endswith("-start"):
            call_id = data["call_id"]
            if call_id in self.calls:
                raise TraceError("Duplicate call identity")
            if kind == "model-start" and any(context_id not in self.contexts for context_id in data["context_ids"]):
                raise TraceError("Model call references unrecorded context")
            self.calls[call_id] = kind
            self.pending[call_id] = kind
        elif kind.endswith("-end"):
            call_id = data["call_id"]
            if self.pending.get(call_id) != kind.removesuffix("-end") + "-start":
                raise TraceError("Missing, duplicate, or mismatched call start")
            if kind == "model-end":
                if (self.manifest["execution_kind"] == "external-host" and data["outcome"] == "passed"
                        and data["receipt"] is None):
                    raise TraceError("External model response lacks a host receipt reference")
                self.model_responses += data["outcome"] == "passed"
            elif kind == "check-end":
                self.oracle_outcomes[data["oracle"]] += 1
            del self.pending[call_id]
        elif kind == "cleanup":
            if self.cleanup is not None:
                raise TraceError("Duplicate cleanup observation")
            if data["original_before"] != self.manifest["bindings"]["original_roots"]:
                raise TraceError("Cleanup refers to a different original input basis")
            self.cleanup = data
        elif kind == "finish":
            if data["outcome"] == "passed":
                if self.pending or self.cleanup is None:
                    raise TraceError("Completed attempt lacks call outcomes or cleanup")
                if not self.cleanup["workspace_removed"] or self.cleanup["original_before"] != self.cleanup["original_after"]:
                    raise TraceError("Completed attempt lacks original-root integrity")
                if self.manifest["execution_kind"] == "external-host" and not self.model_responses:
                    raise TraceError("Completed external attempt lacks model observations")
            self.outcome = data["outcome"]
        self.metrics[kind] += 1


class AttemptTrace:
    """Append observations at host boundaries; never invoke models or commands."""

    def __init__(self, directory: Path, manifest: Mapping[str, Any]):
        self.manifest = validate_manifest(manifest)
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        (self.directory / "blobs").mkdir()
        raw = canonical_json(self.manifest)
        with (self.directory / "manifest.json").open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        self._previous = identity(raw)
        self._state = _TraceState(self.manifest)
        self._started = time.monotonic_ns()
        self._sequence = 0
        self._bytes = len(raw)
        self._lock = RLock()
        self._blobs: set[str] = set()
        self._stream = (self.directory / "events.jsonl").open("xb")

    def blob(self, raw: bytes) -> str:
        if not isinstance(raw, bytes) or len(raw) > MAX_BLOB_BYTES:
            raise TraceError("Artifact exceeds its byte bound")
        key = identity(raw)
        with self._lock:
            if self._stream.closed:
                raise TraceError("Attempt is closed")
            if key not in self._blobs:
                if len(self._blobs) >= MAX_EVENTS:
                    raise TraceError("Attempt exceeds its artifact count bound")
                if self._bytes + len(raw) > MAX_TRACE_BYTES - MAX_EVENT_BYTES:
                    raise TraceError("Attempt exceeds its evidence budget")
                with (self.directory / "blobs" / key[7:]).open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                self._bytes += len(raw)
                self._blobs.add(key)
        return key

    def record(self, kind: str, observation: Mapping[str, Any]) -> str:
        data = _validate_event(kind, observation)
        raw_data = canonical_json(data)
        if len(raw_data) > MAX_EVENT_BYTES // 2:
            raise TraceError("Observation payload exceeds its byte bound")
        data = json.loads(raw_data)  # caller mutation cannot alter retained state
        with self._lock:
            if self._stream.closed:
                raise TraceError("Attempt is closed")
            if any(data[field] not in self._blobs for field in _BLOBS.get(kind, ()) if data[field] is not None):
                raise TraceError("Observation references missing artifact bytes")
            if kind == "finish" and data["outcome"] == "passed" and any(
                self.manifest[field] is not None and self.manifest[field] not in self._blobs
                for field in ("settings", "admission")
            ):
                raise TraceError("Completed attempt lacks retained configuration/admission references")
            event = {"sequence": self._sequence, "previous": self._previous,
                     "elapsed_ns": time.monotonic_ns() - self._started,
                     "observed_at": datetime.now(timezone.utc).isoformat(), "kind": kind, "data": data}
            event["event_id"] = identity(canonical_json(event))
            raw = canonical_json(event)
            limit = MAX_EVENTS if kind == "finish" else MAX_EVENTS - 1
            byte_limit = MAX_TRACE_BYTES if kind == "finish" else MAX_TRACE_BYTES - MAX_EVENT_BYTES
            if self._sequence >= limit or self._bytes + len(raw) > byte_limit:
                raise TraceError("Attempt exceeds its trace budget")
            self._state.accept(kind, data)
            self._stream.write(raw)
            self._stream.flush()
            os.fsync(self._stream.fileno())
            self._bytes += len(raw)
            self._sequence += 1
            self._previous = event["event_id"]
            if kind == "finish":
                self._stream.close()
            return event["event_id"]

    def finish(self, outcome: str, *, exception_type: str | None = None) -> str:
        return self.record("finish", {"outcome": outcome, "exception_type": exception_type})

    def close(self) -> None:
        """Preserve an interrupted attempt; closing cannot manufacture success."""
        if not self._stream.closed:
            self.finish("integration-failed")

    def __enter__(self):
        return self

    def __exit__(self, kind, _error, _traceback):
        try:
            if not self._stream.closed:
                outcome = "cancelled" if kind is KeyboardInterrupt else "failed" if kind else "integration-failed"
                self.finish(outcome, exception_type=kind.__name__ if kind else None)
        finally:
            self._stream.close()


def inspect_attempt(directory: Path, *, expected_manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Recount a bounded retained attempt without trusting its summary claims."""
    directory = Path(directory)
    if directory.is_symlink() or (directory / "blobs").is_symlink():
        raise TraceError("Trace storage cannot redirect reads")

    def read(path: Path, maximum: int) -> bytes:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
            raise TraceError("Missing, redirected, or oversized trace input")
        with path.open("rb") as stream:
            raw = stream.read(maximum + 1)
        if len(raw) > maximum:
            raise TraceError("Trace input grew beyond its bound")
        return raw

    raw_manifest = read(directory / "manifest.json", MAX_EVENT_BYTES)
    manifest = validate_manifest(json.loads(raw_manifest))
    if expected_manifest is not None and manifest != validate_manifest(expected_manifest):
        raise TraceError("Trace does not match the frozen scheduled attempt")
    if canonical_json(manifest) != raw_manifest:
        raise TraceError("Manifest is not canonical")
    state = _TraceState(manifest)
    previous = identity(raw_manifest)
    raw_events = read(directory / "events.jsonl", MAX_TRACE_BYTES)
    count, elapsed, retained = 0, 0, len(raw_manifest) + len(raw_events)
    checked_blobs: dict[str, int] = {}
    for path in (directory / "blobs").iterdir():
        if len(checked_blobs) >= MAX_EVENTS:
            raise TraceError("Artifact count exceeds its bound")
        key = "sha256:" + path.name
        _digest(key)
        raw_blob = read(path, MAX_BLOB_BYTES)
        if identity(raw_blob) != key:
            raise TraceError("Retained artifact changed")
        checked_blobs[key] = len(raw_blob)
        retained += len(raw_blob)
        if retained > MAX_TRACE_BYTES:
            raise TraceError("Retained trace exceeds its byte bound")
    referenced_blobs = {manifest[field] for field in ("settings", "admission") if manifest[field] is not None}
    source_paths = set()
    source_bytes = 0
    model_usage: dict[str, int | None] = {"input_tokens": 0, "output_tokens": 0}
    context_usage: dict[str, dict[str, Any]] = {}
    checks = []
    resources = []
    for raw in raw_events.splitlines(keepends=True):
        if len(raw) > MAX_EVENT_BYTES or count >= MAX_EVENTS:
            raise TraceError("Trace event bound exceeded")
        event = _object(json.loads(raw), {"sequence", "previous", "elapsed_ns", "observed_at", "kind", "data", "event_id"})
        if canonical_json(event) != raw or type(event["sequence"]) is not int or event["sequence"] != count or event["previous"] != previous:
            raise TraceError("Trace is truncated, reordered, or has missing events")
        expected = identity(canonical_json({k: v for k, v in event.items() if k != "event_id"}))
        if expected != event["event_id"]:
            raise TraceError("Observation bytes changed")
        _number(event["elapsed_ns"])
        if event["elapsed_ns"] < elapsed:
            raise TraceError("Observation time moved backwards")
        timestamp = datetime.fromisoformat(event["observed_at"])
        if timestamp.tzinfo is None:
            raise TraceError("Observation time lacks an explicit timezone")
        data = _validate_event(event["kind"], event["data"])
        for field in _BLOBS.get(event["kind"], ()):
            key = data[field]
            if key is None:
                continue
            if key not in checked_blobs:
                raise TraceError("Observation references missing artifact bytes")
            referenced_blobs.add(key)
        state.accept(event["kind"], data)
        if event["kind"] == "source-read":
            source_paths.add(data["path"])
            source_bytes += checked_blobs[data["blob"]]
        elif event["kind"] == "context":
            key = data["counter_id"] + ":" + data["counter_mode"]
            row = context_usage.setdefault(key, {"counter_id": data["counter_id"], "mode": data["counter_mode"],
                "emitted_bytes": 0, "canonical_tokens": 0, "host_framing_tokens": 0, "inclusions": 0})
            row["emitted_bytes"] += checked_blobs[data["blob"]]
            for field in ("canonical_tokens", "host_framing_tokens"):
                row[field] = None if row[field] is None or data[field] is None else row[field] + data[field]
        elif event["kind"] == "model-start":
            for context_id in data["context_ids"]:
                item = state.contexts[context_id]
                context_usage[item["counter_id"] + ":" + item["counter_mode"]]["inclusions"] += 1
        elif event["kind"] == "model-end":
            for field in model_usage:
                before = model_usage[field]
                model_usage[field] = None if before is None or data[field] is None else before + data[field]
        elif event["kind"] == "check-end":
            checks.append({key: data[key] for key in ("call_id", "exit_code", "compilation", "oracle")})
        elif event["kind"] == "resources":
            resources.append(data)
        count += 1
        elapsed, previous = event["elapsed_ns"], event["event_id"]
    if state.outcome == "passed" and not referenced_blobs <= checked_blobs.keys():
        raise TraceError("Completed attempt lacks its configuration/admission references")
    return {"attempt_id": manifest["attempt_id"], "outcome": state.outcome or "interrupted",
            "events": count, "last_event": previous, "pending_calls": sorted(state.pending),
            "retained_bytes": retained, "unreferenced_blobs": sorted(checked_blobs.keys() - referenced_blobs),
            "observations": dict(state.metrics), "oracle_outcomes": dict(state.oracle_outcomes),
            "work": {"unique_source_paths": len(source_paths), "source_read_bytes": source_bytes,
                     "contexts": list(context_usage.values()), "model_usage": model_usage,
                     "checks": checks, "resources": resources, "elapsed_ns": elapsed},
            "execution_kind": manifest["execution_kind"], "model_execution_established": False,
            "admission_independently_verified": False,
            "host_receipt": manifest["admission"], "bindings": manifest["bindings"]}


def inspect_campaign(directory: Path, *, expected_attempts: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Keep incomplete and damaged attempts in the campaign denominator."""
    schedule = {}
    if expected_attempts is not None:
        if not isinstance(expected_attempts, Mapping) or len(expected_attempts) > MAX_EVENTS:
            raise TraceError("Invalid bounded attempt schedule")
        for name, manifest in expected_attempts.items():
            _identifier(name)
            schedule[name] = validate_manifest(manifest)
    attempts = []
    retained = {path.name: path for path in Path(directory).iterdir()}
    if len(retained) > MAX_EVENTS:
        raise TraceError("Retained attempt count exceeds its bound")
    for name in sorted(retained.keys() | schedule.keys()):
        if name not in retained:
            attempts.append({"attempt_id": schedule[name]["attempt_id"], "outcome": "missing-evidence",
                             "error_type": "TraceError"})
            continue
        path = retained[name]
        if not path.is_dir() or path.is_symlink():
            raise TraceError("Campaign entries must be owned attempt directories")
        try:
            if expected_attempts is not None and name not in schedule:
                raise TraceError("Retained attempt is absent from the frozen schedule")
            result = inspect_attempt(path, expected_manifest=schedule.get(name))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            result = {"attempt_id": path.name, "outcome": "invalid-evidence", "error_type": type(exc).__name__}
        attempts.append(result)
    identities = [item["attempt_id"] for item in attempts]
    if len(identities) != len(set(identities)):
        raise TraceError("Duplicate attempt identity across retained directories")
    return {"attempts": attempts, "denominator": len(attempts),
            "outcomes": dict(Counter(item["outcome"] for item in attempts)),
            "analysis_outcomes": dict(Counter(
                "integration-failed" if item["outcome"] in {"interrupted", "invalid-evidence", "missing-evidence"} else item["outcome"]
                for item in attempts)),
            "schedule_supplied": expected_attempts is not None,
            "schedule_complete": expected_attempts is not None and all(item["outcome"] in OUTCOMES for item in attempts),
            "denominator_scope": "scheduled-and-retained" if expected_attempts is not None else "retained-only",
            "model_execution_established": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("attempt", "campaign"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--schedule", type=Path, help="Frozen directory-name to attempt-manifest mapping")
    args = parser.parse_args()
    schedule = None
    if args.schedule is not None:
        if args.kind != "campaign" or args.schedule.stat().st_size > MAX_BLOB_BYTES:
            parser.error("A bounded schedule is supported only for campaign inspection")
        with args.schedule.open("rb") as stream:
            raw = stream.read(MAX_BLOB_BYTES + 1)
        if len(raw) > MAX_BLOB_BYTES:
            raise TraceError("Attempt schedule exceeds its byte bound")

        def pairs(values):
            result = {}
            for key, value in values:
                if key in result:
                    raise TraceError("Duplicate schedule field")
                result[key] = value
            return result

        schedule = json.loads(raw, object_pairs_hook=pairs)
    result = inspect_attempt(args.directory) if args.kind == "attempt" else inspect_campaign(args.directory, expected_attempts=schedule)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
