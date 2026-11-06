# HelperPreparationError

**Location:** `src/llm_wiki_cli/services/helper_cache.py:47`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [helper_cache](../modules/helper_cache.md)

## Description

The selected bundled helper could not be prepared once.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(language: str, message: str, cache_root: Path \| None = None)` | — | — |
| `__str__` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HelperPreparationError (src/llm_wiki_cli/services/helper_cache.py)"]
    n1["RuntimeError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/services/context_packet.py"]
    n4["src/llm_wiki_cli/services/context_service.py"]
    n5["_profile (src/llm_wiki_cli/services/helper_cache.py)"]
    n6["_selected_rust_executable (src/llm_wiki_cli/services/helper_cache.py)"]
    n7["ensure_helper (src/llm_wiki_cli/services/helper_cache.py)"]
    n8["prepare_operation_helpers (src/llm_wiki_cli/services/helper_preparation.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/helper_cache.md"
    click n2 "../modules/api.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/helper_cache.md"
    click n6 "../modules/helper_cache.md"
    click n7 "../modules/helper_cache.md"
    click n8 "../modules/helper_preparation.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [helper_cache](../modules/helper_cache.md) | 2 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `_profile` | call | [helper_cache](../modules/helper_cache.md) | 12 |
| `_selected_rust_executable` | call | [helper_cache](../modules/helper_cache.md) | 3 |
| `ensure_helper` | call | [helper_cache](../modules/helper_cache.md) | 2 |
| `prepare_operation_helpers` | call | [helper_preparation](../modules/helper_preparation.md) | 3 |
