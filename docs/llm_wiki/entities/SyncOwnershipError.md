# SyncOwnershipError

**Location:** `src/llm_wiki_engine/sync_ownership.py:6`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_ownership](../modules/sync_ownership.md)

## Description

A page cannot be safely assigned to one recorded source entity.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncOwnershipError (src/llm_wiki_engine/sync_ownership.py)"]
    n1["ValueError"]
    n2["PageTransitionError (src/llm_wiki_engine/sync_ownership.py)"]
    n3["_ownership_error (src/llm_wiki_cli/services/sync_analysis.py)"]
    n4["_recorded_entity_pages (src/llm_wiki_cli/services/sync_analysis.py)"]
    n5["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["src/llm_wiki_cli/services/sync_transitions.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/sync_ownership.md"
    click n2 "../modules/sync_ownership.md"
    click n3 "../modules/sync_analysis.md"
    click n4 "../modules/sync_analysis.md"
    click n5 "../modules/sync_runtime.md"
    click n6 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_ownership](../modules/sync_ownership.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `PageTransitionError` | [sync_ownership](../modules/sync_ownership.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_ownership_error` | call | [sync_analysis](../modules/sync_analysis.md) | 1 |
| `_ownership_error` | type_reference | [sync_analysis](../modules/sync_analysis.md) | — |
| `_recorded_entity_pages` | call | [sync_analysis](../modules/sync_analysis.md) | 2 |
| `_prepare_sync_run` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `sync_transitions` | import | [sync_transitions](../modules/sync_transitions.md) | — |
