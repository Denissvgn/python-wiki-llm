"""Host capabilities the engine uses instead of ambient process state.

Engine code starts processes, reads the environment, resolves the working
directory and reads the clock through :func:`current_host`. The default
:class:`Host` does exactly what the code did before, on this machine, so
callers that never choose a host see no change.

An embedding application subclasses :class:`Host`, for example to pin the
environment or to refuse subprocesses with :class:`NoProcessHost`, and runs
engine work inside :func:`using_host`. The choice is scoped to the current
context, so concurrent operations can use different hosts.

Human-readable progress and diagnostics go through :func:`emit`, which writes
to the host's ``stdout`` or ``stderr``. A host built with its own streams
captures that output; the default resolves ``sys.stdout``/``sys.stderr`` on
every write, so redirection and test capture keep working.

A host built with ``events=`` also receives structured
:class:`~llm_wiki_engine.engine_events.EngineEvent` objects for each
engine operation, including one ``message`` event per line written.

This is the only engine module that touches ``subprocess``, ``os.environ``,
the current directory, the clock and the standard streams directly.
"""

from __future__ import annotations

import copy
import io
import os
import subprocess
import sys
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal, Protocol

from .engine_events import EngineEvent, EventSink, current_operation


class TextSink(Protocol):
    """A writable text stream, such as ``sys.stdout`` or ``io.StringIO``."""

    def write(self, text: str, /) -> object: ...

    def flush(self) -> object: ...


class HostCapabilityError(PermissionError):
    """The active host does not grant this capability.

    It is an ``OSError``, so callers that already treat an unavailable
    executable as a soft failure degrade the same way.
    """


#: Every capability the default host grants.
ALL_CAPABILITIES = frozenset({"subprocess", "environment", "cwd", "clock"})


class Host:
    """This machine: real processes, live environment and cwd, wall clock."""

    #: Capabilities this host grants; engines report and check them.
    capabilities: frozenset[str] = ALL_CAPABILITIES

    # Class-level defaults keep subclasses that skip ``__init__`` working.
    _stdout: TextSink | None = None
    _stderr: TextSink | None = None
    _events: EventSink | None = None

    def __init__(
        self,
        *,
        stdout: TextSink | None = None,
        stderr: TextSink | None = None,
        events: EventSink | None = None,
    ) -> None:
        if events is not None and not callable(events):
            raise TypeError("events must be a callable that accepts an EngineEvent")
        self._stdout = stdout
        self._stderr = stderr
        self._events = events

    @property
    def stdout(self) -> TextSink:
        """Where progress and results are written."""
        return sys.stdout if self._stdout is None else self._stdout

    @property
    def stderr(self) -> TextSink:
        """Where warnings and errors are written."""
        return sys.stderr if self._stderr is None else self._stderr

    @property
    def reports_events(self) -> bool:
        """Whether this host receives structured engine events."""
        return self._events is not None

    def publish(self, event: EngineEvent) -> None:
        """Hand one engine event to this host's event sink, if it has one."""
        if self._events is not None:
            self._events(event)

    def with_output(self, *, stdout: TextSink | None = None, stderr: TextSink | None = None) -> Host:
        """A copy of this host whose given streams replace the current ones.

        The copy keeps this host's event sink.
        """
        clone = copy.copy(self)
        if stdout is not None:
            clone._stdout = stdout
        if stderr is not None:
            clone._stderr = stderr
        return clone

    def run(self, args: Any, **options: Any) -> subprocess.CompletedProcess:
        # Resolved on every call so process-wide patches of subprocess apply.
        return subprocess.run(args, **options)

    def popen(self, args: Any, **options: Any) -> subprocess.Popen:
        return subprocess.Popen(args, **options)

    @property
    def environ(self) -> Mapping[str, str]:
        return os.environ

    def cwd(self) -> Path:
        return Path.cwd()

    def now(self) -> datetime:
        """The current UTC time."""
        return datetime.now(timezone.utc)

    def today(self) -> date:
        """The local calendar date."""
        return date.today()


class NoProcessHost(Host):
    """A host that grants no subprocesses; everything else is local."""

    capabilities = ALL_CAPABILITIES - {"subprocess"}

    def run(self, args: Any, **options: Any) -> subprocess.CompletedProcess:
        raise HostCapabilityError(f"subprocess not granted by host: {_program(args)}")

    def popen(self, args: Any, **options: Any) -> subprocess.Popen:
        raise HostCapabilityError(f"subprocess not granted by host: {_program(args)}")


def _program(args: Any) -> str:
    if isinstance(args, (str, bytes, os.PathLike)):
        return os.fsdecode(args)
    return os.fsdecode(args[0]) if args else ""


_DEFAULT = Host()
_ACTIVE: ContextVar[Host | None] = ContextVar("llm_wiki_host", default=None)


def current_host() -> Host:
    """The host chosen for this context, or the local default."""
    return _ACTIVE.get() or _DEFAULT


@contextmanager
def using_host(host: Host) -> Iterator[Host]:
    """Run the enclosed engine work against ``host``."""
    if not isinstance(host, Host):
        raise TypeError("host must be a Host instance")
    token = _ACTIVE.set(host)
    try:
        yield host
    finally:
        _ACTIVE.reset(token)


Stream = Literal["stdout", "stderr"]


def emit(*values: object, stream: Stream = "stdout", sep: str = " ", end: str = "\n", flush: bool = False) -> None:
    """Write one human-readable line to the active host's stream."""
    host = current_host()
    target = host.stderr if stream == "stderr" else host.stdout
    print(*values, sep=sep, end=end, file=target, flush=flush)
    if host.reports_events and not isinstance(target, _Unpublished):
        text = sep.join(str(value) for value in values) + end
        for line in text.splitlines():
            _publish_message(host, stream, line)


def _publish_message(host: Host, stream: Stream, line: str) -> None:
    operation = current_operation()
    if operation is not None:
        host.publish(EngineEvent(
            "message", operation.name, operation.operation_id, {"stream": stream, "text": line},
        ))


class MessageStream:
    """A stream that writes to the active host and reports each line as an event.

    For code that writes to a stream object rather than calling :func:`emit`.
    A trailing partial line is reported by :meth:`close`.
    """

    def __init__(self, stream: Stream = "stdout") -> None:
        self._stream: Stream = stream
        self._pending = ""

    def _target(self) -> tuple[Host, TextSink]:
        host = current_host()
        return host, host.stderr if self._stream == "stderr" else host.stdout

    def write(self, text: str, /) -> int:
        host, target = self._target()
        target.write(text)
        if host.reports_events and not isinstance(target, _Unpublished):
            *lines, self._pending = (self._pending + text).split("\n")
            for line in lines:
                _publish_message(host, self._stream, line.removesuffix("\r"))
        return len(text)

    def flush(self) -> None:
        self._target()[1].flush()

    def close(self) -> None:
        pending, self._pending = self._pending, ""
        host, target = self._target()
        if pending and host.reports_events and not isinstance(target, _Unpublished):
            _publish_message(host, self._stream, pending)


class _Unpublished(io.TextIOBase):
    def writable(self) -> bool:
        return True


class _Discard(_Unpublished):
    def write(self, text: str) -> int:
        return len(text)


class _Deferred(_Unpublished):
    def __init__(self, output):
        self.output = output

    def write(self, text: str) -> int:
        return self.output.write(text)


@contextmanager
def deferred_stdout() -> Iterator[None]:
    """Publish stdout and its message events only after the enclosed checks succeed."""
    host = current_host()
    if isinstance(host.stdout, _Discard):
        yield
        return
    with tempfile.SpooledTemporaryFile(max_size=256 * 1024, mode="w+", encoding="utf-8", errors="surrogatepass", newline="") as output:
        with using_host(host.with_output(stdout=_Deferred(output))):
            yield
        output.seek(0)
        for line in output:
            emit(line, end="")
        host.stdout.flush()


@contextmanager
def discarding_stdout() -> Iterator[Host]:
    """Run the enclosed work with the active host's stdout discarded."""
    with using_host(current_host().with_output(stdout=_Discard())) as host:
        yield host


@contextmanager
def discarding_output() -> Iterator[Host]:
    """Run the enclosed work with the active host's stdout and stderr discarded."""
    with using_host(current_host().with_output(stdout=_Discard(), stderr=_Discard())) as host:
        yield host


class ErrorRecorder:
    """Forwards writes to a host's stderr and keeps a copy for error messages."""

    def __init__(self, host: Host) -> None:
        self._host = host
        self._parts: list[str] = []

    def write(self, text: str, /) -> int:
        self._parts.append(text)
        self._host.stderr.write(text)
        return len(text)

    def flush(self) -> None:
        self._host.stderr.flush()

    def error_text(self) -> str:
        """The ``Error:`` lines written so far, or every line if there are none."""
        lines = "".join(self._parts).splitlines()
        errors = [line for line in lines if line.startswith("Error:")]
        return "\n".join(errors or lines).strip()


@contextmanager
def recording_errors() -> Iterator[ErrorRecorder]:
    """Run the enclosed work with stderr still written, and recorded."""
    host = current_host()
    recorder = ErrorRecorder(host)
    with using_host(host.with_output(stderr=recorder)):
        yield recorder
