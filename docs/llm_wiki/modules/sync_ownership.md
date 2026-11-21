# sync_ownership Module

**Path:** `src/llm_wiki_engine/sync_ownership.py`

## Description

Errors raised when a sync cannot keep verified page ownership.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/sync_analysis.py"]
    n1["src/llm_wiki_cli/services/sync_transitions.py"]
    n2["src/llm_wiki_engine/sync_ownership.py"]
    n3["src/llm_wiki_engine/sync_transition_execution.py"]
    n0 --> n2
    n1 --> n0
    n1 --> n2
    n3 --> n2
    click n0 "../modules/sync_analysis.md"
    click n1 "../modules/sync_transitions.md"
    click n2 "../modules/sync_ownership.md"
    click n3 "../modules/sync_transition_execution.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_analysis](../modules/sync_analysis.md) |
| Inbound | [sync_transitions](../modules/sync_transitions.md) |
| Inbound | [sync_transition_execution](../modules/sync_transition_execution.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [SyncOwnershipError](../entities/SyncOwnershipError.md) | 6 | `ValueError` | A page cannot be safely assigned to one recorded source entity. |
| [PageTransitionError](../entities/PageTransitionError.md) | 10 | `SyncOwnershipError` | The intended page writes cannot preserve verified ownership. |
