# maintenance_cmd Module

**Path:** `src/llm_wiki_cli/commands/maintenance_cmd.py`

## Description

CLI adapter for explicit ordinary maintenance review operations.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `api` |
| `..services.request_json` | `load_request` |
| `__future__` | `annotations` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/__init__.py"]
    n3["src/llm_wiki_cli/commands/maintenance_cmd.py"]
    n4["src/llm_wiki_cli/services/request_json.py"]
    n1 --> n3
    n2 --> n3
    n3 --> n0
    n3 --> n4
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/commands___init__.md"
    click n3 "../modules/maintenance_cmd.md"
    click n4 "../modules/request_json.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [commands___init__](../modules/commands___init__.md) |
| Outbound | [api](../modules/api.md) |
| Outbound | [request_json](../modules/request_json.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_capture_options` | `(args)` | — | — |
| `_render_status` | `(result)` | — | — |
| `run` | `(args) -> None` | — | — |
