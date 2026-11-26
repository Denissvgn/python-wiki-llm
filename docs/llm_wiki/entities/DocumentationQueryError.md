# DocumentationQueryError

**Location:** `src/llm_wiki_engine/query_request_format.py:30`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [query_request_format](../modules/query_request_format.md)

## Description

Raised when a documentation graph query request is invalid.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str = '', *, field: str \| None = None)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationQueryError (src/llm_wiki_engine/query_request_format.py)"]
    n1["ValueError"]
    n2["_attach_query_result_byte_bound (src/llm_wiki_cli/services/documentation_queries.py)"]
    n3["_fit_query_result (src/llm_wiki_cli/services/documentation_queries.py)"]
    n4["_normalise_source_path (src/llm_wiki_cli/services/documentation_queries.py)"]
    n5["_query_identity_within_limit (src/llm_wiki_cli/services/documentation_queries.py)"]
    n6["_require_query (src/llm_wiki_cli/services/documentation_queries.py)"]
    n7["_require_query_offset (src/llm_wiki_cli/services/documentation_queries.py)"]
    n8["_require_query_projection (src/llm_wiki_cli/services/documentation_queries.py)"]
    n9["DocumentationGraphQueryService.__init__ (src/llm_wiki_cli/services/documentation_queries.py)"]
    n10["DocumentationGraphQueryService._build_knowledge_indexes (src/llm_wiki_cli/services/documentation_queries.py)"]
    n11["DocumentationGraphQueryService._build_section_ownership_indexes (src/llm_wiki_cli/services/documentation_queries.py)"]
    n12["DocumentationGraphQueryService._build_typed_graph_indexes (src/llm_wiki_cli/services/documentation_queries.py)"]
    n13["DocumentationGraphQueryService._knowledge_direction (src/llm_wiki_cli/services/documentation_queries.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    n13 --> n0
    click n0 "../modules/query_request_format.md"
    click n2 "../modules/documentation_queries.md"
    click n3 "../modules/documentation_queries.md"
    click n4 "../modules/documentation_queries.md"
    click n5 "../modules/documentation_queries.md"
    click n6 "../modules/documentation_queries.md"
    click n7 "../modules/documentation_queries.md"
    click n8 "../modules/documentation_queries.md"
    click n9 "../modules/documentation_queries.md"
    click n10 "../modules/documentation_queries.md"
    click n11 "../modules/documentation_queries.md"
    click n12 "../modules/documentation_queries.md"
    click n13 "../modules/documentation_queries.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [query_request_format](../modules/query_request_format.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_attach_query_result_byte_bound` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_fit_query_result` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_normalise_source_path` | call | [documentation_queries](../modules/documentation_queries.md) | 5 |
| `_query_identity_within_limit` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_require_query` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_require_query_offset` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_require_query_projection` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `DocumentationGraphQueryService.__init__` | call | [documentation_queries](../modules/documentation_queries.md) | 4 |
| `DocumentationGraphQueryService._build_knowledge_indexes` | call | [documentation_queries](../modules/documentation_queries.md) | 6 |
| `DocumentationGraphQueryService._build_section_ownership_indexes` | call | [documentation_queries](../modules/documentation_queries.md) | 6 |
| `DocumentationGraphQueryService._build_typed_graph_indexes` | call | [documentation_queries](../modules/documentation_queries.md) | 3 |
| `DocumentationGraphQueryService._knowledge_direction` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |

> References: showing 12 of 32 logical references; 20 omitted by the 12-row generated summary limit.
