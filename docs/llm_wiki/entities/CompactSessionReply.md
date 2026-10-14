# CompactSessionReply

**Location:** `src/llm_wiki_cli/services/context_session.py:140`
**Kind:** Class
**Bases:** —
**Module:** [context_session](../modules/context_session.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `CompactSessionReply` in `src/llm_wiki_cli/services/context_session.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `str` | *required* | — |
| `result_id` | `str \| None` | *required* | — |
| `view_id` | `str \| None` | *required* | — |
| `view` | `CompactTaskContext \| None` | *required* | — |
| `canonical` | `TaskContext \| None` | *required* | — |
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
    n0["CompactSessionReply (src/llm_wiki_cli/services/context_session.py)"]
    n1["ContextSession.read_compact (src/llm_wiki_cli/api.py)"]
    n2["ContextSession._read (src/llm_wiki_cli/services/context_session.py)"]
    n3["ContextSession.read_compact (src/llm_wiki_cli/services/context_session.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/context_session.md"
    click n1 "../modules/api.md"
    click n2 "../modules/context_session.md"
    click n3 "../modules/context_session.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_session](../modules/context_session.md) | 1 | `_metadata`, `canonical`, `delta`, `result_id`, `state`, `view`, `view_id` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `ContextSession.read_compact` | type_reference | [api](../modules/api.md) | — |
| `ContextSession._read` | call | [context_session](../modules/context_session.md) | 1 |
| `ContextSession.read_compact` | type_reference | [context_session](../modules/context_session.md) | — |
