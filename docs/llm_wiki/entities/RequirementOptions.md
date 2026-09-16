# _RequirementOptions

**Location:** `src/llm_wiki_cli/api_types.py:22`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

Optional observation criterion for a requirement. Present evidence and complete runtime behavior are distinct; incomplete static graphs cannot establish an unqualified negative.

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `criterion` | `Literal['present', 'complete']` | *optional* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_RequirementOptions (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["EvidenceRequirement (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `criterion` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
| Subclass | `EvidenceRequirement` | [api_types](../modules/api_types.md) |