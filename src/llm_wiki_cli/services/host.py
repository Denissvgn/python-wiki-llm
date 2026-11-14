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

This is the only engine module that touches ``subprocess``, ``os.environ``,
the current directory, the clock and the standard streams directly.
"""

from __future__ import annotations

import copy
import io
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal, Protocol


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

    def __init__(self, *, stdout: TextSink | None = None, stderr: TextSink | None = None) -> None:
        self._stdout = stdout
        self._stderr = stderr

    @property
    def stdout(self) -> TextSink:
        """Where progress and results are written."""
        return sys.stdout if self._stdout is None else self._stdout

    @property
    def stderr(self) -> TextSink:
        """Where warnings and errors are written."""
        return sys.stderr if self._stderr is None else self._stderr

    def with_output(self, *, stdout: TextSink | None = None, stderr: TextSink | None = None) -> Host:
        """A copy of this host whose given streams replace the current ones."""
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


class _Discard(io.TextIOBase):
    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        return len(text)


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
