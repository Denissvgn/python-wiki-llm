"""Structured events an engine reports to its host while an operation runs.

A host that wants more than text on its streams passes an event sink, any
callable taking one :class:`EngineEvent`, as ``Host(events=...)``. Every
engine use case then reports:

``operation.started``
    ``data``: ``source_root`` and ``wiki_root`` when the request has them.
``message``
    One line the operation wrote to the host; ``data``: ``stream``
    (``"stdout"`` or ``"stderr"``) and ``text`` (without the line break).
    Lines written while output is deliberately discarded are not reported.
``operation.finished``
    ``data``: ``result``, the JSON-ready form of the returned result.
``operation.failed``
    ``data``: ``error`` (exception class name), ``message`` and, when the
    error carries one, ``exit_code``. The exception is still raised.

All events of one call share ``operation`` (the use-case name, such as
``"sync"``) and ``operation_id``, so one sink can serve several engines.
``data`` holds only JSON-compatible values. The sink runs on the
operation's thread; an exception it raises stops the operation the same way
a failing stream write would.

This module only uses the standard library, so a host can import it without
loading the engine.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

EventKind = Literal["operation.started", "message", "operation.finished", "operation.failed"]

#: Every event kind an engine reports.
EVENT_KINDS: frozenset[str] = frozenset(
    {"operation.started", "message", "operation.finished", "operation.failed"}
)


@dataclass(frozen=True)
class EngineEvent:
    """One thing that happened during an engine operation."""

    kind: EventKind
    operation: str
    operation_id: str
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in EVENT_KINDS:
            raise ValueError(f"unknown engine event kind: {self.kind!r}")
        object.__setattr__(self, "data", MappingProxyType(dict(self.data)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "operation": self.operation,
            "operation_id": self.operation_id,
            "data": dict(self.data),
        }


#: Receives each event; its return value is ignored.
EventSink = Callable[[EngineEvent], object]


@dataclass(frozen=True)
class OperationIdentity:
    """Names the engine operation that events are reported for."""

    name: str
    operation_id: str


_CURRENT: ContextVar[OperationIdentity | None] = ContextVar("llm_wiki_engine_operation", default=None)


def current_operation() -> OperationIdentity | None:
    """The engine operation running in this context, if any."""
    return _CURRENT.get()


@contextmanager
def operation_identity(name: str, operation_id: str) -> Iterator[OperationIdentity]:
    """Report events inside the block as part of operation ``name``."""
    identity = OperationIdentity(name, operation_id)
    token = _CURRENT.set(identity)
    try:
        yield identity
    finally:
        _CURRENT.reset(token)


__all__ = [
    "EVENT_KINDS",
    "EngineEvent",
    "EventKind",
    "EventSink",
    "OperationIdentity",
    "current_operation",
    "operation_identity",
]
