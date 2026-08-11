# ManagedSchemaBlock

**Location:** `src/llm_wiki_cli/services/schema.py:54`
**Kind:** Class
**Bases:** —
**Module:** [services_schema](../modules/services_schema.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Parsed metadata for a managed schema block without health inference.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `ManagedSchemaBlockState` | *required* | — |
| `profile` | `SchemaRenderProfile \| None` | `None` | — |
| `version` | `int \| None` | `None` | — |
| `raw_profile` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManagedSchemaBlock (src/llm_wiki_cli/services/schema.py)"]
    n1["_diagnostic_schema_target (src/llm_wiki_cli/commands/status_cmd.py)"]
    n2["_managed_schema_candidates (src/llm_wiki_cli/commands/status_cmd.py)"]
    n3["_read_managed_schema (src/llm_wiki_cli/commands/status_cmd.py)"]
    n4["classify_lifecycle_status (src/llm_wiki_cli/services/rendering_lifecycle.py)"]
    n5["classify_managed_schema_block (src/llm_wiki_cli/services/schema.py)"]
    n6["require_managed_schema_profile (src/llm_wiki_cli/services/schema.py)"]
    n7["require_replaceable_managed_schema (src/llm_wiki_cli/services/schema.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/services_schema.md"
    click n1 "../modules/status_cmd.md"
    click n2 "../modules/status_cmd.md"
    click n3 "../modules/status_cmd.md"
    click n4 "../modules/rendering_lifecycle.md"
    click n5 "../modules/services_schema.md"
    click n6 "../modules/services_schema.md"
    click n7 "../modules/services_schema.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [services_schema](../modules/services_schema.md) | 0 | `profile`, `raw_profile`, `state`, `version` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_diagnostic_schema_target` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_managed_schema_candidates` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_read_managed_schema` | call | [status_cmd](../modules/status_cmd.md) | 4 |
| `_read_managed_schema` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `classify_lifecycle_status` | type_reference | [rendering_lifecycle](../modules/rendering_lifecycle.md) | — |
| `classify_managed_schema_block` | call | [services_schema](../modules/services_schema.md) | 9 |
| `classify_managed_schema_block` | type_reference | [services_schema](../modules/services_schema.md) | — |
| `require_managed_schema_profile` | type_reference | [services_schema](../modules/services_schema.md) | — |
| `require_replaceable_managed_schema` | type_reference | [services_schema](../modules/services_schema.md) | — |
