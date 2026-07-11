from __future__ import annotations

import errno
from collections.abc import Iterator


_RECOVERY_GUIDANCE = (
    "Recover system resource capacity first, then manually retry once with "
    "--jobs 1; no automatic retry was attempted."
)
_MISSING_ERRNO = object()
_ENOSPC = getattr(errno, "ENOSPC", _MISSING_ERRNO)
_EMFILE = getattr(errno, "EMFILE", _MISSING_ERRNO)
_ENFILE = getattr(errno, "ENFILE", _MISSING_ERRNO)
_ENOMEM = getattr(errno, "ENOMEM", _MISSING_ERRNO)
_EAGAIN = getattr(errno, "EAGAIN", _MISSING_ERRNO)


def _exception_chain(exc: BaseException) -> Iterator[BaseException]:
    pending = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)


def resource_failure_hint(
    exc: BaseException, *, executor_start: bool = False
) -> str | None:
    """Return portable recovery guidance for recognised capacity failures."""

    chain = tuple(_exception_chain(exc))
    for current in chain:
        if isinstance(current, MemoryError):
            return f"Memory capacity was exhausted. {_RECOVERY_GUIDANCE}"
        if not isinstance(current, OSError):
            continue
        if current.errno == _ENOSPC:
            return (
                "ENOSPC may indicate exhausted disk or quota capacity, or host "
                "watcher capacity; it does not identify a single cause. "
                f"{_RECOVERY_GUIDANCE}"
            )
        if current.errno == _EMFILE:
            return (
                "The process file-descriptor capacity was exhausted (EMFILE). "
                f"{_RECOVERY_GUIDANCE}"
            )
        if current.errno == _ENFILE:
            return (
                "The host file-descriptor capacity was exhausted (ENFILE). "
                f"{_RECOVERY_GUIDANCE}"
            )
        if current.errno == _ENOMEM:
            return f"Memory capacity was exhausted (ENOMEM). {_RECOVERY_GUIDANCE}"
        if current.errno == _EAGAIN:
            return (
                "A temporary process, thread, or file resource was unavailable "
                f"(EAGAIN). {_RECOVERY_GUIDANCE}"
            )
    if executor_start and any(isinstance(current, RuntimeError) for current in chain):
        return (
            "The extraction worker pool could not start because runtime capacity "
            f"was unavailable. {_RECOVERY_GUIDANCE}"
        )
    return None


def format_resource_failure(
    exc: BaseException, *, executor_start: bool = False
) -> str:
    """Append a resource hint to an exception message when one is recognised."""

    message = str(exc).strip() or exc.__class__.__name__
    hint = resource_failure_hint(exc, executor_start=executor_start)
    if hint is None:
        return message
    return f"{message}. Resource guidance: {hint}"
