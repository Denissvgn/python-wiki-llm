# DocumentationWorklistError

**Location:** `src/llm_wiki_cli/services/documentation_worklist.py:132`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [documentation_worklist](../modules/documentation_worklist.md)

## Description

Raised when deterministic worklist inputs are invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationWorklistError (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n1["ValueError"]
    n2["_add_imported_page_candidates (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n3["_require_non_negative_int (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n4["_require_positive_int (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n5["build_documentation_worklist (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/documentation_worklist.md"
    click n2 "../modules/documentation_worklist.md"
    click n3 "../modules/documentation_worklist.md"
    click n4 "../modules/documentation_worklist.md"
    click n5 "../modules/documentation_worklist.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_worklist](../modules/documentation_worklist.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_add_imported_page_candidates` | call | [documentation_worklist](../modules/documentation_worklist.md) | 1 |
| `_require_non_negative_int` | call | [documentation_worklist](../modules/documentation_worklist.md) | 1 |
| `_require_positive_int` | call | [documentation_worklist](../modules/documentation_worklist.md) | 1 |
| `build_documentation_worklist` | call | [documentation_worklist](../modules/documentation_worklist.md) | 1 |
