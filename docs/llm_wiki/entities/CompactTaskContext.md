# CompactTaskContext

**Location:** `src/llm_wiki_cli/services/task_compact.py:85`
**Kind:** Class
**Bases:** —
**Module:** [task_compact](../modules/task_compact.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `CompactTaskContext` in `src/llm_wiki_cli/services/task_compact.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `ok` | `bool` | *required* | — |
| `rendered` | `str` | *required* | — |
| `accounting` | `Mapping[str, Any]` | *required* | — |
| `canonical_text` | `str` | *required* | — |
| `canonical_accounting` | `Mapping[str, Any]` | *required* | — |
| `error` | `str \| None` | `None` | — |
| `schema_version` | `str` | `COMPACT_SCHEMA` | — |
| `diagnostic_rendered` | `str` | `''` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `()` | — | — |
| `view_id` | `()` | `@property` | — |
| `to_payload` | `()` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["CompactTaskContext (src/llm_wiki_cli/services/task_compact.py)"]
    n1["build_compact_task_context (src/llm_wiki_cli/api.py)"]
    n2["render_compact_task_context (src/llm_wiki_cli/api.py)"]
    n3["src/llm_wiki_cli/services/context_session.py"]
    n4["render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)"]
    n5["build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/task_compact.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/context_session.md"
    click n4 "../modules/task_compact.md"
    click n5 "../modules/task_compact_delivery.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [task_compact](../modules/task_compact.md) | 3 | `accounting`, `canonical_accounting`, `canonical_text`, `diagnostic_rendered`, `error`, `ok`, `rendered`, `schema_version` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `render_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `context_session` | import | [context_session](../modules/context_session.md) | — |
| `render_compact_task_context` | call | [task_compact](../modules/task_compact.md) | 2 |
| `build_compact_task_context` | type_reference | [task_compact_delivery](../modules/task_compact_delivery.md) | — |
