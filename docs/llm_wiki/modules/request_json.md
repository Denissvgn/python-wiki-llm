# request_json Module

**Path:** `src/llm_wiki_cli/services/request_json.py`

## Description

Loads explicit JSON request files or stdin under a one-mebibyte UTF-8 bound. Duplicate keys, nonfinite numbers, malformed text and non-object requests fail before the request reaches workspace readers.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `json` | `json` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/maintenance_cmd.py"]
    n1["src/llm_wiki_cli/commands/query_cmd.py"]
    n2["src/llm_wiki_cli/commands/task_cmd.py"]
    n3["src/llm_wiki_cli/services/context_budget.py"]
    n4["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n5["src/llm_wiki_cli/services/maintenance_service.py"]
    n6["src/llm_wiki_cli/services/mcp_server.py"]
    n7["src/llm_wiki_cli/services/request_json.py"]
    n8["src/llm_wiki_cli/services/sync_recovery.py"]
    n9["src/llm_wiki_cli/services/task_compact.py"]
    n10["src/llm_wiki_cli/services/task_context.py"]
    n11["src/llm_wiki_cli/services/workflow_profile.py"]
    n0 --> n7
    n0 --> n8
    n1 --> n7
    n2 --> n7
    n3 --> n7
    n4 --> n7
    n5 --> n4
    n5 --> n7
    n6 --> n3
    n6 --> n7
    n6 --> n10
    n6 --> n11
    n8 --> n4
    n8 --> n7
    n9 --> n3
    n9 --> n7
    n9 --> n10
    n9 --> n11
    n10 --> n3
    n10 --> n7
    n10 --> n11
    n11 --> n7
    click n0 "../modules/maintenance_cmd.md"
    click n1 "../modules/query_cmd.md"
    click n2 "../modules/task_cmd.md"
    click n3 "../modules/context_budget.md"
    click n4 "../modules/maintenance_protocol.md"
    click n5 "../modules/maintenance_service.md"
    click n6 "../modules/mcp_server.md"
    click n7 "../modules/request_json.md"
    click n8 "../modules/sync_recovery.md"
    click n9 "../modules/task_compact.md"
    click n10 "../modules/task_context.md"
    click n11 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [maintenance_cmd](../modules/maintenance_cmd.md) |
| Inbound | [query_cmd](../modules/query_cmd.md) |
| Inbound | [task_cmd](../modules/task_cmd.md) |
| Inbound | [context_budget](../modules/context_budget.md) |
| Inbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Inbound | [maintenance_service](../modules/maintenance_service.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Inbound | [sync_recovery](../modules/sync_recovery.md) |
| Inbound | [task_compact](../modules/task_compact.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [workflow_profile](../modules/workflow_profile.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_pairs` | `(items)` | — | — |
| `_constant` | `(value)` | — | — |
| `parse_request` | `(raw: bytes \| str) -> dict[str, Any]` | — | — |
| `load_request` | `(path: str) -> dict[str, Any]` | — | — |