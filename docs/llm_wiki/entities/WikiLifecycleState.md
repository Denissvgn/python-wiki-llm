# WikiLifecycleState

**Location:** `src/llm_wiki_cli/services/wiki_lifecycle.py:130`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Description

One unambiguous lifecycle route for a wiki target.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `FIRST_USE` | `'first-use'` | — |
| `SYNC_SEEDABLE` | `'sync-seedable'` | — |
| `MIGRATION_REQUIRED` | `'migration-required'` | — |
| `MANAGED` | `'managed'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiLifecycleState (src/llm_wiki_cli/services/wiki_lifecycle.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/sync_cmd.py"]
    n4["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n5["src/llm_wiki_cli/services/ci_installer.py"]
    n6["src/llm_wiki_cli/services/lint_service.py"]
    n7["classify_wiki_lifecycle (src/llm_wiki_cli/services/wiki_lifecycle.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/wiki_lifecycle.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/ci_installer.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/wiki_lifecycle.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_lifecycle](../modules/wiki_lifecycle.md) | 0 | `FIRST_USE`, `MANAGED`, `MIGRATION_REQUIRED`, `SYNC_SEEDABLE` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) | — |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `ci_installer` | import | [ci_installer](../modules/ci_installer.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `classify_wiki_lifecycle` | type_reference | [wiki_lifecycle](../modules/wiki_lifecycle.md) | — |
