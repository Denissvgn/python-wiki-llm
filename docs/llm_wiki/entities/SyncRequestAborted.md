# SyncRequestAborted

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:273`
**Kind:** Class
**Bases:** `SyncAborted`
**Module:** [sync_runtime](../modules/sync_runtime.md)

## Description

The request's options were rejected before any sync work started.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncRequestAborted (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["SyncAborted (src/llm_wiki_cli/services/sync_runtime.py)"]
    n2["_flow_category_args (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["_surface_args (src/llm_wiki_cli/services/sync_runtime.py)"]
    n4["_sync_run_options_from_request (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/sync_runtime.md"
    click n1 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/sync_runtime.md"
    click n4 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `SyncAborted` | [sync_runtime](../modules/sync_runtime.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_flow_category_args` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_surface_args` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_sync_run_options_from_request` | call | [sync_runtime](../modules/sync_runtime.md) | 4 |
