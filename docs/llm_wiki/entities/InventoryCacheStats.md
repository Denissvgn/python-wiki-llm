# InventoryCacheStats

**Location:** `src/llm_wiki_cli/services/inventory_cache.py:51`
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
| `failure_stage` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryCacheStats (src/llm_wiki_cli/services/inventory_cache.py)"]
    n1["run (src/llm_wiki_cli/commands/ci_check_cmd.py)"]
    n2["src/llm_wiki_cli/services/extraction_service.py"]
    n3["format_cache_stats (src/llm_wiki_cli/services/inventory_cache.py)"]
    n4["InventoryCache.__init__ (src/llm_wiki_cli/services/inventory_cache.py)"]
    n5["src/llm_wiki_cli/services/lint_service.py"]
    n6["inventory_result (src/llm_wiki_cli/services/sync_analysis_cache.py)"]
    n7["_print_cache_stats (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/inventory_cache.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/inventory_cache.md"
    click n4 "../modules/inventory_cache.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/sync_analysis_cache.md"
    click n7 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [inventory_cache](../modules/inventory_cache.md) | 1 | `changed`, `deleted`, `enabled`, `failure_stage`, `fresh_extracted`, `hits`, `load_error`, `misses`, `path`, `saved_entries`, `stale`, `status` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `run` | call | [ci_check_cmd](../modules/ci_check_cmd.md) | 1 |
| `extraction_service` | import | [extraction_service](../modules/extraction_service.md) | — |
| `format_cache_stats` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
| `InventoryCache.__init__` | call | [inventory_cache](../modules/inventory_cache.md) | 1 |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `inventory_result` | call | [sync_analysis_cache](../modules/sync_analysis_cache.md) | 1 |
| `_print_cache_stats` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
