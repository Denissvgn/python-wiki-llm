# _ExtractSourceRequired

**Location:** `src/llm_wiki_cli/api_types.py:14`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `_ExtractSourceRequired` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `schema_version` | `str` | *required* | — |
| `inventory` | `dict[str, dict[str, Any]]` | *required* | — |
| `data_flow_details` | `dict[str, Any]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ExtractSourceRequired (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["ExtractSourceResult (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `data_flow_details`, `inventory`, `schema_version` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
| Subclass | `ExtractSourceResult` | [api_types](../modules/api_types.md) |
