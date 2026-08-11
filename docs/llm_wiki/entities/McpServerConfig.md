# McpServerConfig

**Location:** `src/llm_wiki_cli/services/mcp_server.py:241`
**Kind:** Class
**Bases:** —
**Module:** [mcp_server](../modules/mcp_server.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `McpServerConfig` in `src/llm_wiki_cli/services/mcp_server.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `src_dir` | `str` | `'.'` | — |
| `wiki_dir` | `str` | `'docs/llm_wiki'` | — |
| `transport` | `str` | `'stdio'` | — |
| `host` | `str` | `'127.0.0.1'` | — |
| `port` | `int` | `8765` | — |
| `path` | `str` | `'/mcp'` | — |
| `allowed_origins` | `tuple[str, ...]` | `field(default_factory=tuple)` | — |
| `source_selection` | `str \| None` | `None` | — |
| `allow_external_src` | `bool` | `False` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["McpServerConfig (src/llm_wiki_cli/services/mcp_server.py)"]
    n1["create_mcp_server (src/llm_wiki_cli/services/mcp_server.py)"]
    n2["run_mcp_server (src/llm_wiki_cli/services/mcp_server.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/mcp_server.md"
    click n1 "../modules/mcp_server.md"
    click n2 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [mcp_server](../modules/mcp_server.md) | 0 | `allow_external_src`, `allowed_origins`, `host`, `path`, `port`, `source_selection`, `src_dir`, `transport`, `wiki_dir` |

### References

| Reference | Kind | Source |
|---|---|---|
| `create_mcp_server` | type_reference | [mcp_server](../modules/mcp_server.md) |
| `run_mcp_server` | type_reference | [mcp_server](../modules/mcp_server.md) |
