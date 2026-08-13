# DocumentationQueryError

**Location:** `src/llm_wiki_cli/services/documentation_queries.py:128`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [documentation_queries](../modules/documentation_queries.md)

## Description

Raised when a documentation graph query request is invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationQueryError (src/llm_wiki_cli/services/documentation_queries.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/services/context_packet.py"]
    n4["src/llm_wiki_cli/services/context_service.py"]
    n5["src/llm_wiki_cli/services/documentation_claim_evidence.py"]
    n6["_attach_query_result_byte_bound (src/llm_wiki_cli/services/documentation_queries.py)"]
    n7["_fit_query_result (src/llm_wiki_cli/services/documentation_queries.py)"]
    n8["_normalise_source_path (src/llm_wiki_cli/services/documentation_queries.py)"]
    n9["_query_identity_within_limit (src/llm_wiki_cli/services/documentation_queries.py)"]
    n10["_require_query (src/llm_wiki_cli/services/documentation_queries.py)"]
    n11["DocumentationGraphQueryService.__init__ (src/llm_wiki_cli/services/documentation_queries.py)"]
    n12["DocumentationGraphQueryService._build_knowledge_indexes (src/llm_wiki_cli/services/documentation_queries.py)"]
    n13["DocumentationGraphQueryService._build_section_ownership_indexes (src/llm_wiki_cli/services/documentation_queries.py)"]
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
    click n0 "../modules/documentation_queries.md"
    click n2 "../modules/api.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/documentation_claim_evidence.md"
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
| [documentation_queries](../modules/documentation_queries.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `documentation_claim_evidence` | import | [documentation_claim_evidence](../modules/documentation_claim_evidence.md) | — |
| `_attach_query_result_byte_bound` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_fit_query_result` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_normalise_source_path` | call | [documentation_queries](../modules/documentation_queries.md) | 5 |
| `_query_identity_within_limit` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `_require_query` | call | [documentation_queries](../modules/documentation_queries.md) | 1 |
| `DocumentationGraphQueryService.__init__` | call | [documentation_queries](../modules/documentation_queries.md) | 3 |
| `DocumentationGraphQueryService._build_knowledge_indexes` | call | [documentation_queries](../modules/documentation_queries.md) | 6 |
| `DocumentationGraphQueryService._build_section_ownership_indexes` | call | [documentation_queries](../modules/documentation_queries.md) | 6 |

> References: showing 12 of 34 logical references; 22 omitted by the 12-row generated summary limit.
