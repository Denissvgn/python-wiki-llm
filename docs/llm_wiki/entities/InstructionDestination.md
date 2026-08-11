# InstructionDestination

**Location:** `src/llm_wiki_cli/services/instruction_ownership.py:78`
**Kind:** Class
**Bases:** —
**Module:** [instruction_ownership](../modules/instruction_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Package-relative destination for content leaving generated prose.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str` | *required* | — |
| `heading` | `str \| None` | `None` | — |
| `anchor` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InstructionDestination (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1["_correctness_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n2["_installed_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n3["_skill (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n4["_topic (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n5["destination_exists (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n6["destination_is_packaged (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n7["inbound_route_resolves (src/llm_wiki_cli/services/instruction_ownership.py)"]
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
| [instruction_ownership](../modules/instruction_ownership.md) | 0 | `anchor`, `heading`, `path` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_correctness_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_installed_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_skill` | call | [instruction_ownership](../modules/instruction_ownership.md) |
| `_skill` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `_topic` | call | [instruction_ownership](../modules/instruction_ownership.md) |
| `_topic` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `destination_exists` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `destination_is_packaged` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `inbound_route_resolves` | call | [instruction_ownership](../modules/instruction_ownership.md) |
