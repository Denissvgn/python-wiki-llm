# queue_cmd Module

**Path:** `src/llm_wiki_cli/commands/queue_cmd.py`

## Description

Read-only managed-wiki maintenance triage.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.maintenance_queue` | `build_maintenance_queue`, `render_queue` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/queue_cmd.py"]
    n2["src/llm_wiki_cli/services/maintenance_queue.py"]
    n0 --> n1
    n1 --> n2
    click n0 "../modules/cli.md"
    click n1 "../modules/queue_cmd.md"
    click n2 "../modules/maintenance_queue.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [maintenance_queue](../modules/maintenance_queue.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |
