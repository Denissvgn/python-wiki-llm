# DocumentationPersistedStateError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:251`
**Kind:** Class
**Bases:** `DocumentationIntegrityError`, `DocumentationSchemaError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when a stored documentation-run contract is corrupt.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationPersistedStateError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationIntegrityError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["DocumentationSchemaError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["load_documentation_run (src/llm_wiki_cli/services/documentation_run/workspace.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/workspace.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `DocumentationIntegrityError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Base | `DocumentationSchemaError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `load_documentation_run` | call | [workspace](../modules/workspace.md) | 3 |
