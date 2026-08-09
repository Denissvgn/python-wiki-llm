# InventoryCacheStats

**Location:** `src/llm_wiki_cli/services/inventory_cache.py:42`
**Kind:** Class
**Bases:** —
**Module:** [inventory_cache](../modules/inventory_cache.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `InventoryCacheStats` in `src/llm_wiki_cli/services/inventory_cache.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `enabled` | `bool` | `False` | — |
| `path` | `str \| None` | `None` | — |
| `status` | `str` | `'disabled'` | — |
| `hits` | `int` | `0` | — |
| `misses` | `int` | `0` | — |
| `stale` | `int` | `0` | — |
| `changed` | `int` | `0` | — |
| `deleted` | `int` | `0` | — |
| `fresh_extracted` | `int` | `0` | — |
| `saved_entries` | `int` | `0` | — |
| `load_error` | `str` | `''` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryCacheStats (src/llm_wiki_cli/services/inventory_cache.py)"]
    n1["_print_cache_stats (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["format_cache_stats (src/llm_wiki_cli/services/inventory_cache.py)"]
    n4["InventoryCache.__init__ (src/llm_wiki_cli/services/inventory_cache.py)"]
    n5["src/llm_wiki_cli/services/lint_service.py"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/inventory_cache.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/inventory_cache.md"
    click n4 "../modules/inventory_cache.md"
    click n5 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [inventory_cache](../modules/inventory_cache.md) | 1 | `changed`, `deleted`, `enabled`, `fresh_extracted`, `hits`, `load_error`, `misses`, `path`, `saved_entries`, `stale`, `status` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_print_cache_stats` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `extraction_service` | import | [extraction_service](../modules/extraction_service.md) |
| `format_cache_stats` | type_reference | [inventory_cache](../modules/inventory_cache.md) |
| `InventoryCache.__init__` | call | [inventory_cache](../modules/inventory_cache.md) |
| `lint_service` | import | [lint_service](../modules/lint_service.md) |
