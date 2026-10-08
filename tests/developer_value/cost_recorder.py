"""Prospective local authoring-cost observations, never reconstructed effort.

The SQLite ledger is insert-only, transactionally sequenced, hash chained and uses
FULL synchronous commits and a separately fsynced .head high-water commitment
(which must be archived with the database). Keep its directory on durable local storage. The hash
chain detects alteration, not an adversary who can rewrite the entire database;
retain/export its terminal hash in a separately owned evidence commitment.

Use ONE long-lived broker for separate shells/agents, with the project's absolute
``.venv/bin/python -m tests.developer_value.cost_recorder serve --db ... --socket ...``.
Send JSON operations with ``request --socket ... --json '{"operation":"start_span",
"arguments":{...}}'``. ``tool`` executes argv on the broker, retaining a safe label,
argv hash, exit/timeout outcomes and output byte/hash commitments, never output
text or credentials. Explicit labels must themselves be safe to retain.

Direct API: ``with CostRecorder(path, clock=callable) as recorder: ...``. A clock
returns ``(monotonic_ns, aware_UTC_ISO_timestamp)``. Each instance is a NEW clock
segment; reopening an active run interrupts its outstanding intervals/attempts
and records a missing restart gap. Never pretend reopening continues a clock.
Start a run with frozen source/prose identities and an explicit phase/category
scope. Optional ``controller_attempt_id``, ``controller_span_id``, ``controller_phase``
and ``controller_category`` together open an explicitly measured continuous
controller lifecycle at the run-start boundary. ``end_run`` closes it at the
same terminal boundary. This includes controller waiting/setup latency, never
exclusive active effort; child spans can categorize its work without additive
claims. Do not manually close that automatic controller span/attempt.
The default denominator is their Cartesian product; ``required_pairs``
can declare a sparse scope up front. Zero-work cells need an explicit reason via
``category_not_applicable``. Attempts and tools remain in the denominator even
when they fail. A completed terminal request is not proof of complete coverage:
``summary()['complete']`` additionally checks coverage, attempts, intervals and
all gaps. Pauses are spans and remain in elapsed/worker windows; active windows
exclude only spans explicitly categorized ``pause``. Reported spans measure
observed task latency, not active thinking or billed model time.

``complete`` denotes successful measured-scope completion; ``accounting_complete``
can also be true for a fully observed failed delivery. Receipt observation status
is always partial unless unavailable: no complete model-request scope is inferred.

Actual usage is unavailable by default. To accept a receipt, independently pin
its exact raw SHA-256 in ``trusted_receipt_sha256`` before recording it. Only the
strict ``developer-value-host-usage/v1`` receipt schema in ``record_usage`` is
accepted, with existing run/actor/task/attempt attribution. A pin is a trust
assertion by the evidence controller, not automatic host authentication.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
import fcntl
from hashlib import sha256
import json
import math
import os
import signal
from pathlib import Path
import socket
import socketserver
import sqlite3
import subprocess
import sys
import threading
import time
from typing import Any
from uuid import uuid4

SCHEMA = "developer-value-guide-cost-event/v1"
Clock = Callable[[], tuple[int, str]]
OUTCOMES = {"completed", "failed", "aborted", "interrupted", "timed-out"}
ZERO_HASH = "0" * 64
MAX_REQUEST_BYTES = 2 * 1024 * 1024


def canonical_json(value: Any) -> str:
    """UTF-8 canonical JSON used for exports and hash commitments."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_sha256(value: bytes) -> str:
    return sha256(value).hexdigest()


def system_clock() -> tuple[int, str]:
    return time.monotonic_ns(), datetime.now(timezone.utc).isoformat()


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be aware UTC")
    return parsed


def _identity(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty")
    return value


def _digest(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("expected lowercase SHA-256")
    return value


def _union(intervals: Sequence[tuple[int, int]]) -> int:
    total = 0
    right: int | None = None
    for start, end in sorted(intervals):
        if end < start:
            raise ValueError("invalid interval order")
        total += max(0, end - max(start, right if right is not None else start))
        right = max(end, right if right is not None else end)
    return total


class CostRecorder:
    """One writer/clock segment. Call methods through the broker for concurrency."""

    def __init__(self, path: str | Path, *, clock: Clock | None = None,
                 trusted_receipt_sha256: Sequence[str] = ()) -> None:
        trusted = frozenset(_digest(h) for h in trusted_receipt_sha256)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._head_path = self.path.with_suffix(self.path.suffix + ".head")
        self._lock_file = self.path.with_suffix(self.path.suffix + ".lock").open("a+b")
        try:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock_file.close()
            raise ValueError("ledger already has a live writer; use its broker") from None
        self._clock = clock or system_clock
        self._mutex = threading.RLock()
        self.trusted_receipt_sha256 = trusted
        self.clock_segment_id = str(uuid4())
        self._closed = False
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        try:
            self._db.execute("PRAGMA synchronous=FULL")
            self._db.execute("PRAGMA journal_mode=DELETE")
            self._db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL,
                    event_json TEXT NOT NULL, event_hash TEXT NOT NULL);
                CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'append-only ledger'); END;
                CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'append-only ledger'); END;
            """)
            previous = self.events()
            if previous:
                self._write_head(previous[-1])
            self._append("clock_segment_start", None, {})
            runs = {e["run_id"] for e in previous if e["event_kind"] == "run_start"}
            for run_id in sorted(runs):
                run_events = [e for e in previous if e["run_id"] == run_id]
                if any(e["event_kind"] == "run_end" for e in run_events):
                    continue
                for start in self._open_intervals(run_events).values():
                    self._append("interval_interrupted", run_id, {
                        **self._attribution(start), "span_id": start["span_id"],
                        "original_clock_segment_id": start["clock_segment_id"],
                        "outcome": "interrupted", "reason": "recorder restart; end boundary unavailable",
                    })
                for attempt in self._open_attempts(run_events).values():
                    self._append("attempt_end", run_id, {
                        **self._attribution(attempt), "outcome": "interrupted",
                        "reason": "recorder restart; previous attempt boundary unavailable",
                    })
                self.record_gap(run_id, reason="recorder restart: discontinuity since last retained boundary; duration unavailable")
        except BaseException as error:
            self._db.close()
            self._lock_file.close()
            if isinstance(error, sqlite3.DatabaseError):
                raise ValueError("corrupt SQLite ledger") from error
            raise

    def __enter__(self) -> CostRecorder:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        with self._mutex:
            if not self._closed:
                try:
                    try:
                        self._append("clock_segment_end", None, {})
                    except ValueError:
                        # Invalid clocks already have a retained diagnostic; close resources.
                        pass
                finally:
                    self._db.close()
                    self._lock_file.close()
                    self._closed = True

    @staticmethod
    def _attribution(event: Mapping[str, Any]) -> dict[str, Any]:
        return {k: event[k] for k in ("actor_id", "task_id", "attempt_id") if k in event}

    @staticmethod
    def _open_intervals(events: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        opened: dict[str, dict[str, Any]] = {}
        for event in events:
            kind = event["event_kind"]
            if kind in {"span_start", "tool_start"}:
                opened[event["span_id"]] = event
            elif kind in {"span_end", "tool_end", "interval_interrupted"}:
                opened.pop(event["span_id"], None)
        return opened

    @staticmethod
    def _open_attempts(events: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        opened: dict[str, dict[str, Any]] = {}
        for event in events:
            if event["event_kind"] == "attempt_start":
                opened[event["attempt_id"]] = event
            elif event["event_kind"] == "attempt_end":
                opened.pop(event["attempt_id"], None)
        return opened

    def events(self) -> list[dict[str, Any]]:
        """Read and verify every event without manufacturing observations."""
        with self._mutex:
            rows = list(self._db.execute(
                "SELECT sequence,event_id,event_json,event_hash FROM events ORDER BY sequence"))
            result = _verify_rows(rows)
            _verify_head(result, self._head_path)
            return result

    def _write_head(self, event: Mapping[str, Any]) -> None:
        # Independent durable high-water commitment detects a truncated DB prefix.
        temporary = self._head_path.with_name(self._head_path.name + "." + str(uuid4()) + ".tmp")
        with temporary.open("x") as handle:
            handle.write(canonical_json({"sequence": event["sequence"], "event_hash": event["event_hash"]}) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self._head_path)

    def _append(self, kind: str, run_id: str | None, fields: dict[str, Any],
                *, stamp: tuple[int, str] | None = None) -> dict[str, Any]:
        with self._mutex:
            if self._closed:
                raise ValueError("recorder closed")
            events = self.events()
            now_ns, now_wall = stamp or self._clock()
            _integer(now_ns, "monotonic_ns")
            wall = _utc(now_wall)
            current = [e for e in events if e["clock_segment_id"] == self.clock_segment_id]
            if current:
                previous = current[-1]
                delta_ns = now_ns - previous["monotonic_ns"]
                delta_wall = (wall - _utc(previous["timestamp_utc"])).total_seconds()
                if delta_ns < 0 or delta_wall < 0:
                    self._append("clock_error", run_id, {
                        "reason": "invalid clock order; rejected boundary unavailable",
                        "rejected_monotonic_ns": now_ns, "rejected_timestamp_utc": now_wall,
                    }, stamp=(previous["monotonic_ns"], previous["timestamp_utc"]))
                    raise ValueError("invalid clock order")
                if abs(delta_wall - delta_ns / 1e9) > 1:
                    fields = {**fields, "clock_discontinuity": {
                        "monotonic_delta_seconds": delta_ns / 1e9, "wall_delta_seconds": delta_wall,
                        "reason": "UTC and continuous monotonic clock differ by more than one second"}}

            event = {
                **fields, "schema_version": SCHEMA, "sequence": len(events) + 1,
                "event_id": str(uuid4()), "event_kind": kind, "run_id": run_id,
                "clock_segment_id": self.clock_segment_id, "monotonic_ns": now_ns,
                "timestamp_utc": now_wall, "previous_hash": events[-1]["event_hash"] if events else ZERO_HASH,
            }
            event["event_hash"] = content_sha256(canonical_json(event).encode())
            self._db.execute("BEGIN IMMEDIATE")
            try:
                self._db.execute("INSERT INTO events VALUES (?,?,?,?)", (
                    event["sequence"], event["event_id"], canonical_json(event), event["event_hash"]))
                self._db.execute("COMMIT")
                self._write_head(event)
                # fsync database and directory in addition to SQLite FULL durability.
                with self.path.open("rb") as handle:
                    os.fsync(handle.fileno())
                directory = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            except BaseException:
                if self._db.in_transaction:
                    self._db.execute("ROLLBACK")
                raise
            return event

    def _run(self, run_id: str, *, active: bool = True) -> list[dict[str, Any]]:
        result = [e for e in self.events() if e["run_id"] == run_id]
        if not result or result[0]["event_kind"] != "run_start":
            raise ValueError("unknown run")
        if active and any(e["event_kind"] == "run_end" for e in result):
            raise ValueError("run already terminal")
        return result

    def start_run(self, run_id: str, *, actor_id: str, task_id: str, phases: Sequence[str],
                  categories: Sequence[str], source_manifest_sha256: str,
                  prose_manifest_sha256: str, prior_work: str = "unavailable",
                  required_pairs: Sequence[Mapping[str, str]] | None = None,
                  controller_attempt_id: str | None = None,
                  controller_span_id: str | None = None,
                  controller_phase: str | None = None,
                  controller_category: str | None = None) -> dict[str, Any]:
        with self._mutex:
            _identity(run_id, "run_id")
            if any(e["run_id"] == run_id for e in self.events()):
                raise ValueError("duplicate run ID")
            for values, name in ((phases, "phase"), (categories, "category")):
                if not values or len(set(values)) != len(values):
                    raise ValueError(f"empty or duplicate {name} denominator")
                for value in values:
                    _identity(value, name)
            pairs = ([dict(p) for p in required_pairs] if required_pairs is not None else
                     [{"phase": p, "category": c} for p in phases for c in categories])
            if not pairs or any(set(p) != {"phase", "category"} or p["phase"] not in phases
                                or p["category"] not in categories for p in pairs):
                raise ValueError("invalid required phase/category denominator")
            if len({(p["phase"], p["category"]) for p in pairs}) != len(pairs):
                raise ValueError("duplicate required denominator pair")
            controller = (controller_attempt_id, controller_span_id, controller_phase, controller_category)
            if any(value is not None for value in controller):
                if not all(isinstance(value, str) and value for value in controller):
                    raise ValueError("controller scope needs attempt/span/phase/category together")
                if controller_phase not in phases or controller_category not in categories:
                    raise ValueError("controller scope outside declared phase/category")
            start = self._append("run_start", run_id, {
                "actor_id": _identity(actor_id, "actor_id"), "task_id": _identity(task_id, "task_id"),
                "phases": list(phases), "categories": list(categories), "required_pairs": pairs,
                "source_manifest_sha256": _digest(source_manifest_sha256),
                "prose_manifest_sha256": _digest(prose_manifest_sha256),
                "prior_work": _identity(prior_work, "prior_work"),
                "usage": {"status": "unavailable", "reason": "no attributable pinned host receipt"},
                "controller_scope": {"attempt_id": controller_attempt_id, "span_id": controller_span_id,
                                     "phase": controller_phase, "category": controller_category} if controller_attempt_id else None,
            })
            if controller_attempt_id is not None:
                stamp = (start["monotonic_ns"], start["timestamp_utc"])
                attribution = {"actor_id": actor_id, "task_id": task_id, "attempt_id": controller_attempt_id}
                self._append("attempt_start", run_id, {**attribution, "resumed_from": None,
                    "usage": {"status": "unavailable", "reason": "no attributable pinned host receipt"}}, stamp=stamp)
                self._append("span_start", run_id, {**attribution, "span_id": controller_span_id,
                    "phase": controller_phase, "category": controller_category, "parent_span_id": None,
                    "measurement_scope": "explicit continuous controller lifecycle latency; not exclusive active effort"}, stamp=stamp)
            return start

    def start_attempt(self, run_id: str, attempt_id: str, *, actor_id: str, task_id: str,
                      resumed_from: str | None = None) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            _identity(attempt_id, "attempt_id")
            if any(e.get("attempt_id") == attempt_id for e in events):
                raise ValueError("duplicate attempt ID")
            if resumed_from is not None:
                previous = [e for e in events if e["event_kind"] == "attempt_end" and e["attempt_id"] == resumed_from]
                if not previous or previous[-1]["outcome"] == "completed":
                    raise ValueError("resume must reference a failed/aborted/interrupted attempt")
            return self._append("attempt_start", run_id, {
                "actor_id": _identity(actor_id, "actor_id"), "task_id": _identity(task_id, "task_id"),
                "attempt_id": attempt_id, "resumed_from": resumed_from,
                "usage": {"status": "unavailable", "reason": "no attributable pinned host receipt"},
            })

    def _attempt(self, events: Sequence[dict[str, Any]], attempt_id: str,
                 actor_id: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        opened = self._open_attempts(events)
        if attempt_id not in opened:
            raise ValueError("attempt missing or already terminal")
        attempt = opened[attempt_id]
        if actor_id is not None and (attempt["actor_id"] != actor_id or attempt["task_id"] != task_id):
            raise ValueError("attempt attribution differs")
        return attempt

    def end_attempt(self, run_id: str, attempt_id: str, *, outcome: str) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            attempt = self._attempt(events, attempt_id)
            controller = events[0].get("controller_scope")
            if controller and controller["attempt_id"] == attempt_id:
                raise ValueError("automatic controller attempt closes only through end_run")
            if any(e["attempt_id"] == attempt_id for e in self._open_intervals(events).values()):
                raise ValueError("attempt contains unclosed interval")
            return self._append("attempt_end", run_id, {**self._attribution(attempt), "outcome": _outcome(outcome)})

    def _start_interval(self, kind: str, run_id: str, span_id: str, *, actor_id: str,
                        task_id: str, attempt_id: str, phase: str, category: str,
                        parent_span_id: str | None = None, **extra: Any) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            self._attempt(events, attempt_id, actor_id, task_id)
            _identity(span_id, "span_id")
            if any(e.get("span_id") == span_id for e in events):
                raise ValueError("duplicate span ID")
            if phase not in events[0]["phases"] or category not in events[0]["categories"]:
                raise ValueError("phase/category outside declared scope")
            if any(e["event_kind"] == "category_not_applicable" and e["phase"] == phase and e["category"] == category for e in events):
                raise ValueError("category was declared not applicable")
            opened = self._open_intervals(events)
            if parent_span_id is not None:
                if parent_span_id not in opened or opened[parent_span_id]["event_kind"] != "span_start":
                    raise ValueError("parent span missing or closed")
            return self._append(kind, run_id, {
                "actor_id": actor_id, "task_id": task_id, "attempt_id": attempt_id,
                "span_id": span_id, "phase": phase, "category": category,
                "parent_span_id": parent_span_id, **extra,
            })

    def start_span(self, run_id: str, span_id: str, *, actor_id: str, task_id: str,
                   attempt_id: str, phase: str, category: str,
                   parent_span_id: str | None = None) -> dict[str, Any]:
        return self._start_interval("span_start", run_id, span_id, actor_id=actor_id,
                                    task_id=task_id, attempt_id=attempt_id, phase=phase,
                                    category=category, parent_span_id=parent_span_id)

    def start_tool(self, run_id: str, span_id: str, *, actor_id: str, task_id: str,
                   attempt_id: str, phase: str, category: str, command_label: str,
                   command_sha256: str, parent_span_id: str | None = None,
                   redaction_reason: str = "argv omitted; safe operation label and hash only") -> dict[str, Any]:
        return self._start_interval("tool_start", run_id, span_id, actor_id=actor_id,
                                    task_id=task_id, attempt_id=attempt_id, phase=phase,
                                    category=category, parent_span_id=parent_span_id,
                                    tool={"command_or_operation": _identity(command_label, "command_label"),
                                          "command_sha256": _digest(command_sha256)},
                                    gap_or_redaction_reason=_identity(redaction_reason, "redaction_reason"))

    def _end_interval(self, kind: str, run_id: str, span_id: str, outcome: str,
                      *, stamp: tuple[int, str] | None = None, **extra: Any) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            start = self._open_intervals(events).get(span_id)
            if start is None or start["event_kind"] != kind.replace("end", "start"):
                raise ValueError("interval start missing or already closed")
            if any(e.get("parent_span_id") == span_id for e in self._open_intervals(events).values()):
                raise ValueError("parent contains unclosed child interval")
            return self._append(kind, run_id, {
                **self._attribution(start), "span_id": span_id, "phase": start["phase"],
                "category": start["category"], "parent_span_id": start["parent_span_id"],
                "outcome": _outcome(outcome), **extra,
            }, stamp=stamp)

    def end_span(self, run_id: str, span_id: str, *, outcome: str = "completed") -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            controller = events[0].get("controller_scope")
            if controller and controller["span_id"] == span_id:
                raise ValueError("automatic controller span closes only through end_run")
            return self._end_interval("span_end", run_id, span_id, outcome)

    def end_tool(self, run_id: str, span_id: str, *, exit_code: int | None,
                 stdout_sha256: str, stderr_sha256: str, stdout_bytes: int,
                 stderr_bytes: int, outcome: str | None = None,
                 _stamp: tuple[int, str] | None = None) -> dict[str, Any]:
        if exit_code is not None and (isinstance(exit_code, bool) or not isinstance(exit_code, int)):
            raise ValueError("invalid exit code")
        selected = outcome or ("completed" if exit_code == 0 else "failed")
        if selected == "completed" and exit_code != 0:
            raise ValueError("completed tool must have zero exit")
        return self._end_interval("tool_end", run_id, span_id, selected, stamp=_stamp, tool={
            "exit_code": exit_code, "outcome": selected,
            "stdout_sha256": _digest(stdout_sha256), "stderr_sha256": _digest(stderr_sha256),
            "stdout_bytes": _integer(stdout_bytes, "stdout_bytes"),
            "stderr_bytes": _integer(stderr_bytes, "stderr_bytes"),
        })

    def record_artifact(self, run_id: str, *, actor_id: str, task_id: str,
                        attempt_id: str, path: str, content: bytes,
                        estimate_tokens: bool = False) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            self._attempt(events, attempt_id, actor_id, task_id)
            return self._append("artifact_snapshot", run_id, {
                "actor_id": actor_id, "task_id": task_id, "attempt_id": attempt_id,
                "artifact": {"path": _identity(path, "path"), "sha256": content_sha256(content), "bytes": len(content)},
                "estimated_content_tokens": {"status": "estimated" if estimate_tokens else "not-computed",
                    "method": "ceil(UTF8_bytes/4); content estimate only, not actual model usage",
                    "value": math.ceil(len(content) / 4) if estimate_tokens else None},
            })

    def record_review(self, run_id: str, *, actor_id: str, task_id: str, attempt_id: str,
                      review_id: str, outcome: str, artifact_sha256: str,
                      defects: Sequence[str]) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            self._attempt(events, attempt_id, actor_id, task_id)
            if any(e.get("review_id") == review_id for e in events):
                raise ValueError("duplicate review ID")
            return self._append("review_result", run_id, {
                "actor_id": actor_id, "task_id": task_id, "attempt_id": attempt_id,
                "review_id": _identity(review_id, "review_id"), "outcome": _identity(outcome, "outcome"),
                "artifact_sha256": _digest(artifact_sha256), "defects": list(defects),
            })

    def record_gap(self, run_id: str, *, reason: str, actor_id: str = "controller",
                   task_id: str = "coverage", attempt_id: str | None = None) -> dict[str, Any]:
        with self._mutex:
            self._run(run_id)
            return self._append("gap", run_id, {
                "actor_id": _identity(actor_id, "actor_id"), "task_id": _identity(task_id, "task_id"),
                "attempt_id": attempt_id, "reason": _identity(reason, "reason"), "gap_or_redaction_reason": reason,
                "duration_seconds": None, "coverage": "unavailable",
            })

    def category_not_applicable(self, run_id: str, *, phase: str, category: str,
                                reason: str) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            if {"phase": phase, "category": category} not in events[0]["required_pairs"]:
                raise ValueError("category outside declared denominator")
            if any(e.get("phase") == phase and e.get("category") == category for e in events[1:]):
                raise ValueError("category already observed or excluded")
            return self._append("category_not_applicable", run_id, {
                "phase": phase, "category": category, "reason": _identity(reason, "reason")})

    def record_usage(self, run_id: str, *, receipt_path: str | Path) -> dict[str, Any]:
        """Accept ONLY a pinned exact host receipt, never inline token estimates.

        Strict keys: schema_version='developer-value-host-usage/v1', status='actual',
        attribution={run_id,actor_id,task_id,attempt_id}, host_receipt_id, provider,
        input_tokens, output_tokens, cached_tokens, reasoning_tokens,
        monetary_cost, currency. Optional usage measures are explicitly null.
        """
        with self._mutex:
            events = self._run(run_id)
            raw = Path(receipt_path).read_bytes()
            digest = content_sha256(raw)
            if digest not in self.trusted_receipt_sha256:
                raise ValueError("receipt is not explicitly pinned as trusted")
            receipt = json.loads(raw)
            keys = {"schema_version", "status", "attribution", "host_receipt_id", "provider",
                    "input_tokens", "output_tokens", "cached_tokens", "reasoning_tokens", "monetary_cost", "currency"}
            if set(receipt) != keys or receipt["schema_version"] != "developer-value-host-usage/v1" or receipt["status"] != "actual":
                raise ValueError("invalid actual host receipt schema; estimates are prohibited")
            attribution = receipt["attribution"]
            if set(attribution) != {"run_id", "actor_id", "task_id", "attempt_id"} or attribution["run_id"] != run_id:
                raise ValueError("invalid receipt attribution")
            attempts = [e for e in events if e["event_kind"] == "attempt_start" and e["attempt_id"] == attribution["attempt_id"]]
            if not attempts or any(attempts[0][key] != attribution[key] for key in ("actor_id", "task_id")):
                raise ValueError("receipt attribution does not match a recorded attempt")
            for key in ("input_tokens", "output_tokens", "cached_tokens", "reasoning_tokens"):
                if receipt[key] is not None or key in {"input_tokens", "output_tokens"}:
                    _integer(receipt[key], key)
            cost = receipt["monetary_cost"]
            if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0):
                raise ValueError("invalid monetary cost")
            if (cost is None) != (receipt["currency"] is None):
                raise ValueError("currency and monetary cost must be available together")
            _identity(receipt["host_receipt_id"], "host_receipt_id")
            _identity(receipt["provider"], "provider")
            if receipt["currency"] is not None:
                _identity(receipt["currency"], "currency")
            if any(e["event_kind"] == "usage_record" and (
                    e["usage"]["receipt_sha256"] == digest or
                    (e["usage"]["provider"], e["usage"]["host_receipt_id"]) == (receipt["provider"], receipt["host_receipt_id"])) for e in self.events()):
                raise ValueError("duplicate host receipt")
            return self._append("usage_record", run_id, {
                **{key: attribution[key] for key in ("actor_id", "task_id", "attempt_id")},
                "usage": {**receipt, "receipt_sha256": digest, "record_reference": str(receipt_path),
                          "trust_basis": "controller explicitly pinned exact raw host receipt SHA-256"}})

    def end_run(self, run_id: str, *, outcome: str) -> dict[str, Any]:
        with self._mutex:
            events = self._run(run_id)
            selected = _outcome(outcome)
            controller = events[0].get("controller_scope")
            stamp = self._clock()
            if controller is not None:
                span_id = controller["span_id"]
                start = self._open_intervals(events).get(span_id)
                if start is None:
                    if not any(e["event_kind"] == "interval_interrupted" and e["span_id"] == span_id for e in events):
                        raise ValueError("automatic controller scope missing or manually closed")
                    # Restart already interrupted that scope/attempt; retain a terminal
                    # record without inventing their unavailable original end boundary.
                else:
                    self._end_interval("span_end", run_id, span_id, selected, stamp=stamp)
                    self._append("attempt_end", run_id, {**self._attribution(start), "outcome": selected}, stamp=stamp)
            return self._append("run_end", run_id, {"outcome": selected}, stamp=stamp)

    def summary(self, run_id: str) -> dict[str, Any]:
        """Return the full declared denominator; incomplete observations never pass."""
        with self._mutex:
            events = self._run(run_id, active=False)
            errors: list[str] = []
            terminal = [e for e in events if e["event_kind"] == "run_end"]
            if len(terminal) != 1:
                errors.append("terminal run record absent")
            opened = self._open_intervals(events)
            if opened:
                errors.append("unclosed intervals: " + ",".join(sorted(opened)))
            open_attempts = self._open_attempts(events)
            if open_attempts:
                errors.append("unclosed attempts: " + ",".join(sorted(open_attempts)))
            interrupted = [e for e in events if e["event_kind"] == "interval_interrupted"]
            if interrupted:
                errors.append("interrupted intervals have unavailable end boundaries")
            gaps = [e for e in events if e["event_kind"] == "gap"]
            if gaps:
                errors.append("explicit unavailable coverage gaps")
            if any(e["event_kind"] == "clock_error" or "clock_discontinuity" in e for e in events):
                errors.append("invalid clock order or UTC discontinuity")
            starts = {e["span_id"]: e for e in events if e["event_kind"] in {"span_start", "tool_start"}}
            closed: list[tuple[dict[str, Any], dict[str, Any]]] = []
            for end in events:
                if end["event_kind"] in {"span_end", "tool_end"}:
                    start = starts.get(end["span_id"])
                    if start is None or start["clock_segment_id"] != end["clock_segment_id"] or end["monotonic_ns"] < start["monotonic_ns"]:
                        errors.append("missing start or invalid interval clock order")
                    else:
                        closed.append((start, end))
            workers: dict[str, dict[str, list[tuple[int, int]]]] = defaultdict(lambda: defaultdict(list))
            windows: dict[str, list[tuple[int, int]]] = defaultdict(list)
            active_windows: dict[str, list[tuple[int, int]]] = defaultdict(list)
            tool_seconds = 0.0
            for start, end in closed:
                interval = (start["monotonic_ns"], end["monotonic_ns"])
                segment = start["clock_segment_id"]
                seconds = (interval[1] - interval[0]) / 1e9
                if start["event_kind"] == "tool_start":
                    tool_seconds += seconds
                else:
                    workers[start["actor_id"]][segment].append(interval)
                    windows[segment].append(interval)
                    if start["category"] != "pause":
                        active_windows[segment].append(interval)
            overlaps: list[dict[str, Any]] = []
            worker_pairs = [(s, e) for s, e in closed if s["event_kind"] == "span_start"]
            for index, (start, end) in enumerate(worker_pairs):
                ancestors: set[str] = set()
                parent = start.get("parent_span_id")
                while parent is not None:
                    if parent in ancestors or parent not in starts:
                        errors.append("invalid parent chain")
                        break
                    ancestors.add(parent)
                    parent = starts[parent].get("parent_span_id")
                for other_start, other_end in worker_pairs[index + 1:]:
                    if start["actor_id"] != other_start["actor_id"] or start["clock_segment_id"] != other_start["clock_segment_id"]:
                        continue
                    left = max(start["monotonic_ns"], other_start["monotonic_ns"])
                    right = min(end["monotonic_ns"], other_end["monotonic_ns"])
                    if left >= right:
                        continue
                    nested = other_start["span_id"] in ancestors
                    other_parent = other_start.get("parent_span_id")
                    while other_parent is not None and other_parent in starts:
                        if other_parent == start["span_id"]:
                            nested = True
                        other_parent = starts[other_parent].get("parent_span_id")
                    ambiguous = not nested and (start["phase"], start["category"]) != (other_start["phase"], other_start["category"])
                    overlaps.append({"actor_id": start["actor_id"], "span_ids": [start["span_id"], other_start["span_id"]],
                                     "seconds": (right - left) / 1e9, "nested": nested, "ambiguous_attribution": ambiguous})
                    if ambiguous:
                        errors.append("overlapping unparented worker phase/category attribution")
            per_actor = {actor: sum(_union(i) for i in segments.values()) / 1e9 for actor, segments in workers.items()}
            pauses: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
            for start, end in worker_pairs:
                if start["category"] == "pause":
                    pauses[start["actor_id"], start["clock_segment_id"]].append((start["monotonic_ns"], end["monotonic_ns"]))
            active_windows.clear()
            per_actor_active: dict[str, float] = {}
            for actor, segments in workers.items():
                actor_active = 0
                for segment, intervals in segments.items():
                    remaining = _subtract(intervals, pauses.get((actor, segment), []))
                    active_windows[segment].extend(remaining)
                    actor_active += _union(remaining)
                per_actor_active[actor] = actor_active / 1e9
            observed_interrupted: list[dict[str, Any]] = []
            lower_bound_windows = {segment: list(intervals) for segment, intervals in windows.items()}
            lower_bound_workers = {actor: {segment: list(intervals) for segment, intervals in segments.items()} for actor, segments in workers.items()}
            for marker in interrupted:
                start = starts[marker["span_id"]]
                observations = [e for e in events if e["clock_segment_id"] == start["clock_segment_id"]]
                known_end = max(e["monotonic_ns"] for e in observations)
                seconds = max(0, known_end - start["monotonic_ns"]) / 1e9
                observed_interrupted.append({**marker, "known_lower_bound_seconds": seconds,
                    "last_observed_monotonic_ns": known_end,
                    "unobserved_tail_seconds": None, "duration_seconds": None})
                if start["event_kind"] == "span_start":
                    lower_bound_windows.setdefault(start["clock_segment_id"], []).append((start["monotonic_ns"], known_end))
                    lower_bound_workers.setdefault(start["actor_id"], {}).setdefault(start["clock_segment_id"], []).append((start["monotonic_ns"], known_end))
            missing_denominator: list[dict[str, str]] = []
            denominator: list[dict[str, Any]] = []
            for pair in events[0]["required_pairs"]:
                matching = [(s, e) for s, e in closed if s["phase"] == pair["phase"] and s["category"] == pair["category"]]
                exclusions = [e for e in events if e["event_kind"] == "category_not_applicable" and e["phase"] == pair["phase"] and e["category"] == pair["category"]]
                if not matching and not exclusions:
                    missing_denominator.append(pair)
                denominator.append({**pair, "span_count": len(matching),
                    "outcomes": dict(Counter(e["outcome"] for _, e in matching)),
                    "worker_seconds": _worker_union_seconds(matching),
                    "raw_worker_seconds": sum((e["monotonic_ns"] - s["monotonic_ns"]) / 1e9 for s, e in matching if s["event_kind"] == "span_start"),
                    "tool_seconds": sum((e["monotonic_ns"] - s["monotonic_ns"]) / 1e9 for s, e in matching if s["event_kind"] == "tool_start"),
                    "not_applicable_reason": exclusions[0]["reason"] if exclusions else None})
            if missing_denominator:
                errors.append("missing declared phase/category observations")
            missing_intervals: list[dict[str, Any]] = []
            by_segment: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for event in events:
                by_segment[event["clock_segment_id"]].append(event)
            for segment, observations in by_segment.items():
                left = observations[0]["monotonic_ns"]
                right = observations[-1]["monotonic_ns"]
                cursor = left
                for start, end in sorted(windows.get(segment, [])):
                    if start > cursor:
                        missing_intervals.append({"clock_segment_id": segment, "start_ns": cursor,
                            "end_ns": start, "seconds": (start - cursor) / 1e9})
                    cursor = max(cursor, end)
                if cursor < right:
                    missing_intervals.append({"clock_segment_id": segment, "start_ns": cursor,
                        "end_ns": right, "seconds": (right - cursor) / 1e9})
            if missing_intervals:
                errors.append("unobserved intervals between task boundaries")
            attempts = [e for e in events if e["event_kind"] in {"attempt_start", "attempt_end"}]
            attempt_starts = [e for e in attempts if e["event_kind"] == "attempt_start"]
            if not attempt_starts:
                errors.append("no declared attempts")
            usages = [e["usage"] for e in events if e["event_kind"] == "usage_record"]
            receipted_attempts = {e["attempt_id"] for e in events if e["event_kind"] == "usage_record"}
            wall_seconds = (_utc(events[-1]["timestamp_utc"]) - _utc(events[0]["timestamp_utc"])).total_seconds()
            if wall_seconds < 0:
                errors.append("wall clock discontinuity: negative total")
            return {
                "schema_version": "developer-value-guide-cost-summary/v1", "run_id": run_id,
                "complete": not errors and bool(terminal) and terminal[0]["outcome"] == "completed", "accounting_complete": not errors,
                "successful_delivery": not errors and bool(terminal) and terminal[0]["outcome"] == "completed", "outcome": terminal[0]["outcome"] if terminal else "unavailable",
                "errors": errors, "gaps": gaps, "missing_intervals": missing_intervals,
                "missing_denominator": missing_denominator, "denominator": denominator,
                "elapsed_wall_seconds": wall_seconds, "critical_path_seconds": sum(_union(i) for i in windows.values()) / 1e9,
                "active_window_seconds": sum(_union(i) for i in active_windows.values()) / 1e9,
                "per_actor_active_seconds": per_actor_active,
                "critical_path_lower_bound_seconds": sum(_union(i) for i in lower_bound_windows.values()) / 1e9,
                "worker_lower_bound_seconds": sum(_union(i) for segments in lower_bound_workers.values() for i in segments.values()) / 1e9,
                "worker_seconds": sum(per_actor.values()), "per_actor_seconds": per_actor,
                "tool_seconds": tool_seconds, "clock_segments": list(by_segment), "overlaps": overlaps,
                "category_seconds_are_nonadditive": True,
                "unattributed_controller_overhead_seconds": sum(i["seconds"] for i in missing_intervals),
                "attempts": attempts, "interrupted_intervals": observed_interrupted,
                "clock_discontinuities": [e for e in events if e["event_kind"] == "clock_error" or "clock_discontinuity" in e],
                "invocation_outcomes": [e for e in events if e["event_kind"] == "tool_end"],
                "reviews": [e for e in events if e["event_kind"] == "review_result"],
                "artifacts": [e for e in events if e["event_kind"] == "artifact_snapshot"],
                "actual_usage": {"status": "partial" if usages else "unavailable",
                    "reason": "only exact pinned attributable host receipts; content estimates excluded",
                    "coverage": {"attempts": len(attempt_starts), "receipted_attempts": len(receipted_attempts)}, "receipts": usages,
                    "request_scope_coverage": {"status": "unavailable", "reason": "no frozen complete model-request denominator; attempt receipt presence is not complete usage coverage"},
                    "monetary_coverage": "unavailable" if not usages or any(u["monetary_cost"] is None for u in usages) else "receipted-subset"},
                "terminal_hash": events[-1]["event_hash"], "prior_work": events[0]["prior_work"],
                "declared_scope": {key: events[0][key] for key in ("phases", "categories", "required_pairs")},
            }

    def export_jsonl(self, path: str | Path) -> dict[str, Any]:
        """Create a new durable canonical JSONL export; never overwrite evidence."""
        with self._mutex:
            events = self.events()
            data = "".join(canonical_json(e) + "\n" for e in events).encode()
            destination = Path(path)
            with destination.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            directory = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return {"path": str(destination), "bytes": len(data), "sha256": content_sha256(data), "events": len(events)}

    def run_tool(self, *, argv: Sequence[str], timeout: float = 300, **arguments: Any) -> dict[str, Any]:
        """Execute a bounded argv locally with broker-owned start/end boundaries.

        No shell, external service, credential text or transcript is logged. The
        caller owns argv safety and environment. Output bytes remain hashes/counts.
        Spawn failure and timeout are durable tool outcomes, not discarded retries.
        Tools run in a fresh POSIX session; timeout/interruption kills the entire
        process group before retaining the end boundary. A descendant deliberately
        escaping that group is outside this owned-tool containment contract.
        """
        if not argv or any(not isinstance(value, str) for value in argv):
            raise ValueError("argv must be a nonempty string array")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        run_id = arguments.pop("run_id")
        span_id = arguments.pop("span_id")
        arguments["command_sha256"] = content_sha256(canonical_json(list(argv)).encode())
        self.start_tool(run_id, span_id, **arguments)
        outcome = "failed"
        exit_code: int | None = None
        stdout = stderr = b""
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(list(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                outcome = "completed" if exit_code == 0 else "failed"
            except subprocess.TimeoutExpired:
                _kill_tool_group(process)
                stdout, stderr = process.communicate(timeout=5)
                exit_code = process.returncode
                outcome = "timed-out"
        except subprocess.TimeoutExpired as error:
            # A descendant that deliberately escapes its process group is outside
            # ordinary tool containment; retain incomplete output, never completion.
            stdout, stderr = error.stdout or b"", error.stderr or b""
            outcome = "interrupted"
            if process is not None:
                _kill_tool_group(process)
                process.wait(timeout=5)
        except OSError as error:
            # Avoid paths/argv in retained exception messages.
            stderr = ("spawn failed: " + type(error).__name__).encode()
        except BaseException:
            if process is not None:
                _kill_tool_group(process)
                process.wait(timeout=5)
            self.end_tool(run_id, span_id, exit_code=None, stdout_sha256=content_sha256(stdout),
                          stderr_sha256=content_sha256(stderr), stdout_bytes=len(stdout), stderr_bytes=len(stderr), outcome="interrupted")
            raise
        with self._mutex:
            stamp = self._clock()  # Boundary before output hashing/durable commit.
            return self.end_tool(run_id, span_id, exit_code=exit_code,
                stdout_sha256=content_sha256(stdout), stderr_sha256=content_sha256(stderr),
                stdout_bytes=len(stdout), stderr_bytes=len(stderr), outcome=outcome, _stamp=stamp)


def _kill_tool_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate ordinary POSIX descendants as well as the direct tool child."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _subtract(intervals: Sequence[tuple[int, int]], pauses: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """Subtract pauses from each actor's windows before computing global unions."""
    remaining = list(intervals)
    for left, right in pauses:
        updated: list[tuple[int, int]] = []
        for start, end in remaining:
            if right <= start or left >= end:
                updated.append((start, end))
            else:
                if start < left:
                    updated.append((start, left))
                if end > right:
                    updated.append((right, end))
        remaining = updated
    return remaining


def _worker_union_seconds(pairs: Sequence[tuple[dict[str, Any], dict[str, Any]]]) -> float:
    grouped: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for start, end in pairs:
        if start["event_kind"] == "span_start":
            grouped[start["actor_id"], start["clock_segment_id"]].append((start["monotonic_ns"], end["monotonic_ns"]))
    return sum(_union(intervals) for intervals in grouped.values()) / 1e9


def _verify_rows(rows: Sequence[tuple[Any, ...]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    previous_hash = ZERO_HASH
    clocks: dict[str, tuple[int, datetime]] = {}
    ids: set[str] = set()
    try:
        for position, row in enumerate(rows, 1):
            sequence, event_id, event_json, event_hash = row
            event = json.loads(event_json)
            if (sequence != position or event["sequence"] != sequence or event["event_id"] != event_id
                    or event_id in ids or event["schema_version"] != SCHEMA):
                raise ValueError("ledger duplicate ID or missing/altered sequence/schema")
            ids.add(event_id)
            payload = dict(event)
            stored_hash = payload.pop("event_hash")
            if (stored_hash != event_hash or content_sha256(canonical_json(payload).encode()) != event_hash
                    or event["previous_hash"] != previous_hash or canonical_json(event) != event_json):
                raise ValueError("ledger hash chain/canonical bytes altered")
            stamp = (_integer(event["monotonic_ns"], "monotonic_ns"), _utc(event["timestamp_utc"]))
            segment = event["clock_segment_id"]
            if segment in clocks and (stamp[0] < clocks[segment][0] or stamp[1] < clocks[segment][1]):
                raise ValueError("invalid clock order")
            if segment not in clocks and event["event_kind"] != "clock_segment_start":
                raise ValueError("clock segment start missing")
            clocks[segment] = stamp
            previous_hash = event_hash
            result.append(event)
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("malformed event ledger") from error
    return result


def _verify_head(events: Sequence[dict[str, Any]], head_path: Path, *, captured: bytes | None = None) -> None:
    if not events:
        if head_path.exists():
            raise ValueError("ledger truncated below retained head")
        return
    if not head_path.exists():
        raise ValueError("durable ledger head is missing")
    try:
        head = json.loads(captured if captured is not None else head_path.read_bytes())
        position = _integer(head["sequence"], "head sequence")
        if position < 1 or position > len(events) or events[position - 1]["event_hash"] != head["event_hash"]:
            raise ValueError("ledger truncated or differs from retained head")
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("malformed ledger head") from error
    # A complete SQLite transaction may precede its head replace on interruption.
    # Accept only a verified extension of that exact checkpoint, never a shorter DB.


def read_events(path: str | Path) -> list[dict[str, Any]]:
    """Pure read of SQLite events, including while the broker owns the writer.

    Does not create a new segment or acquire a writer lock. The database and its
    sibling .head are one durable ledger; archive both with canonical exports.
    """
    target = Path(path)
    try:
        connection = sqlite3.connect(target.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            head_path = target.with_suffix(target.suffix + ".head")
            checkpoint = head_path.read_bytes() if head_path.exists() else None
            connection.execute("BEGIN")
            rows = list(connection.execute("SELECT sequence,event_id,event_json,event_hash FROM events ORDER BY sequence"))
            events = _verify_rows(rows)
            _verify_head(events, head_path, captured=checkpoint)
            return events
        finally:
            connection.close()
    except sqlite3.DatabaseError as error:
        raise ValueError("corrupt or unreadable SQLite ledger") from error


def validate_export(path: str | Path, *, expected_terminal_hash: str | None = None,
                    require_terminal: bool = False) -> dict[str, Any]:
    """Pure canonical JSONL integrity check; optionally bind an external head.

    A chain alone cannot detect removing its complete suffix. Supply the previously
    retained expected_terminal_hash to detect such truncation. require_terminal
    additionally rejects any run without a terminal record (even a failed terminal
    is a valid completed accounting observation).
    """
    raw = Path(path).read_bytes()
    if not raw or not raw.endswith(b"\n"):
        raise ValueError("empty or truncated export")
    rows: list[tuple[Any, ...]] = []
    try:
        for line in raw.decode("utf-8").splitlines():
            event = json.loads(line)
            rows.append((event["sequence"], event["event_id"], line, event["event_hash"]))
    except (UnicodeError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("malformed or truncated export") from error
    events = _verify_rows(rows)
    if expected_terminal_hash is not None and events[-1]["event_hash"] != _digest(expected_terminal_hash):
        raise ValueError("export differs from retained terminal hash")
    if require_terminal:
        runs = {e["run_id"] for e in events if e["event_kind"] == "run_start"}
        for run_id in runs:
            if len([e for e in events if e["run_id"] == run_id and e["event_kind"] == "run_end"]) != 1:
                raise ValueError("terminal run record absent")
    return {"valid": True, "events": len(events), "terminal_hash": events[-1]["event_hash"], "sha256": content_sha256(raw)}


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _outcome(value: str) -> str:
    if value not in OUTCOMES:
        raise ValueError("invalid terminal outcome")
    return value


OPERATIONS = frozenset({"start_run", "end_run", "start_attempt", "end_attempt", "start_span", "end_span",
                       "start_tool", "end_tool", "record_artifact", "record_review", "record_gap", "record_usage",
                       "category_not_applicable", "summary", "events", "export_jsonl", "run_tool", "shutdown"})


def request(socket_path: str | Path, operation: str, **arguments: Any) -> Any:
    """One newline-delimited JSON request; broker errors raise ValueError."""
    payload = (canonical_json({"operation": operation, "arguments": arguments}) + "\n").encode()
    if len(payload) > MAX_REQUEST_BYTES:
        raise ValueError("request too large")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(str(socket_path))
        client.sendall(payload)
        with client.makefile("rb") as stream:
            response = json.loads(stream.readline())
    if not response["ok"]:
        raise ValueError(response["error"])
    return response["result"]


def serve(db_path: str | Path, socket_path: str | Path, *,
          trusted_receipt_sha256: Sequence[str] = ()) -> None:
    """Run a local 0600 Unix socket broker until interrupted.

    An existing socket is never silently removed: after verifying its previous
    process exited, explicitly remove a stale socket and restart. Ledger locking
    prevents a second writer. Broker restart records an honest discontinuity.
    """
    destination = Path(socket_path)
    if destination.exists():
        raise ValueError("socket already exists; verify/remove stale socket explicitly")
    with CostRecorder(db_path, trusted_receipt_sha256=trusted_receipt_sha256) as recorder:
        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                try:
                    raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
                    if len(raw) > MAX_REQUEST_BYTES or not raw.endswith(b"\n"):
                        raise ValueError("oversized or incomplete request")
                    packet = json.loads(raw)
                    if set(packet) != {"operation", "arguments"} or packet["operation"] not in OPERATIONS or not isinstance(packet["arguments"], dict):
                        raise ValueError("invalid request operation")
                    args = dict(packet["arguments"])
                    if any(k.startswith("_") for k in args):
                        raise ValueError("private arguments prohibited")
                    if packet["operation"] == "record_artifact":
                        # JSON callers provide text explicitly or a local file path.
                        if "content_text" in args:
                            args["content"] = args.pop("content_text").encode()
                        elif "content_path" in args:
                            args["content"] = Path(args.pop("content_path")).read_bytes()
                        else:
                            raise ValueError("artifact needs content_text or content_path")
                    if packet["operation"] == "shutdown":
                        if args:
                            raise ValueError("shutdown takes no arguments")
                        self.server.shutdown()
                        result = {"status": "stopping"}
                    else:
                        result = getattr(recorder, packet["operation"])(**args)
                    response = {"ok": True, "result": result}
                except Exception as error:
                    # Parameters/content are not included in error replies.
                    response = {"ok": False, "error": f"{type(error).__name__}: {error}"}
                self.wfile.write((canonical_json(response) + "\n").encode())

        class Server(socketserver.ThreadingUnixStreamServer):
            daemon_threads = False
            block_on_close = True

        previous_umask = os.umask(0o077)
        try:
            server = Server(str(destination), Handler)
        finally:
            os.umask(previous_umask)
        os.chmod(destination, 0o600)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            destination.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    server = commands.add_parser("serve")
    server.add_argument("--db", required=True)
    server.add_argument("--socket", required=True)
    server.add_argument("--trusted-receipt-sha256", action="append", default=[])
    call = commands.add_parser("request")
    call.add_argument("--socket", required=True)
    call.add_argument("--json", required=True)
    tool = commands.add_parser("tool")
    tool.add_argument("--socket", required=True)
    for name in ("run-id", "span-id", "actor-id", "task-id", "attempt-id", "phase", "category"):
        tool.add_argument("--" + name, required=True)
    tool.add_argument("--parent-span-id")
    tool.add_argument("--label", required=True)
    tool.add_argument("--redaction-reason", default="argv omitted; safe operation label and hash only")
    tool.add_argument("--timeout", type=float, default=300)
    tool.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            serve(args.db, args.socket, trusted_receipt_sha256=args.trusted_receipt_sha256)
            return 0
        if args.command == "request":
            packet = json.loads(args.json)
            result = request(args.socket, packet["operation"], **packet.get("arguments", {}))
        else:
            command = args.argv[1:] if args.argv and args.argv[0] == "--" else args.argv
            result = request(args.socket, "run_tool", argv=command, timeout=args.timeout,
                run_id=args.run_id, span_id=args.span_id, actor_id=args.actor_id, task_id=args.task_id,
                attempt_id=args.attempt_id, phase=args.phase, category=args.category,
                parent_span_id=args.parent_span_id, command_label=args.label, redaction_reason=args.redaction_reason)
        print(canonical_json(result))
        if args.command == "tool":
            return result["tool"]["exit_code"] if result["tool"]["exit_code"] is not None and result["tool"]["exit_code"] >= 0 else 1
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(f"cost recorder: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
