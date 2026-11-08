# DocumentationTransitionError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:306`
**Kind:** Class
**Bases:** `DocumentationRunError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when a stage transition violates the lifecycle graph.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationTransitionError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n3["_bind_publication (src/llm_wiki_cli/services/documentation_run/publication.py)"]
    n4["bind_publication_workspace (src/llm_wiki_cli/services/documentation_run/publication.py)"]
    n5["reconcile_publication (src/llm_wiki_cli/services/documentation_run/publication.py)"]
    n6["reviewed_publication (src/llm_wiki_cli/services/documentation_run/publication.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run___init__.md"
    click n3 "../modules/publication.md"
    click n4 "../modules/publication.md"
    click n5 "../modules/publication.md"
    click n6 "../modules/publication.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `DocumentationRunError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [documentation_run___init__](../modules/documentation_run___init__.md) | — |
| `_bind_publication` | call | [publication](../modules/publication.md) | 2 |
| `bind_publication_workspace` | call | [publication](../modules/publication.md) | 1 |
| `reconcile_publication` | call | [publication](../modules/publication.md) | 5 |
| `reviewed_publication` | call | [publication](../modules/publication.md) | 2 |
