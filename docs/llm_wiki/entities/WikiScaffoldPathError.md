# WikiScaffoldPathError

**Location:** `src/llm_wiki_cli/services/wiki_lifecycle.py:27`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Description

Raised when a managed scaffold path is redirected or non-regular.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiScaffoldPathError (src/llm_wiki_cli/services/wiki_lifecycle.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/init_cmd.py"]
    n3["src/llm_wiki_cli/commands/status_cmd.py"]
    n4["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n5["provision_wiki_scaffold (src/llm_wiki_cli/services/wiki_lifecycle.py)"]
    n6["require_safe_wiki_scaffold (src/llm_wiki_cli/services/wiki_lifecycle.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/wiki_lifecycle.md"
    click n2 "../modules/init_cmd.md"
    click n3 "../modules/status_cmd.md"
    click n4 "../modules/upgrade_cmd.md"
    click n5 "../modules/wiki_lifecycle.md"
    click n6 "../modules/wiki_lifecycle.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_lifecycle](../modules/wiki_lifecycle.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `init_cmd` | import | [init_cmd](../modules/init_cmd.md) | — |
| `status_cmd` | import | [status_cmd](../modules/status_cmd.md) | — |
| `upgrade_cmd` | import | [upgrade_cmd](../modules/upgrade_cmd.md) | — |
| `provision_wiki_scaffold` | call | [wiki_lifecycle](../modules/wiki_lifecycle.md) | 1 |
| `require_safe_wiki_scaffold` | call | [wiki_lifecycle](../modules/wiki_lifecycle.md) | 3 |
