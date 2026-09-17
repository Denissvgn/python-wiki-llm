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
    n0["src/llm_wiki_cli/commands/query_cmd.py"]
    n1["src/llm_wiki_cli/commands/task_cmd.py"]
    n2["src/llm_wiki_cli/services/context_budget.py"]
    n3["src/llm_wiki_cli/services/request_json.py"]
    n4["src/llm_wiki_cli/services/task_context.py"]
    n5["src/llm_wiki_cli/services/workflow_profile.py"]
    n0 --> n3
    n1 --> n3
    n2 --> n3
    n4 --> n2
    n4 --> n3
    n4 --> n5
    n5 --> n3
    click n0 "../modules/query_cmd.md"
    click n1 "../modules/task_cmd.md"
    click n2 "../modules/context_budget.md"
    click n3 "../modules/request_json.md"
    click n4 "../modules/task_context.md"
    click n5 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [query_cmd](../modules/query_cmd.md) |
| Inbound | [task_cmd](../modules/task_cmd.md) |
| Inbound | [context_budget](../modules/context_budget.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [workflow_profile](../modules/workflow_profile.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_pairs` | `(items)` | — | — |
| `_constant` | `(value)` | — | — |
| `parse_request` | `(raw: bytes \| str) -> dict[str, Any]` | — | — |
| `load_request` | `(path: str) -> dict[str, Any]` | — | — |