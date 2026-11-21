# EngineEvent

**Location:** `src/llm_wiki_engine/engine_events.py:55`
**Kind:** Class
**Bases:** —
**Module:** [engine_events](../modules/engine_events.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One thing that happened during an engine operation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `EventKind` | *required* | — |
| `operation` | `str` | *required* | — |
| `operation_id` | `str` | *required* | — |
| `data` | `Mapping[str, Any]` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | The ``llm-wiki-engine-event/v1`` form of this event. |
| `from_dict` | `(document: object) -> EngineEvent` | `@classmethod` | Read an event written by :meth:`to_dict`; ``ValueError`` when invalid. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EngineEvent (src/llm_wiki_engine/engine_events.py)"]
    n1["Engine._report (src/llm_wiki_cli/engine/__init__.py)"]
    n2["Engine._report (src/llm_wiki_engine/engine.py)"]
    n3["EngineEvent.from_dict (src/llm_wiki_engine/engine_events.py)"]
    n4["_publish_message (src/llm_wiki_engine/host.py)"]
    n5["Host.publish (src/llm_wiki_engine/host.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/engine_events.md"
    click n1 "../modules/engine___init__.md"
    click n2 "../modules/engine.md"
    click n3 "../modules/engine_events.md"
    click n4 "../modules/host.md"
    click n5 "../modules/host.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [engine_events](../modules/engine_events.md) | 3 | `data`, `kind`, `operation`, `operation_id` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `Engine._report` | call | [engine___init__](../modules/engine___init__.md) | 1 |
| `Engine._report` | call | [engine](../modules/engine.md) | 1 |
| `EngineEvent.from_dict` | call | [engine_events](../modules/engine_events.md) | 1 |
| `EngineEvent.from_dict` | type_reference | [engine_events](../modules/engine_events.md) | — |
| `_publish_message` | call | [host](../modules/host.md) | 1 |
| `Host.publish` | type_reference | [host](../modules/host.md) | — |
