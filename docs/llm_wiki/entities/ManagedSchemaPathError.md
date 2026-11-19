# ManagedSchemaPathError

**Location:** `src/llm_wiki_cli/services/schema.py:46`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [services_schema](../modules/services_schema.md)

## Description

Raised when a managed schema path cannot be accessed safely.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManagedSchemaPathError (src/llm_wiki_cli/services/schema.py)"]
    n1["ValueError"]
    n2["_managed_schema_agents (src/llm_wiki_cli/commands/init_cmd.py)"]
    n3["run (src/llm_wiki_cli/commands/init_cmd.py)"]
    n4["_clean_agent_schemas (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n5["_preflight_agent_schemas (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n6["require_safe_schema_path (src/llm_wiki_cli/services/schema.py)"]
    n7["_clean_old_schema (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n8["_require_replaceable_schema_path (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n9["_restore_old_schema (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n10["_upgrade_schema (src/llm_wiki_cli/services/upgrade_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    click n0 "../modules/services_schema.md"
    click n2 "../modules/init_cmd.md"
    click n3 "../modules/init_cmd.md"
    click n4 "../modules/uninstall_cmd.md"
    click n5 "../modules/uninstall_cmd.md"
    click n6 "../modules/services_schema.md"
    click n7 "../modules/upgrade_runtime.md"
    click n8 "../modules/upgrade_runtime.md"
    click n9 "../modules/upgrade_runtime.md"
    click n10 "../modules/upgrade_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [services_schema](../modules/services_schema.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_managed_schema_agents` | call | [init_cmd](../modules/init_cmd.md) | 1 |
| `run` | call | [init_cmd](../modules/init_cmd.md) | 4 |
| `_clean_agent_schemas` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_preflight_agent_schemas` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 2 |
| `require_safe_schema_path` | call | [services_schema](../modules/services_schema.md) | 2 |
| `_clean_old_schema` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 1 |
| `_require_replaceable_schema_path` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 1 |
| `_restore_old_schema` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 1 |
| `_upgrade_schema` | call | [upgrade_runtime](../modules/upgrade_runtime.md) | 1 |
