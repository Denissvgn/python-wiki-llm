# SyncError

**Location:** `src/llm_wiki_cli/services/sync_service.py:85`
**Kind:** Class
**Bases:** `Exception`
**Module:** [sync_service](../modules/sync_service.md)

## Description

Sync stopped; ``exit_code`` is the status the CLI would exit with.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, *, exit_code: int) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncError (src/llm_wiki_cli/services/sync_service.py)"]
    n1["Exception"]
    n2["SyncRequestError (src/llm_wiki_cli/services/sync_service.py)"]
    n3["src/llm_wiki_cli/api.py"]
    n4["src/llm_wiki_cli/engine/__init__.py"]
    n5["execute_sync (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/sync_service.md"
    click n2 "../modules/sync_service.md"
    click n3 "../modules/api.md"
    click n4 "../modules/engine___init__.md"
    click n5 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_service](../modules/sync_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Exception` | — |
| Subclass | `SyncRequestError` | [sync_service](../modules/sync_service.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `execute_sync` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
