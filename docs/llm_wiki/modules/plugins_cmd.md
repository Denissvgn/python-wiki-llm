# plugins_cmd Module

**Path:** `src/llm_wiki_cli/commands/plugins_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/plugins_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path` |
| `..services.plugin_samples` | `export_sample`, `list_samples` |
| `..services.plugins` | `PluginError`, `list_plugins`, `remove_plugin`, `validate_plugin` |
| `..services.schema` | `strip_plugin_skill_blocks` |
| `__future__` | `annotations` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/plugins_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/plugin_samples.py"]
    n4["src/llm_wiki_cli/services/plugins.py"]
    n5["src/llm_wiki_cli/services/schema.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n3 --> n4
    n4 --> n2
    n5 --> n4
    click n0 "../modules/cli.md"
    click n1 "../modules/plugins_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/plugin_samples.md"
    click n4 "../modules/plugins.md"
    click n5 "../modules/services_schema.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [plugin_samples](../modules/plugin_samples.md) |
| Outbound | [plugins](../modules/plugins.md) |
| Outbound | [services_schema](../modules/services_schema.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_render_components` | `(plugin: dict) -> str` | — | — |
| `run` | `(args) -> None` | — | — |
