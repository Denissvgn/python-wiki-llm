# InstructionRoute

**Location:** `src/llm_wiki_cli/services/instruction_ownership.py:87`
**Kind:** Class
**Bases:** —
**Module:** [instruction_ownership](../modules/instruction_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Route that must occur in a particular rendered section.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `destination_path` | `str` | *required* | — |
| `source_heading` | `str` | *required* | — |
| `kind` | `InstructionRouteKind` | *required* | — |
| `literal` | `str \| None` | `None` | — |
| `profiles` | `tuple[SchemaRenderProfile, ...]` | `tuple(SchemaRenderProfile)` | — |
| `agent_targets` | `tuple[str, ...]` | `tuple(SCHEMA_FILENAMES)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InstructionRoute (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1["_correctness_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n2["_installed_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n3["_profiled_topic_routes (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n4["_profiled_workflow_routes (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n5["_topic_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n6["_workflow_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n7["route_exists (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/instruction_ownership.md"
    click n1 "../modules/instruction_ownership.md"
    click n2 "../modules/instruction_ownership.md"
    click n3 "../modules/instruction_ownership.md"
    click n4 "../modules/instruction_ownership.md"
    click n5 "../modules/instruction_ownership.md"
    click n6 "../modules/instruction_ownership.md"
    click n7 "../modules/instruction_ownership.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [instruction_ownership](../modules/instruction_ownership.md) | 0 | `agent_targets`, `destination_path`, `kind`, `literal`, `profiles`, `source_heading` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_correctness_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_installed_route` | call | [instruction_ownership](../modules/instruction_ownership.md) |
| `_installed_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_profiled_topic_routes` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_profiled_workflow_routes` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_topic_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_workflow_route` | call | [instruction_ownership](../modules/instruction_ownership.md) |
| `_workflow_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `route_exists` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
