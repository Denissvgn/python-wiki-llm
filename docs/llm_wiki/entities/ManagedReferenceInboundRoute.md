# ManagedReferenceInboundRoute

**Location:** `src/llm_wiki_cli/services/instruction_ownership.py:142`
**Kind:** Class
**Bases:** —
**Module:** [instruction_ownership](../modules/instruction_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One active source route into a managed reference topic.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source_path` | `str` | *required* | — |
| `source_text` | `str` | *required* | — |
| `kind` | `InboundRouteKind` | *required* | — |
| `destination_path` | `str` | *required* | — |
| `destination_heading` | `str` | *required* | — |
| `destination_anchor` | `str` | *required* | — |
| `markdown_target` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManagedReferenceInboundRoute (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1["_managed_topic_route (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n2["inbound_route_resolves (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/instruction_ownership.md"
    click n1 "../modules/instruction_ownership.md"
    click n2 "../modules/instruction_ownership.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [instruction_ownership](../modules/instruction_ownership.md) | 0 | `destination_anchor`, `destination_heading`, `destination_path`, `kind`, `markdown_target`, `source_path`, `source_text` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_managed_topic_route` | call | [instruction_ownership](../modules/instruction_ownership.md) |
| `_managed_topic_route` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `inbound_route_resolves` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
