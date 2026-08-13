# McpWikiError

**Location:** `src/llm_wiki_cli/services/mcp_server.py:115`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [mcp_server](../modules/mcp_server.md)

## Description

Raised for invalid MCP wiki requests.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, *, code: str \| None = None, data: Mapping[str, Any] \| None = None) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["McpWikiError (src/llm_wiki_cli/services/mcp_server.py)"]
    n1["ValueError"]
    n2["_api_mcp_error (src/llm_wiki_cli/services/mcp_server.py)"]
    n3["_bounded_query_filter_values (src/llm_wiki_cli/services/mcp_server.py)"]
    n4["_bounded_query_limit (src/llm_wiki_cli/services/mcp_server.py)"]
    n5["_ensure_inside (src/llm_wiki_cli/services/mcp_server.py)"]
    n6["_graph_query_args (src/llm_wiki_cli/services/mcp_server.py)"]
    n7["_knowledge_direction (src/llm_wiki_cli/services/mcp_server.py)"]
    n8["_knowledge_kinds (src/llm_wiki_cli/services/mcp_server.py)"]
    n9["_knowledge_locator (src/llm_wiki_cli/services/mcp_server.py)"]
    n10["_normalise_origin (src/llm_wiki_cli/services/mcp_server.py)"]
    n11["_normalise_source_path (src/llm_wiki_cli/services/mcp_server.py)"]
    n12["_normalize_knowledge_mode (src/llm_wiki_cli/services/mcp_server.py)"]
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
    click n0 "../modules/mcp_server.md"
    click n2 "../modules/mcp_server.md"
    click n3 "../modules/mcp_server.md"
    click n4 "../modules/mcp_server.md"
    click n5 "../modules/mcp_server.md"
    click n6 "../modules/mcp_server.md"
    click n7 "../modules/mcp_server.md"
    click n8 "../modules/mcp_server.md"
    click n9 "../modules/mcp_server.md"
    click n10 "../modules/mcp_server.md"
    click n11 "../modules/mcp_server.md"
    click n12 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [mcp_server](../modules/mcp_server.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_api_mcp_error` | call | [mcp_server](../modules/mcp_server.md) | 1 |
| `_api_mcp_error` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `_bounded_query_filter_values` | call | [mcp_server](../modules/mcp_server.md) | 4 |
| `_bounded_query_limit` | call | [mcp_server](../modules/mcp_server.md) | 1 |
| `_ensure_inside` | call | [mcp_server](../modules/mcp_server.md) | 1 |
| `_graph_query_args` | call | [mcp_server](../modules/mcp_server.md) | 5 |
| `_knowledge_direction` | call | [mcp_server](../modules/mcp_server.md) | 1 |
| `_knowledge_kinds` | call | [mcp_server](../modules/mcp_server.md) | 1 |
| `_knowledge_locator` | call | [mcp_server](../modules/mcp_server.md) | 2 |
| `_normalise_origin` | call | [mcp_server](../modules/mcp_server.md) | 3 |
| `_normalise_source_path` | call | [mcp_server](../modules/mcp_server.md) | 1 |
| `_normalize_knowledge_mode` | call | [mcp_server](../modules/mcp_server.md) | 1 |

> References: showing 12 of 39 logical references; 27 omitted by the 12-row generated summary limit.
