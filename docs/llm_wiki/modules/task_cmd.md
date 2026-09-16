# task_cmd Module

**Path:** `src/llm_wiki_cli/commands/task_cmd.py`

## Description

Adapts explicit task requests and optional profiles to canonical task context. Workspace roots, counter configuration and full-inventory permission are operator options. A response that cannot fit emits no partial context, and read proposals remain data for the host to consider.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `api` |
| `..services.io` | `write_text_output`, `write_utf8_stdout` |
| `..services.request_json` | `load_request` |
| `..services.token_counting` | `LocalTokenizerCounter` |
| `json` | `json` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/task_cmd.py"]
    n3["src/llm_wiki_cli/services/io.py"]
    n4["src/llm_wiki_cli/services/request_json.py"]
    n5["src/llm_wiki_cli/services/token_counting.py"]
    n0 --> n5
    n1 --> n2
    n2 --> n0
    n2 --> n3
    n2 --> n4
    n2 --> n5
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/task_cmd.md"
    click n3 "../modules/io.md"
    click n4 "../modules/request_json.md"
    click n5 "../modules/token_counting.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [api](../modules/api.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [request_json](../modules/request_json.md) |
| Outbound | [token_counting](../modules/token_counting.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |