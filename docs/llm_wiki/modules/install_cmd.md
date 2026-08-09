# install_cmd Module

**Path:** `src/llm_wiki_cli/commands/install_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/install_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `read_config`, `validate_path` |
| `..services.plugins` | `PluginError`, `install_plugin` |
| `..services.schema` | `refresh_skill_blocks` |
| `__future__` | `annotations` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/install_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/plugins.py"]
    n4["src/llm_wiki_cli/services/schema.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n3 --> n2
    n4 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/install_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/plugins.md"
    click n4 "../modules/services_schema.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [plugins](../modules/plugins.md) |
| Outbound | [services_schema](../modules/services_schema.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_component_summary` | `(plugin: dict) -> str` | — | — |
| `run` | `(args) -> None` | — | — |
