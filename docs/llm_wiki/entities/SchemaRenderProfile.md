# SchemaRenderProfile

**Location:** `src/llm_wiki_cli/services/schema.py:28`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [services_schema](../modules/services_schema.md)

## Description

Supported managed-schema rendering profiles.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `COMPACT` | `'compact'` | — |
| `EXPANDED_INLINE` | `'expanded_inline'` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SchemaRenderProfile (src/llm_wiki_cli/services/schema.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/init_cmd.py"]
    n4["_installed_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n5["_topic_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n6["_workflow_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n7["correctness_destination_ready (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n8["CorrectnessClauseCoverage.rendered_text (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n9["removal_prerequisites_ready (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n10["route_exists (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n11["src/llm_wiki_cli/services/rendering_lifecycle.py"]
    n12["_schema_profile_marker (src/llm_wiki_cli/services/schema.py)"]
    n13["build_schema_content (src/llm_wiki_cli/services/schema.py)"]
    n14["classify_managed_schema_block (src/llm_wiki_cli/services/schema.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    n13 --> n0
    n14 --> n0
    click n0 "../modules/services_schema.md"
    click n3 "../modules/init_cmd.md"
    click n4 "../modules/instruction_ownership.md"
    click n5 "../modules/instruction_ownership.md"
    click n6 "../modules/instruction_ownership.md"
    click n7 "../modules/instruction_ownership.md"
    click n8 "../modules/instruction_ownership.md"
    click n9 "../modules/instruction_ownership.md"
    click n10 "../modules/instruction_ownership.md"
    click n11 "../modules/rendering_lifecycle.md"
    click n12 "../modules/services_schema.md"
    click n13 "../modules/services_schema.md"
    click n14 "../modules/services_schema.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [services_schema](../modules/services_schema.md) | 0 | `COMPACT`, `EXPANDED_INLINE` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `init_cmd` | import | [init_cmd](../modules/init_cmd.md) | — |
| `_installed_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `_topic_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `_workflow_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `correctness_destination_ready` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `CorrectnessClauseCoverage.rendered_text` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `removal_prerequisites_ready` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `route_exists` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) | — |
| `rendering_lifecycle` | import | [rendering_lifecycle](../modules/rendering_lifecycle.md) | — |
| `_schema_profile_marker` | type_reference | [services_schema](../modules/services_schema.md) | — |
| `build_schema_content` | type_reference | [services_schema](../modules/services_schema.md) | — |
| `classify_managed_schema_block` | call | [services_schema](../modules/services_schema.md) | 1 |

> References: showing 12 of 18 logical references; 6 omitted by the 12-row generated summary limit.
