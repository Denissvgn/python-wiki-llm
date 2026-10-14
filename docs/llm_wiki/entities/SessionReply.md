# SessionReply

**Location:** `src/llm_wiki_cli/services/context_session.py:126`
**Kind:** Class
**Bases:** —
**Module:** [context_session](../modules/context_session.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Separates full, unchanged or delta context delivery from session work telemetry. A matching result identity is returned unchanged only after current input validation. Delta consumers must reconstruct and validate the complete canonical task result.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `str` | *required* | — |
| `result_id` | `str \| None` | *required* | — |
| `context` | `TaskContext \| None` | *required* | — |
| `delta` | `Mapping[str, Any] \| None` | *required* | — |
| `_metadata` | `Mapping[str, Any]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `metadata` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SessionReply (src/llm_wiki_cli/services/context_session.py)"]
    n1["ContextSession.read (src/llm_wiki_cli/api.py)"]
    n2["ContextSession.read_compact (src/llm_wiki_cli/api.py)"]
    n3["ContextSession._read (src/llm_wiki_cli/services/context_session.py)"]
    n4["ContextSession.read (src/llm_wiki_cli/services/context_session.py)"]
    n5["ContextSession.read_compact (src/llm_wiki_cli/services/context_session.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/context_session.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/context_session.md"
    click n4 "../modules/context_session.md"
    click n5 "../modules/context_session.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_session](../modules/context_session.md) | 1 | `_metadata`, `context`, `delta`, `result_id`, `state` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `ContextSession.read` | type_reference | [api](../modules/api.md) | — |
| `ContextSession.read_compact` | type_reference | [api](../modules/api.md) | — |
| `ContextSession._read` | call | [context_session](../modules/context_session.md) | 1 |
| `ContextSession.read` | type_reference | [context_session](../modules/context_session.md) | — |
| `ContextSession.read_compact` | type_reference | [context_session](../modules/context_session.md) | — |
