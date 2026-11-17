"""Bounded command-local phase events; services are silent without a caller sink."""

from __future__ import annotations

import contextvars
import json
import re
import sys
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, TextIO, TypeVar, cast

from .contracts import PROGRESS_SCHEMA_VERSION

_CURRENT: contextvars.ContextVar[Progress | None] = contextvars.ContextVar(
    "llm_wiki_progress", default=None
)
_LABEL = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
_COUNTERS = frozenset(
    {
        "inventory_files",
        "cache_hits",
        "cache_misses",
        "concepts",
        "relationships",
        "mapped_pages",
        "written_artifacts",
        "completed_plans",
    }
)
_F = TypeVar("_F", bound=Callable[..., Any])


@dataclass(eq=False)
class Phase:
    name: str
    started: float
    elapsed_seconds: float = 0.0
    announced: bool = False
    owner: int = field(default_factory=threading.get_ident)


class Progress:
    """One lightweight heartbeat worker and one bounded stream per command."""

    def __init__(
        self,
        command: str,
        *,
        mode: str = "auto",
        output_format: str = "text",
        stream: TextIO | None = None,
        clock: Callable[[], float] = time.perf_counter,
        interval: float = 10.0,
        start_thread: bool = True,
    ):
        if mode not in {"auto", "always", "never"} or output_format not in {
            "text",
            "json",
        }:
            raise ValueError("invalid progress mode or format")
        if not _LABEL.fullmatch(command.replace("-", "_")) or not 0 < interval <= 15:
            raise ValueError("invalid progress command or heartbeat interval")
        self.command = command
        self.mode = mode
        self.output_format = output_format
        self.stream = sys.stderr if stream is None else stream
        self.clock = clock
        self.interval = interval
        self.start_thread = start_thread
        self.run_id = uuid.uuid4().hex
        self.started = clock()
        self.last_event = self.started
        self.phases: list[Phase] = []
        self.durations: dict[str, float] = {}
        self.counts: dict[str, int] = {}
        self.failure_phase: str | None = None
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._broken = False
        self._announced = False
        self._terminal = False
        try:
            interactive = self.stream.isatty()
        except Exception:
            interactive = False
        self.immediate = mode == "always" or (mode == "auto" and interactive)

    def _emit(
        self, event: str, phase: str | None = None, elapsed_ms: int | None = None
    ) -> None:
        if self.mode == "never" or self._broken:
            return
        now = self.clock()
        payload = {
            "schema_version": PROGRESS_SCHEMA_VERSION,
            "run_id": self.run_id,
            "command": self.command,
            "event": event,
            "phase": phase,
            "elapsed_ms": max(0, round((now - self.started) * 1000))
            if elapsed_ms is None
            else max(0, elapsed_ms),
            "counts": dict(sorted(self.counts.items())),
        }
        try:
            if self.output_format == "json":
                line = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            else:
                line = f"{self.command}: {event} phase={phase or 'run'} elapsed={payload['elapsed_ms']}ms"
            if len(line.encode("utf-8")) > 1023:
                return
            self.stream.write(line + "\n")
            self.stream.flush()
            self.last_event = now
        except Exception:
            self._broken = True

    def _announce(self) -> None:
        if not self._announced:
            self._emit("run_started")
            self._announced = True

    def tick(self) -> None:
        """Emit a due heartbeat; injectable clocks need no real waiting in tests."""
        with self._lock:
            if self._terminal or self._stop.is_set() or self.mode == "never":
                return
            now = self.clock()
            if now - self.last_event < self.interval:
                return
            # With no instrumented phase, the command itself is still active.
            self._announce()
            for active in self.phases:
                if not active.announced:
                    self._emit(
                        "phase_started",
                        active.name,
                        round((now - active.started) * 1000),
                    )
                    active.announced = True
            active = self.phases[-1] if self.phases else None
            self._emit(
                "heartbeat",
                None if active is None else active.name,
                round((now - (active.started if active else self.started)) * 1000),
            )

    def _heartbeat(self) -> None:
        while not self._stop.wait(self.interval):
            self.tick()

    @contextmanager
    def phase(self, name: str) -> Iterator[Phase]:
        if not _LABEL.fullmatch(name):
            raise ValueError("progress phases must be bounded static labels")
        with self._lock:
            current = next(
                (
                    item
                    for item in reversed(self.phases)
                    if item.owner == threading.get_ident()
                ),
                None,
            )
        if current is not None and current.name == name:
            yield current
            return
        active = Phase(name, self.clock())
        with self._lock:
            self.phases.append(active)
            if self.immediate:
                self._announce()
                self._emit("phase_started", name, 0)
                active.announced = True
        failed = False
        try:
            yield active
        except BaseException as exc:
            failed = not isinstance(exc, SystemExit) or exc.code not in (None, 0)
            with self._lock:
                if failed and self.failure_phase is None:
                    self.failure_phase = name
            raise
        finally:
            with self._lock:
                active.elapsed_seconds = max(0.0, self.clock() - active.started)
                self.durations[name] = (
                    self.durations.get(name, 0.0) + active.elapsed_seconds
                )
                self.phases.remove(active)
                if active.announced and not failed:
                    self._emit(
                        "phase_finished", name, round(active.elapsed_seconds * 1000)
                    )

    @contextmanager
    def run(self) -> Iterator[Progress]:
        self.started = self.last_event = self.clock()
        token = _CURRENT.set(self)
        failed = False
        try:
            if self.immediate:
                self._announce()
            if self.mode != "never" and self.start_thread:
                try:
                    self._thread = threading.Thread(
                        target=self._heartbeat, name="llm-wiki-progress", daemon=True
                    )
                    self._thread.start()
                except (RuntimeError, OSError, MemoryError):
                    self._thread = None
            yield self
        except BaseException as exc:
            failed = not isinstance(exc, SystemExit) or exc.code not in (None, 0)
            raise
        finally:
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=1.0)
            with self._lock:
                if not self._terminal and (self.immediate or self._announced or failed):
                    self._announce()
                    self._emit(
                        "run_failed" if failed else "run_finished", self.failure_phase
                    )
                self._terminal = True
            _CURRENT.reset(token)


@contextmanager
def phase(name: str) -> Iterator[Phase]:
    reporter = _CURRENT.get()
    if reporter is not None:
        with reporter.phase(name) as timing:
            yield timing
    else:
        timing = Phase(name, time.perf_counter())
        try:
            yield timing
        finally:
            timing.elapsed_seconds = max(0.0, time.perf_counter() - timing.started)


def observed_phase(name: str) -> Callable[[_F], _F]:
    def decorate(function: _F) -> _F:
        @wraps(function)
        def observed(*args, **kwargs):
            with phase(name):
                return function(*args, **kwargs)

        return cast(_F, observed)

    return decorate


def current_progress() -> Progress | None:
    return _CURRENT.get()


def record_counts(**counts: int) -> None:
    reporter = _CURRENT.get()
    if reporter is not None:
        with reporter._lock:
            reporter.counts.update(
                {
                    key: value
                    for key, value in counts.items()
                    if key in _COUNTERS and type(value) is int and 0 <= value < 2**63
                }
            )


def with_progress(
    reporter: Progress | None, function: Callable[..., Any], *args, **kwargs
):
    """Propagate only the caller's progress sink to extraction worker threads."""
    token = _CURRENT.set(reporter)
    try:
        return function(*args, **kwargs)
    finally:
        _CURRENT.reset(token)
