# RelatedConceptsResult

**Location:** `src/llm_wiki_cli/api_types.py:222`
**Kind:** Class
**Bases:** `ConceptResult`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `RelatedConceptsResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `direction` | `str` | *required* | — |
| `kinds` | `list[str]` | *required* | — |
| `relationships` | `list[dict[str, Any]]` | *required* | — |
| `related_concepts` | `list[dict[str, Any]]` | *required* | — |
| `unresolved_targets` | `list[dict[str, Any]]` | *required* | — |
| `external_targets` | `list[dict[str, Any]]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["RelatedConceptsResult (src/llm_wiki_cli/api_types.py)"]
    n1["ConceptResult (src/llm_wiki_cli/api_types.py)"]
    n2["related_concepts (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `direction`, `external_targets`, `kinds`, `related_concepts`, `relationships`, `unresolved_targets` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ConceptResult` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `related_concepts` | type_reference | [api](../modules/api.md) |
