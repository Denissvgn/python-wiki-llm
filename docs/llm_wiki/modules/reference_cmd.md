# reference_cmd Module

**Path:** `src/llm_wiki_cli/commands/reference_cmd.py`

## Description

Generate or render stable command reference data.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.cli_reference` | `MAX_CLI_CONTRACT_BYTES`, `get_cli_contract`, `load_cli_contract`, `render_cli_reference` |
| `..services.filesystem_guard` | `atomic_write_private_bytes`, `ensure_guarded_directory` |
| `..services.knowledge_storage_io` | `StorageReadSession`, `_absolute_path` |
| `__future__` | `annotations` |
| `json` | `json` |
| `pathlib` | `Path` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/reference_cmd.py"]
    n2["src/llm_wiki_cli/services/cli_reference.py"]
    n3["src/llm_wiki_cli/services/filesystem_guard.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n0 --> n1
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n2 --> n0
    n2 --> n4
    n4 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/reference_cmd.md"
    click n2 "../modules/cli_reference.md"
    click n3 "../modules/filesystem_guard.md"
    click n4 "../modules/knowledge_storage_io.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [cli_reference](../modules/cli_reference.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `add_commands` | `(subparsers)` | — | — |
| `run` | `(args)` | — | — |
