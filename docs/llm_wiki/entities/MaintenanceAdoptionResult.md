# MaintenanceAdoptionResult

**Location:** `src/llm_wiki_cli/api_types.py:149`
**Kind:** Class
**Bases:** `_MaintenanceAdoptionOptions`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `MaintenanceAdoptionResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `adoption_id` | `str` | *required* | — |
| `changed` | `bool` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceAdoptionResult (src/llm_wiki_cli/api_types.py)"]
    n1["_MaintenanceAdoptionOptions (src/llm_wiki_cli/api_types.py)"]
    n2["adopt_maintenance (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `adoption_id`, `changed` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_MaintenanceAdoptionOptions` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `adopt_maintenance` | type_reference | [api](../modules/api.md) | — |
