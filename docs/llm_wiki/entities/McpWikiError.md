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
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/mcp_server.md"
    click n2 "../modules/mcp_server.md"
    click n3 "../modules/mcp_server.md"
    click n4 "../modules/mcp_server.md"
    click n5 "../modules/mcp_server.md"
    click n6 "../modules/mcp_server.md"
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

| Reference | Kind | Source |
|---|---|---|
| `_api_mcp_error` | call | [mcp_server](../modules/mcp_server.md) |
| `_api_mcp_error` | type_reference | [mcp_server](../modules/mcp_server.md) |
| `_bounded_query_filter_values` | call | [mcp_server](../modules/mcp_server.md) |
| `_bounded_query_filter_values` | call | [mcp_server](../modules/mcp_server.md) |
| `_bounded_query_filter_values` | call | [mcp_server](../modules/mcp_server.md) |
| `_bounded_query_filter_values` | call | [mcp_server](../modules/mcp_server.md) |
| `_bounded_query_limit` | call | [mcp_server](../modules/mcp_server.md) |
| `_ensure_inside` | call | [mcp_server](../modules/mcp_server.md) |
| `_graph_query_args` | call | [mcp_server](../modules/mcp_server.md) |
| `_graph_query_args` | call | [mcp_server](../modules/mcp_server.md) |
| `_graph_query_args` | call | [mcp_server](../modules/mcp_server.md) |
| `_graph_query_args` | call | [mcp_server](../modules/mcp_server.md) |
