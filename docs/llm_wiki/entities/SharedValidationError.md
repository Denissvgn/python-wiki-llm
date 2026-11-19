# SharedValidationError

**Location:** `src/llm_wiki_engine/validation.py:98`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [validation](../modules/validation.md)

## Description

Raised when a caller uses a shared validator without a domain adapter.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SharedValidationError (src/llm_wiki_engine/validation.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_engine/extract_format.py"]
    n3["src/llm_wiki_engine/surface_index_format.py"]
    n4["_check_path_collision (src/llm_wiki_engine/validation.py)"]
    n5["_default_path_error (src/llm_wiki_engine/validation.py)"]
    n6["is_canonical_uuid (src/llm_wiki_engine/validation.py)"]
    n7["require_portable_path_component (src/llm_wiki_engine/validation.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/validation.md"
    click n2 "../modules/extract_format.md"
    click n3 "../modules/surface_index_format.md"
    click n4 "../modules/validation.md"
    click n5 "../modules/validation.md"
    click n6 "../modules/validation.md"
    click n7 "../modules/validation.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `extract_format` | import | [extract_format](../modules/extract_format.md) | — |
| `surface_index_format` | import | [surface_index_format](../modules/surface_index_format.md) | — |
| `_check_path_collision` | call | [validation](../modules/validation.md) | 1 |
| `_default_path_error` | call | [validation](../modules/validation.md) | 1 |
| `_default_path_error` | type_reference | [validation](../modules/validation.md) | — |
| `is_canonical_uuid` | call | [validation](../modules/validation.md) | 1 |
| `require_portable_path_component` | call | [validation](../modules/validation.md) | 5 |
