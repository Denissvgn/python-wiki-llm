# DocumentationIntegrityError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:247`
**Kind:** Class
**Bases:** `DocumentationRunError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when source, input-wiki, or generated ownership changed.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationIntegrityError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["DocumentationPersistedStateError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n4["_remove_built_site_before_builder (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n5["_run_authorized_builder (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n6["export_documentation_run (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run___init__.md"
    click n4 "../modules/export.md"
    click n5 "../modules/export.md"
    click n6 "../modules/export.md"
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
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) |
| `_run_authorized_builder` | call | [export](../modules/export.md) |
| `export_documentation_run` | call | [export](../modules/export.md) |
| `export_documentation_run` | call | [export](../modules/export.md) |
| `export_documentation_run` | call | [export](../modules/export.md) |
