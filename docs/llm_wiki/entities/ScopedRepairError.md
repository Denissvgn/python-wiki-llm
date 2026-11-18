# ScopedRepairError

**Location:** `src/llm_wiki_cli/services/scoped_sync_repair.py:22`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [scoped_sync_repair](../modules/scoped_sync_repair.md)

## Description

The requested repair cannot preserve its declared scope.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ScopedRepairError (src/llm_wiki_cli/services/scoped_sync_repair.py)"]
    n1["ValueError"]
    n2["_repair_path (src/llm_wiki_cli/services/scoped_sync_repair.py)"]
    n3["_require (src/llm_wiki_cli/services/scoped_sync_repair.py)"]
    n4["_run_sync_options (src/llm_wiki_cli/services/sync_runtime.py)"]
    n5["_sync_run_options_from_request (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/scoped_sync_repair.md"
    click n2 "../modules/scoped_sync_repair.md"
    click n3 "../modules/scoped_sync_repair.md"
    click n4 "../modules/sync_runtime.md"
    click n5 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [scoped_sync_repair](../modules/scoped_sync_repair.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_repair_path` | call | [scoped_sync_repair](../modules/scoped_sync_repair.md) | 1 |
| `_require` | call | [scoped_sync_repair](../modules/scoped_sync_repair.md) | 1 |
| `_run_sync_options` | call | [sync_runtime](../modules/sync_runtime.md) | 3 |
| `_sync_run_options_from_request` | call | [sync_runtime](../modules/sync_runtime.md) | 2 |
