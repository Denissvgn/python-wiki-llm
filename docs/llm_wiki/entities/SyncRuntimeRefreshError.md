# SyncRuntimeRefreshError

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:344`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_runtime](../modules/sync_runtime.md)

## Description

A runtime-basis transition cannot be applied in the requested mode.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncRuntimeRefreshError (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["ValueError"]
    n2["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["_try_sync_knowledge_reuse (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_prepare_sync_run` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_try_sync_knowledge_reuse` | call | [sync_runtime](../modules/sync_runtime.md) | 7 |
