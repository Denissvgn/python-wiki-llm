# InvalidRequestError

**Location:** `src/llm_wiki_cli/api.py:332`
**Kind:** Class
**Bases:** `LlmWikiApiError`
**Module:** [api](../modules/api.md)

## Description

Raised when arguments or a submitted request contract are invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InvalidRequestError (src/llm_wiki_cli/api.py)"]
    n1["LlmWikiApiError (src/llm_wiki_cli/api.py)"]
    n2["_impact_query (src/llm_wiki_cli/api.py)"]
    n3["_normalize_optional_knowledge_mode (src/llm_wiki_cli/api.py)"]
    n4["_normalize_query_choice (src/llm_wiki_cli/api.py)"]
    n5["_normalize_query_input (src/llm_wiki_cli/api.py)"]
    n6["_normalize_query_values (src/llm_wiki_cli/api.py)"]
    n7["_query_service (src/llm_wiki_cli/api.py)"]
    n8["_raise_api_error (src/llm_wiki_cli/api.py)"]
    n9["_require_full_inventory_opt_in (src/llm_wiki_cli/api.py)"]
    n10["_run_query (src/llm_wiki_cli/api.py)"]
    n11["_validate_documentation_query_request (src/llm_wiki_cli/api.py)"]
    n12["bootstrap_wiki (src/llm_wiki_cli/api.py)"]
    n13["build_context (src/llm_wiki_cli/api.py)"]
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
    click n0 "../modules/api.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
    click n5 "../modules/api.md"
    click n6 "../modules/api.md"
    click n7 "../modules/api.md"
    click n8 "../modules/api.md"
    click n9 "../modules/api.md"
    click n10 "../modules/api.md"
    click n11 "../modules/api.md"
    click n12 "../modules/api.md"
    click n13 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api](../modules/api.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `LlmWikiApiError` | [api](../modules/api.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_impact_query` | call | [api](../modules/api.md) | 2 |
| `_normalize_optional_knowledge_mode` | call | [api](../modules/api.md) | 1 |
| `_normalize_query_choice` | call | [api](../modules/api.md) | 1 |
| `_normalize_query_input` | call | [api](../modules/api.md) | 1 |
| `_normalize_query_values` | call | [api](../modules/api.md) | 5 |
| `_query_service` | call | [api](../modules/api.md) | 1 |
| `_raise_api_error` | call | [api](../modules/api.md) | 3 |
| `_require_full_inventory_opt_in` | call | [api](../modules/api.md) | 2 |
| `_run_query` | call | [api](../modules/api.md) | 1 |
| `_validate_documentation_query_request` | call | [api](../modules/api.md) | 4 |
| `bootstrap_wiki` | call | [api](../modules/api.md) | 1 |
| `build_context` | call | [api](../modules/api.md) | 1 |

> References: showing 12 of 21 logical references; 9 omitted by the 12-row generated summary limit.
