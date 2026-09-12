# api_diff_cmd Module

**Path:** `src/llm_wiki_cli/commands/api_diff_cmd.py`

## Description

Compare supplied local OpenAPI exports without invoking target code.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `validate_source_root` |
| `..services.api_diff` | `compare_openapi`, `render_markdown` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/api_diff_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/api_diff.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/api_diff_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/api_diff.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [api_diff](../modules/api_diff.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |
