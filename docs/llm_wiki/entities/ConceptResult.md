# ConceptResult

**Location:** `src/llm_wiki_cli/api_types.py:133`
**Kind:** Class
**Bases:** `_BoundedQueryResult`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `ConceptResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `knowledge` | `dict[str, Any]` | *required* | — |
| `concept` | `dict[str, Any] \| None` | *required* | — |
| `total` | `int` | *required* | — |
| `returned` | `int` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptResult (src/llm_wiki_cli/api_types.py)"]
    n1["_BoundedQueryResult (src/llm_wiki_cli/api_types.py)"]
    n2["ConceptSectionsResult (src/llm_wiki_cli/api_types.py)"]
    n3["EvidenceExplanationResult (src/llm_wiki_cli/api_types.py)"]
    n4["RelatedConceptsResult (src/llm_wiki_cli/api_types.py)"]
    n5["TypedGraphTraversalResult (src/llm_wiki_cli/api_types.py)"]
    n6["get_concept (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
    click n3 "../modules/api_types.md"
    click n4 "../modules/api_types.md"
    click n5 "../modules/api_types.md"
    click n6 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `concept`, `knowledge`, `returned`, `total` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_BoundedQueryResult` | [api_types](../modules/api_types.md) |
| Subclass | `ConceptSectionsResult` | [api_types](../modules/api_types.md) |
| Subclass | `EvidenceExplanationResult` | [api_types](../modules/api_types.md) |
| Subclass | `RelatedConceptsResult` | [api_types](../modules/api_types.md) |
| Subclass | `TypedGraphTraversalResult` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `get_concept` | type_reference | [api](../modules/api.md) |
