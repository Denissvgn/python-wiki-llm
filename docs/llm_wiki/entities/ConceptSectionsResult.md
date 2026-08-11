# ConceptSectionsResult

**Location:** `src/llm_wiki_cli/api_types.py:216`
**Kind:** Class
**Bases:** `ConceptResult`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `ConceptSectionsResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `section_ownership` | `dict[str, Any]` | *required* | — |
| `ownership` | `str \| None` | *required* | — |
| `sections` | `list[dict[str, Any]]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptSectionsResult (src/llm_wiki_cli/api_types.py)"]
    n1["ConceptResult (src/llm_wiki_cli/api_types.py)"]
    n2["list_concept_sections (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `ownership`, `section_ownership`, `sections` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ConceptResult` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `list_concept_sections` | type_reference | [api](../modules/api.md) |
