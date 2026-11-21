# _ReusedSync

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:1893`
**Kind:** Class
**Bases:** —
**Module:** [sync_runtime](../modules/sync_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_ReusedSync` in `src/llm_wiki_cli/services/sync_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `artifacts` | `KnowledgeCommitResult` | *required* | — |
| `cache_stats` | `InventoryCacheStats \| None` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ReusedSync (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n2["_try_sync_knowledge_reuse (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/sync_runtime.md"
    click n1 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | `artifacts`, `cache_stats` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_prepare_sync_run` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_try_sync_knowledge_reuse` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_try_sync_knowledge_reuse` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
