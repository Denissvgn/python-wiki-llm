# search_cmd Module

**Path:** `src/llm_wiki_cli/commands/search_cmd.py`

## Description

CLI access to the same read-only search service used by MCP.

## Imports

| Source | Symbols |
|--------|---------|
| `..api` | `search_wiki` |
| `..config` | `validate_path`, `validate_source_root` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/search_cmd.py"]
    n3["src/llm_wiki_cli/config.py"]
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n2 --> n0
    n2 --> n3
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/search_cmd.md"
    click n3 "../modules/config.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [api](../modules/api.md) |
| Outbound | [config](../modules/config.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |
