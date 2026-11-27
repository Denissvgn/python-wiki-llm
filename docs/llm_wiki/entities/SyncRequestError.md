# SyncRequestError

**Location:** `src/llm_wiki_cli/services/sync_service.py:94`
**Kind:** Class
**Bases:** `SyncError`
**Module:** [sync_service](../modules/sync_service.md)

## Description

The request's options are invalid or contradict each other.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncRequestError (src/llm_wiki_cli/services/sync_service.py)"]
    n1["SyncError (src/llm_wiki_cli/services/sync_service.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/engine/__init__.py"]
    n4["execute_sync (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/sync_service.md"
    click n1 "../modules/sync_service.md"
    click n2 "../modules/api.md"
    click n3 "../modules/engine___init__.md"
    click n4 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_service](../modules/sync_service.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `SyncError` | [sync_service](../modules/sync_service.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `execute_sync` | call | [sync_runtime](../modules/sync_runtime.md) | 2 |
