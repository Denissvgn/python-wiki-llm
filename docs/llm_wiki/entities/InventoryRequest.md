# InventoryRequest

**Location:** `src/llm_wiki_cli/services/extraction_service.py:135`
**Kind:** Class
**Bases:** —
**Module:** [extraction_service](../modules/extraction_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated input contract for one extraction pass. It combines the source root
and optional prebuilt snapshot with depth, file narrowing, cache, worker,
helper, plugin, and source-selection controls. Construction normalizes mutable
inputs so the extraction planner receives a stable request.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `src_dir` | `str \| Path` | *required* | — |
| `deep` | `bool` | `False` | — |
| `only_files` | `list[str] \| None` | `None` | — |
| `include_empty` | `bool` | `False` | — |
| `source_snapshot` | `SourceSnapshot \| None` | `None` | — |
| `cache_options` | `InventoryCacheOptions \| None` | `None` | — |
| `parallel_jobs` | `int` | `1` | — |
| `helper_cache_dir` | `str \| None` | `None` | — |
| `include_tests` | `Iterable[str] \| None` | `None` | — |
| `job_request` | `ExtractionJobRequest \| None` | `None` | — |
| `plan_reporter` | `Callable[[ExtractionJobPlan], None] \| None` | `None` | — |
| `include_plugins` | `bool` | `True` | — |
| `capture_data_effect_observations` | `bool` | `False` | — |
| `capture_import_observations` | `bool` | `False` | — |
| `source_selection` | `str \| Path \| None` | `None` | — |
| `source_plugins_only` | `bool` | `False` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryRequest (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["_collect_runtime (src/llm_wiki_cli/services/documentation_native.py)"]
    n2["_build_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
    n3["_coerce_inventory_request (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_inventory_helper_cache_dir (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_inventory_or_exit (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_load_inventory_cache_state (src/llm_wiki_cli/services/extraction_service.py)"]
    n7["_prepare_inventory_build_context (src/llm_wiki_cli/services/extraction_service.py)"]
    n8["_source_snapshot_for_inventory_request (src/llm_wiki_cli/services/extraction_service.py)"]
    n9["build_extract_payload (src/llm_wiki_cli/services/extraction_service.py)"]
    n10["get_inventory (src/llm_wiki_cli/services/extraction_service.py)"]
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
    click n0 "../modules/extraction_service.md"
    click n1 "../modules/documentation_native.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/extraction_service.md"
    click n9 "../modules/extraction_service.md"
    click n10 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 1 | `cache_options`, `capture_data_effect_observations`, `capture_import_observations`, `deep`, `helper_cache_dir`, `include_empty`, `include_plugins`, `include_tests`, `job_request`, `only_files`, `parallel_jobs`, `plan_reporter` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_collect_runtime` | call | [documentation_native](../modules/documentation_native.md) |
| `_build_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_coerce_inventory_request` | call | [extraction_service](../modules/extraction_service.md) |
| `_coerce_inventory_request` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_inventory_helper_cache_dir` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_inventory_or_exit` | call | [extraction_service](../modules/extraction_service.md) |
| `_load_inventory_cache_state` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_prepare_inventory_build_context` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_source_snapshot_for_inventory_request` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `build_extract_payload` | call | [extraction_service](../modules/extraction_service.md) |
| `build_extract_payload` | call | [extraction_service](../modules/extraction_service.md) |
| `get_inventory` | call | [extraction_service](../modules/extraction_service.md) |
