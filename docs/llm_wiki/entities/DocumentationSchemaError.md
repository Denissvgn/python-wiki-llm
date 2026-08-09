# DocumentationSchemaError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:239`
**Kind:** Class
**Bases:** `DocumentationRunError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when a persisted or returned contract is invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationSchemaError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["DocumentationPersistedStateError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n4["DocumentationAgentResult.from_dict (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n5["DocumentationIntakeBrief.from_dict (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run___init__.md"
    click n4 "../modules/documentation_run_contracts.md"
    click n5 "../modules/documentation_run_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `DocumentationRunError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Subclass | `DocumentationPersistedStateError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `__init__` | import | [documentation_run___init__](../modules/documentation_run___init__.md) |
| `DocumentationAgentResult.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationAgentResult.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationAgentResult.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationAgentResult.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationAgentResult.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
