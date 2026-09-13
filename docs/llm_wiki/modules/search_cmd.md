# search_cmd Module

**Path:** `src/llm_wiki_cli/commands/search_cmd.py`

## Description

CLI access to the same read-only search service used by MCP.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `validate_path`, `validate_source_root` |
| `..services.mcp_server` | `McpWikiService` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/search_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/mcp_server.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n3 --> n2
    click n0 "../modules/cli.md"
    click n1 "../modules/search_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/mcp_server.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [mcp_server](../modules/mcp_server.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |
