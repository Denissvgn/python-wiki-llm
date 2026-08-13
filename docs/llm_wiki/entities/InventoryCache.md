# InventoryCache

**Location:** `src/llm_wiki_cli/services/inventory_cache.py:280`
**Kind:** Class
**Bases:** —
**Module:** [inventory_cache](../modules/inventory_cache.md)

## Description

JSON-backed cache for per-file built-in inventory entries.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(src_dir: str \| Path, options: InventoryCacheOptions)` | — | — |
| `enabled` | `() -> bool` | `@property` | — |
| `load` | `(cache_key: dict[str, Any]) -> dict[str, dict]` | — | — |
| `finalize_lookup_status` | `() -> None` | — | — |
| `save` | `(cache_key: dict[str, Any], files: dict[str, dict]) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryCache (src/llm_wiki_cli/services/inventory_cache.py)"]
    n1["_load_inventory_cache_state (src/llm_wiki_cli/services/extraction_service.py)"]
    n2["_prepare_inventory_build_context (src/llm_wiki_cli/services/extraction_service.py)"]
    n3["_record_stale_cache_entry (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_should_save_inventory_cache (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["format_cache_stats (src/llm_wiki_cli/services/inventory_cache.py)"]
    n6["InventoryCache.__init__ (src/llm_wiki_cli/services/inventory_cache.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/inventory_cache.md"
    click n1 "../modules/extraction_service.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/inventory_cache.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [inventory_cache](../modules/inventory_cache.md) | 5 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_load_inventory_cache_state` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_prepare_inventory_build_context` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_record_stale_cache_entry` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_should_save_inventory_cache` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `format_cache_stats` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
| `InventoryCache.__init__` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
