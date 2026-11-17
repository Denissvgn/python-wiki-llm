# MigrateError

**Location:** `src/llm_wiki_cli/services/migrate_service.py:71`
**Kind:** Class
**Bases:** `Exception`
**Module:** [migrate_service](../modules/migrate_service.md)

## Description

Migration stopped; ``exit_code`` is the status the CLI would exit with.

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
    n0["MigrateError (src/llm_wiki_cli/services/migrate_service.py)"]
    n1["Exception"]
    n2["MigrateRequestError (src/llm_wiki_cli/services/migrate_service.py)"]
    n3["src/llm_wiki_cli/api.py"]
    n4["src/llm_wiki_cli/engine/__init__.py"]
    n5["execute_migrate (src/llm_wiki_cli/services/migrate_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/migrate_service.md"
    click n2 "../modules/migrate_service.md"
    click n3 "../modules/api.md"
    click n4 "../modules/engine___init__.md"
    click n5 "../modules/migrate_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [migrate_service](../modules/migrate_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Exception` | — |
| Subclass | `MigrateRequestError` | [migrate_service](../modules/migrate_service.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `execute_migrate` | call | [migrate_runtime](../modules/migrate_runtime.md) | 1 |
