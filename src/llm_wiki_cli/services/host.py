"""Host capabilities the engine uses instead of ambient process state.

Engine code starts processes, reads the environment, resolves the working
directory and reads the clock through :func:`current_host`. The default
:class:`Host` does exactly what the code did before, on this machine, so
callers that never choose a host see no change.

An embedding application subclasses :class:`Host`, for example to pin the
environment or to refuse subprocesses with :class:`NoProcessHost`, and runs
engine work inside :func:`using_host`. The choice is scoped to the current
context, so concurrent operations can use different hosts.

This is the only engine module that touches ``subprocess``, ``os.environ``
and the current directory directly.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HostCapabilityError(PermissionError):
    """The active host does not grant this capability.

    It is an ``OSError``, so callers that already treat an unavailable
    executable as a soft failure degrade the same way.
    """


class Host:
    """This machine: real processes, live environment and cwd, wall clock."""

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
        return datetime.now(timezone.utc)


class NoProcessHost(Host):
    """A host that grants no subprocesses; everything else is local."""

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
