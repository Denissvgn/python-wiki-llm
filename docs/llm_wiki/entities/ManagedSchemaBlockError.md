# ManagedSchemaBlockError

**Location:** `src/llm_wiki_cli/services/schema.py:49`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [services_schema](../modules/services_schema.md)

## Description

Raised when a malformed managed block cannot be replaced safely.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManagedSchemaBlockError (src/llm_wiki_cli/services/schema.py)"]
    n1["ValueError"]
    n2["_managed_schema_agents (src/llm_wiki_cli/commands/init_cmd.py)"]
    n3["run (src/llm_wiki_cli/commands/init_cmd.py)"]
    n4["_preflight_agent_schemas (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n5["_validate_schema_plan (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n6["_clean_old_schema (src/llm_wiki_cli/commands/upgrade_cmd.py)"]
    n7["_require_replaceable_schema_path (src/llm_wiki_cli/commands/upgrade_cmd.py)"]
    n8["require_managed_schema_profile (src/llm_wiki_cli/services/schema.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/services_schema.md"
    click n2 "../modules/init_cmd.md"
    click n3 "../modules/init_cmd.md"
    click n4 "../modules/uninstall_cmd.md"
    click n5 "../modules/uninstall_cmd.md"
    click n6 "../modules/upgrade_cmd.md"
    click n7 "../modules/upgrade_cmd.md"
    click n8 "../modules/services_schema.md"
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

| Reference | Kind | Source |
|---|---|---|
| `_managed_schema_agents` | call | [init_cmd](../modules/init_cmd.md) |
| `run` | call | [init_cmd](../modules/init_cmd.md) |
| `run` | call | [init_cmd](../modules/init_cmd.md) |
| `run` | call | [init_cmd](../modules/init_cmd.md) |
| `run` | call | [init_cmd](../modules/init_cmd.md) |
| `_preflight_agent_schemas` | call | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_preflight_agent_schemas` | call | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_validate_schema_plan` | call | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_validate_schema_plan` | call | [uninstall_cmd](../modules/uninstall_cmd.md) |
| `_clean_old_schema` | call | [upgrade_cmd](../modules/upgrade_cmd.md) |
| `_require_replaceable_schema_path` | call | [upgrade_cmd](../modules/upgrade_cmd.md) |
| `require_managed_schema_profile` | call | [services_schema](../modules/services_schema.md) |
