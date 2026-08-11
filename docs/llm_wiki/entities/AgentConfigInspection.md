# AgentConfigInspection

**Location:** `src/llm_wiki_cli/config.py:323`
**Kind:** Class
**Bases:** —
**Module:** [config](../modules/config.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One safe configuration read with provenance for status reporting.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `AgentConfigState` | *required* | — |
| `reason` | `str` | *required* | — |
| `path` | `Path` | *required* | — |
| `data` | `dict[str, object]` | *required* | — |
| `raw_bytes` | `bytes \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["AgentConfigInspection (src/llm_wiki_cli/config.py)"]
    n1["_configured_agent (src/llm_wiki_cli/commands/status_cmd.py)"]
    n2["_diagnostic_schema_target (src/llm_wiki_cli/commands/status_cmd.py)"]
    n3["_print_managed_lifecycle (src/llm_wiki_cli/commands/status_cmd.py)"]
    n4["_resolve_agent (src/llm_wiki_cli/commands/upgrade_cmd.py)"]
    n5["config_requires_manual_recovery (src/llm_wiki_cli/config.py)"]
    n6["inspect_config (src/llm_wiki_cli/config.py)"]
    n7["inspect_config_path (src/llm_wiki_cli/config.py)"]
    n8["require_config_inspection_unchanged (src/llm_wiki_cli/config.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/config.md"
    click n1 "../modules/status_cmd.md"
    click n2 "../modules/status_cmd.md"
    click n3 "../modules/status_cmd.md"
    click n4 "../modules/upgrade_cmd.md"
    click n5 "../modules/config.md"
    click n6 "../modules/config.md"
    click n7 "../modules/config.md"
    click n8 "../modules/config.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [config](../modules/config.md) | 0 | `data`, `path`, `raw_bytes`, `reason`, `state` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_configured_agent` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_diagnostic_schema_target` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_print_managed_lifecycle` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_resolve_agent` | type_reference | [upgrade_cmd](../modules/upgrade_cmd.md) | — |
| `config_requires_manual_recovery` | type_reference | [config](../modules/config.md) | — |
| `inspect_config` | call | [config](../modules/config.md) | 1 |
| `inspect_config` | type_reference | [config](../modules/config.md) | — |
| `inspect_config_path` | call | [config](../modules/config.md) | 10 |
| `inspect_config_path` | type_reference | [config](../modules/config.md) | — |
| `require_config_inspection_unchanged` | type_reference | [config](../modules/config.md) | — |
