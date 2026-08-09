# PluginError

**Location:** `src/llm_wiki_cli/services/plugins.py:56`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [plugins](../modules/plugins.md)

## Description

Raised when a plugin manifest, install, or lookup is invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PluginError (src/llm_wiki_cli/services/plugins.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/generate_prompt_cmd.py"]
    n3["src/llm_wiki_cli/commands/install_cmd.py"]
    n4["src/llm_wiki_cli/commands/plugins_cmd.py"]
    n5["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n6["_normalize_category_colors (src/llm_wiki_cli/services/diagrams.py)"]
    n7["_normalize_node_classes (src/llm_wiki_cli/services/diagrams.py)"]
    n8["_normalize_style (src/llm_wiki_cli/services/diagrams.py)"]
    n9["_plugin_error (src/llm_wiki_cli/services/entrypoints.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/plugins.md"
    click n2 "../modules/generate_prompt_cmd.md"
    click n3 "../modules/install_cmd.md"
    click n4 "../modules/plugins_cmd.md"
    click n5 "../modules/trigger_cmd.md"
    click n6 "../modules/diagrams.md"
    click n7 "../modules/diagrams.md"
    click n8 "../modules/diagrams.md"
    click n9 "../modules/entrypoints.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [plugins](../modules/plugins.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `generate_prompt_cmd` | import | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) |
| `install_cmd` | import | [install_cmd](../modules/install_cmd.md) |
| `plugins_cmd` | import | [plugins_cmd](../modules/plugins_cmd.md) |
| `trigger_cmd` | import | [trigger_cmd](../modules/trigger_cmd.md) |
| `_normalize_category_colors` | call | [diagrams](../modules/diagrams.md) |
| `_normalize_category_colors` | call | [diagrams](../modules/diagrams.md) |
| `_normalize_node_classes` | call | [diagrams](../modules/diagrams.md) |
| `_normalize_node_classes` | call | [diagrams](../modules/diagrams.md) |
| `_normalize_style` | call | [diagrams](../modules/diagrams.md) |
| `_normalize_style` | call | [diagrams](../modules/diagrams.md) |
| `_plugin_error` | call | [entrypoints](../modules/entrypoints.md) |
| `_plugin_error` | type_reference | [entrypoints](../modules/entrypoints.md) |
