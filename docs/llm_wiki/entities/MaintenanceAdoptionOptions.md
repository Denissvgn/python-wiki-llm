# _MaintenanceAdoptionOptions

**Location:** `src/llm_wiki_cli/api_types.py:141`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `_MaintenanceAdoptionOptions` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `already_adopted` | `bool` | *optional* | — |
| `records` | `int` | *optional* | — |
| `state_hash` | `str` | *optional* | — |
| `coverage` | `dict[str, Any]` | *optional* | — |
| `recovery_dir` | `str` | *optional* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_MaintenanceAdoptionOptions (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["MaintenanceAdoptionResult (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `already_adopted`, `coverage`, `records`, `recovery_dir`, `state_hash` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
| Subclass | `MaintenanceAdoptionResult` | [api_types](../modules/api_types.md) |
