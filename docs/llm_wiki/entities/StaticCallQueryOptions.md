# _StaticCallQueryOptions

**Location:** `src/llm_wiki_cli/api_types.py:373`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

Additive captured-source coverage for static call queries.

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `coverage` | `dict[str, Any]` | *optional* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_StaticCallQueryOptions (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["CalleesResult (src/llm_wiki_cli/api_types.py)"]
    n3["CallersResult (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
    click n3 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `coverage` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
| Subclass | `CalleesResult` | [api_types](../modules/api_types.md) |
| Subclass | `CallersResult` | [api_types](../modules/api_types.md) |
