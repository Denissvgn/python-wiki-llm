# maintenance_cmd Module

**Path:** `src/llm_wiki_cli/commands/maintenance_cmd.py`

## Description

CLI adapter for explicit ordinary maintenance review operations.

The separate `recover-new-pages` action validates the wiki inside the current
project, then forwards the rejection-bound hash and preview/apply option to the
new-page recovery service. Its recovery directory stays outside the wiki.
Adoption, status, acknowledgment and complete authority recovery retain their
existing API routes; removing new pages never acknowledges prose or repairs
missing authority.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `api` |
| `..config` | `validate_path` |
| `..services.request_json` | `load_request` |
| `..services.sync_recovery` | `recover_new_sync_pages` |
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
    n4["src/llm_wiki_cli/config.py"]
    n5["src/llm_wiki_cli/services/request_json.py"]
    n6["src/llm_wiki_cli/services/sync_recovery.py"]
    n0 --> n4
    n1 --> n3
    n1 --> n4
    n2 --> n3
    n3 --> n0
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n6 --> n5
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/commands___init__.md"
    click n3 "../modules/maintenance_cmd.md"
    click n4 "../modules/config.md"
    click n5 "../modules/request_json.md"
    click n6 "../modules/sync_recovery.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [commands___init__](../modules/commands___init__.md) |
| Outbound | [api](../modules/api.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [request_json](../modules/request_json.md) |
| Outbound | [sync_recovery](../modules/sync_recovery.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_capture_options` | `(args)` | — | — |
| `_render_status` | `(result)` | — | — |
| `run` | `(args) -> None` | — | — |
