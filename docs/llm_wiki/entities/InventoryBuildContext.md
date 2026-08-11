# _InventoryBuildContext

**Location:** `src/llm_wiki_cli/services/extraction_service.py:261`
**Kind:** Class
**Bases:** —
**Module:** [extraction_service](../modules/extraction_service.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `_InventoryBuildContext` in `src/llm_wiki_cli/services/extraction_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `request` | `InventoryRequest` | *required* | — |
| `source_snapshot` | `SourceSnapshot` | *required* | — |
| `registry` | `dict[str, str]` | *required* | — |
| `parallel_jobs` | `int` | *required* | — |
| `cache` | `InventoryCache \| None` | *required* | — |
| `cache_key` | `dict \| None` | *required* | — |
| `cache_files` | `dict[str, dict]` | *required* | — |
| `updated_cache_files` | `dict[str, dict]` | *required* | — |
| `source_file_by_path` | `dict[str, SourceFile]` | *required* | — |
| `source_hashes` | `dict[str, str]` | *required* | — |
| `parallel_safe_plugin_entry_points` | `set[str]` | *required* | — |
| `plugin_components` | `tuple[dict, ...]` | *required* | — |
| `plugin_lock_path` | `str \| None` | *required* | — |
| `plugin_lock_hash` | `str \| None` | *required* | — |
| `plugin_root` | `str \| Path` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_InventoryBuildContext (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["_build_builtin_extraction_kwargs (src/llm_wiki_cli/services/extraction_service.py)"]
    n2["_build_extraction_job_plan (src/llm_wiki_cli/services/extraction_service.py)"]
    n3["_build_extraction_kwargs (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_can_use_inventory_cache (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_collect_inventory_outcomes (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_completed_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
    n7["_fresh_inventory_source_files (src/llm_wiki_cli/services/extraction_service.py)"]
    n8["_inventory_plugin_state (src/llm_wiki_cli/services/extraction_service.py)"]
    n9["_merge_inventory_results (src/llm_wiki_cli/services/extraction_service.py)"]
    n10["_plan_inventory_extractions (src/llm_wiki_cli/services/extraction_service.py)"]
    n11["_plan_language_extraction (src/llm_wiki_cli/services/extraction_service.py)"]
    n12["_prepare_inventory_build_context (src/llm_wiki_cli/services/extraction_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    click n0 "../modules/extraction_service.md"
    click n1 "../modules/extraction_service.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/extraction_service.md"
    click n9 "../modules/extraction_service.md"
    click n10 "../modules/extraction_service.md"
    click n11 "../modules/extraction_service.md"
    click n12 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 0 | `cache`, `cache_files`, `cache_key`, `parallel_jobs`, `parallel_safe_plugin_entry_points`, `plugin_components`, `plugin_lock_hash`, `plugin_lock_path`, `plugin_root`, `registry`, `request`, `source_file_by_path` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_builtin_extraction_kwargs` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_build_extraction_job_plan` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_build_extraction_kwargs` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_can_use_inventory_cache` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_collect_inventory_outcomes` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_completed_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_fresh_inventory_source_files` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_inventory_plugin_state` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_merge_inventory_results` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_plan_inventory_extractions` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_plan_language_extraction` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_prepare_inventory_build_context` | call | [extraction_service](../modules/extraction_service.md) | 1 |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
