# query_cmd Module

**Path:** `src/llm_wiki_cli/commands/query_cmd.py`

## Description

Adapts bounded file/stdin JSON to the supported exact documentation query API. Scope, provenance and response bounds are preserved. Invalid input and workspace failures retain distinct exits, and an output file is written only when explicitly requested.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `api` |
| `..services.io` | `write_text_output`, `write_utf8_stdout` |
| `..services.request_json` | `load_request` |
| `__future__` | `annotations` |
| `json` | `json` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/query_cmd.py"]
    n3["src/llm_wiki_cli/services/io.py"]
    n4["src/llm_wiki_cli/services/request_json.py"]
    n1 --> n2
    n2 --> n0
    n2 --> n3
    n2 --> n4
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/query_cmd.md"
    click n3 "../modules/io.md"
    click n4 "../modules/request_json.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [api](../modules/api.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [request_json](../modules/request_json.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |