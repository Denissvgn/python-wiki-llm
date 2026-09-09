# _ReusedSync

**Location:** `src/llm_wiki_cli/commands/sync_cmd.py:1716`
**Kind:** Class
**Bases:** —
**Module:** [sync_cmd](../modules/sync_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_ReusedSync` in `src/llm_wiki_cli/commands/sync_cmd.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `artifacts` | `KnowledgeCommitResult` | *required* | — |
| `cache_stats` | `InventoryCacheStats \| None` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ReusedSync (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n1["_prepare_sync_run (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_try_sync_knowledge_reuse (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/sync_cmd.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/sync_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_cmd](../modules/sync_cmd.md) | 0 | `artifacts`, `cache_stats` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_prepare_sync_run` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_try_sync_knowledge_reuse` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `_try_sync_knowledge_reuse` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
