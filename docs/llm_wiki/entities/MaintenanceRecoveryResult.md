# MaintenanceRecoveryResult

**Location:** `src/llm_wiki_cli/api_types.py:164`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `MaintenanceRecoveryResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `adoption_id` | `str` | *required* | — |
| `restored` | `bool` | *required* | — |
| `state_hash` | `str` | *required* | — |
| `requires_sync` | `bool` | *required* | — |
| `prose_basis_validated` | `bool` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceRecoveryResult (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["recover_maintenance (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `adoption_id`, `prose_basis_validated`, `requires_sync`, `restored`, `state_hash` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `recover_maintenance` | type_reference | [api](../modules/api.md) | — |
