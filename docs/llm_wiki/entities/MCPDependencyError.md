# MCPDependencyError

**Location:** `src/llm_wiki_cli/services/mcp_server.py:111`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [mcp_server](../modules/mcp_server.md)

## Description

Raised when the optional MCP runtime cannot be used.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MCPDependencyError (src/llm_wiki_cli/services/mcp_server.py)"]
    n1["RuntimeError"]
    n2["ensure_mcp_runtime (src/llm_wiki_cli/services/mcp_server.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/mcp_server.md"
    click n2 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [mcp_server](../modules/mcp_server.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `ensure_mcp_runtime` | call | [mcp_server](../modules/mcp_server.md) |
| `ensure_mcp_runtime` | call | [mcp_server](../modules/mcp_server.md) |
