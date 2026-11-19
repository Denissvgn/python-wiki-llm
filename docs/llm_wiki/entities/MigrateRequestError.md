# MigrateRequestError

**Location:** `src/llm_wiki_cli/services/migrate_service.py:79`
**Kind:** Class
**Bases:** `MigrateError`
**Module:** [migrate_service](../modules/migrate_service.md)

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
    n0["MigrateRequestError (src/llm_wiki_cli/services/migrate_service.py)"]
    n1["MigrateError (src/llm_wiki_cli/services/migrate_service.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/engine/__init__.py"]
    n4["execute_migrate (src/llm_wiki_cli/services/migrate_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/migrate_service.md"
    click n1 "../modules/migrate_service.md"
    click n2 "../modules/api.md"
    click n3 "../modules/engine___init__.md"
    click n4 "../modules/migrate_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [migrate_service](../modules/migrate_service.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `MigrateError` | [migrate_service](../modules/migrate_service.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `execute_migrate` | call | [migrate_runtime](../modules/migrate_runtime.md) | 2 |
