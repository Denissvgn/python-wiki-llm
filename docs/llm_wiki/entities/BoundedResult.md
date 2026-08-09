# _BoundedResult

**Location:** `src/llm_wiki_cli/services/documentation_queries.py:71`
**Kind:** Class
**Bases:** —
**Module:** [documentation_queries](../modules/documentation_queries.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One deterministic collection plus its exact response bounds.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `items` | `list[Any]` | *required* | — |
| `total` | `int` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `returned` | `() -> int` | `@property` | — |
| `truncated` | `() -> bool` | `@property` | — |
| `metadata` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_BoundedResult (src/llm_wiki_cli/services/documentation_queries.py)"]
    n1["DocumentationGraphQueryService._bounded (src/llm_wiki_cli/services/documentation_queries.py)"]
    n2["DocumentationGraphQueryService._bounded_payload (src/llm_wiki_cli/services/documentation_queries.py)"]
    n3["DocumentationGraphQueryService._bounded_strings (src/llm_wiki_cli/services/documentation_queries.py)"]
    n4["DocumentationGraphQueryService._knowledge_selection_result (src/llm_wiki_cli/services/documentation_queries.py)"]
    n5["DocumentationGraphQueryService._pages_for_source (src/llm_wiki_cli/services/documentation_queries.py)"]
    n6["DocumentationGraphQueryService._record_bound (src/llm_wiki_cli/services/documentation_queries.py)"]
    n7["DocumentationGraphQueryService.list_concept_sections (src/llm_wiki_cli/services/documentation_queries.py)"]
    n8["DocumentationGraphQueryService.traverse_typed_graph (src/llm_wiki_cli/services/documentation_queries.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/documentation_queries.md"
    click n1 "../modules/documentation_queries.md"
    click n2 "../modules/documentation_queries.md"
    click n3 "../modules/documentation_queries.md"
    click n4 "../modules/documentation_queries.md"
    click n5 "../modules/documentation_queries.md"
    click n6 "../modules/documentation_queries.md"
    click n7 "../modules/documentation_queries.md"
    click n8 "../modules/documentation_queries.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_queries](../modules/documentation_queries.md) | 3 | `items`, `total` |

### References

| Reference | Kind | Source |
|---|---|---|
| `DocumentationGraphQueryService._bounded` | call | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._bounded` | type_reference | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._bounded_payload` | type_reference | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._bounded_strings` | call | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._bounded_strings` | type_reference | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._knowledge_selection_result` | call | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._pages_for_source` | type_reference | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService._record_bound` | type_reference | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService.list_concept_sections` | call | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService.list_concept_sections` | call | [documentation_queries](../modules/documentation_queries.md) |
| `DocumentationGraphQueryService.traverse_typed_graph` | call | [documentation_queries](../modules/documentation_queries.md) |
