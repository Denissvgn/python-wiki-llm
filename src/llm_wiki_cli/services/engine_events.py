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
``data`` holds only JSON-compatible values.

:meth:`EngineEvent.to_dict` writes the ``llm-wiki-engine-event/v1`` format
(JSON Schema ``llm-wiki-engine-event-v1.schema.json``); a host that receives
serialized events checks one with :func:`validate_engine_event` or reads it
back with :meth:`EngineEvent.from_dict`. The sink runs on the
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

#: The format :meth:`EngineEvent.to_dict` writes.
ENGINE_EVENT_SCHEMA_VERSION = "llm-wiki-engine-event/v1"

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
        """The ``llm-wiki-engine-event/v1`` form of this event."""
        return {
            "schema_version": ENGINE_EVENT_SCHEMA_VERSION,
            "kind": self.kind,
            "operation": self.operation,
            "operation_id": self.operation_id,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, document: object) -> EngineEvent:
        """Read an event written by :meth:`to_dict`; ``ValueError`` when invalid."""
        validate_engine_event(document)
        assert isinstance(document, Mapping)
        return cls(document["kind"], document["operation"], document["operation_id"], document["data"])


_EVENT_FIELDS = frozenset({"schema_version", "kind", "operation", "operation_id", "data"})
#: Required and optional ``data`` fields of each kind.
_DATA_FIELDS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "operation.started": (frozenset(), frozenset({"source_root", "wiki_root"})),
    "message": (frozenset({"stream", "text"}), frozenset()),
    "operation.finished": (frozenset({"result"}), frozenset()),
    "operation.failed": (frozenset({"error", "message"}), frozenset({"exit_code"})),
}


def _json_value(value: object, path: str) -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"{path} must be a finite number")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} keys must be strings")
            _json_value(item, f"{path}.{key}")
        return
    raise ValueError(f"{path} must hold only JSON values")


def _text(value: object, path: str, *, empty: bool = False) -> None:
    if not isinstance(value, str) or (not empty and not value):
        raise ValueError(f"{path} must be {'a' if empty else 'a non-empty'} string")


def validate_engine_event(document: object) -> None:
    """Refuse a document that is not a valid ``llm-wiki-engine-event/v1`` event."""
    if not isinstance(document, Mapping) or set(document) != _EVENT_FIELDS:
        raise ValueError("an engine event has exactly " + ", ".join(sorted(_EVENT_FIELDS)))
    if document["schema_version"] != ENGINE_EVENT_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {ENGINE_EVENT_SCHEMA_VERSION!r}")
    kind = document["kind"]
    if kind not in EVENT_KINDS:
        raise ValueError(f"unknown engine event kind: {kind!r}")
    _text(document["operation"], "operation")
    _text(document["operation_id"], "operation_id")
    data = document["data"]
    if not isinstance(data, Mapping):
        raise ValueError("data must be an object")
    required, optional = _DATA_FIELDS[kind]
    keys = set(data)
    if not required <= keys or keys - required - optional:
        raise ValueError(f"{kind} data has fields " + ", ".join(sorted(required | optional)))
    _json_value(data, "data")
    if kind == "operation.started":
        for name in keys:
            _text(data[name], f"data.{name}")
    elif kind == "message":
        if data["stream"] not in ("stdout", "stderr"):
            raise ValueError("data.stream must be 'stdout' or 'stderr'")
        _text(data["text"], "data.text", empty=True)
    elif kind == "operation.finished":
        if not isinstance(data["result"], Mapping):
            raise ValueError("data.result must be an object")
    else:
        _text(data["error"], "data.error")
        _text(data["message"], "data.message", empty=True)
        exit_code = data.get("exit_code", 0)
        if isinstance(exit_code, bool) or not (
            isinstance(exit_code, int) or isinstance(exit_code, float) and exit_code.is_integer()
        ):
            raise ValueError("data.exit_code must be an integer")


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
    "ENGINE_EVENT_SCHEMA_VERSION",
    "EVENT_KINDS",
    "EngineEvent",
    "EventKind",
    "EventSink",
    "OperationIdentity",
    "current_operation",
    "operation_identity",
    "validate_engine_event",
]
