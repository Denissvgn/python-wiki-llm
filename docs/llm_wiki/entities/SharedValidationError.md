# SharedValidationError

**Location:** `src/llm_wiki_cli/services/validation.py:47`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [validation](../modules/validation.md)

## Description

Raised when a caller uses a shared validator without a domain adapter.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SharedValidationError (src/llm_wiki_cli/services/validation.py)"]
    n1["ValueError"]
    n2["_default_path_error (src/llm_wiki_cli/services/validation.py)"]
    n3["is_canonical_uuid (src/llm_wiki_cli/services/validation.py)"]
    n4["require_portable_path_component (src/llm_wiki_cli/services/validation.py)"]
    n5["require_portable_relative_path (src/llm_wiki_cli/services/validation.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/validation.md"
    click n2 "../modules/validation.md"
    click n3 "../modules/validation.md"
    click n4 "../modules/validation.md"
    click n5 "../modules/validation.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [validation](../modules/validation.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_default_path_error` | call | [validation](../modules/validation.md) |
| `_default_path_error` | type_reference | [validation](../modules/validation.md) |
| `is_canonical_uuid` | call | [validation](../modules/validation.md) |
| `require_portable_path_component` | call | [validation](../modules/validation.md) |
| `require_portable_path_component` | call | [validation](../modules/validation.md) |
| `require_portable_path_component` | call | [validation](../modules/validation.md) |
| `require_portable_path_component` | call | [validation](../modules/validation.md) |
| `require_portable_path_component` | call | [validation](../modules/validation.md) |
| `require_portable_relative_path` | call | [validation](../modules/validation.md) |
