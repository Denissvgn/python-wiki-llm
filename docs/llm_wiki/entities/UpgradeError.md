# UpgradeError

**Location:** `src/llm_wiki_cli/services/upgrade_service.py:71`
**Kind:** Class
**Bases:** `Exception`
**Module:** [upgrade_service](../modules/upgrade_service.md)

## Description

Upgrade stopped; ``exit_code`` is the status the CLI would exit with.

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
    n0["UpgradeError (src/llm_wiki_cli/services/upgrade_service.py)"]
    n1["Exception"]
    n2["UpgradeRequestError (src/llm_wiki_cli/services/upgrade_service.py)"]
    n3["src/llm_wiki_cli/engine/__init__.py"]
    n4["execute_upgrade (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/upgrade_service.md"
    click n2 "../modules/upgrade_service.md"
    click n3 "../modules/engine___init__.md"
    click n4 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [upgrade_service](../modules/upgrade_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Exception` | — |
| Subclass | `UpgradeRequestError` | [upgrade_service](../modules/upgrade_service.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `execute_upgrade` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 1 |
