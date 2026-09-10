# DocumentationRunError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:235`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Base error raised by the documentation lifecycle service.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["RuntimeError"]
    n2["DocumentationIntegrityError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["DocumentationSchemaError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n4["DocumentationTransitionError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n5["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run_contracts.md"
    click n4 "../modules/documentation_run_contracts.md"
    click n5 "../modules/documentation_run___init__.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |
| Subclass | `DocumentationIntegrityError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Subclass | `DocumentationSchemaError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Subclass | `DocumentationTransitionError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [documentation_run___init__](../modules/documentation_run___init__.md) | — |
