# InventoryRequest

**Location:** `src/llm_wiki_cli/services/extraction_service.py:153`
**Kind:** Class
**Bases:** —
**Module:** [extraction_service](../modules/extraction_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated input contract for one extraction pass. It combines the source root
and optional prebuilt snapshot with depth, file narrowing, cache, worker,
helper, plugin, and source-selection controls. Construction normalizes mutable
inputs so the extraction planner receives a stable request.

`capture_path_outcomes` enables attributable diagnostics for built-in Python, JavaScript/TypeScript, Go, Rust and Haskell providers. Diagnostic extraction bypasses plain inventory-cache hits; retained qualified sync analysis remains committed to the source/provider basis and missing qualification requires a scoped live retry.

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
| `capture_implementation_observations` | `bool` | `False` | — |
| `capture_path_outcomes` | `bool` | `False` | — |
| `retain_empty_paths` | `tuple[str, ...]` | `()` | — |
| `implementation_cache_artifacts` | `object \| None` | `field(default=None, repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryRequest (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["_prepare_sync_run (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_preflight_bootstrap_analysis (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["_collect_runtime (src/llm_wiki_cli/services/documentation_native.py)"]
    n4["_build_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_coerce_inventory_request (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_inventory_helper_cache_dir (src/llm_wiki_cli/services/extraction_service.py)"]
    n7["_inventory_or_exit (src/llm_wiki_cli/services/extraction_service.py)"]
    n8["_load_inventory_cache_state (src/llm_wiki_cli/services/extraction_service.py)"]
    n9["_prepare_inventory_build_context (src/llm_wiki_cli/services/extraction_service.py)"]
    n10["_source_snapshot_for_inventory_request (src/llm_wiki_cli/services/extraction_service.py)"]
    n11["build_extract_payload (src/llm_wiki_cli/services/extraction_service.py)"]
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
    click n0 "../modules/extraction_service.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/documentation_native.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/extraction_service.md"
    click n9 "../modules/extraction_service.md"
    click n10 "../modules/extraction_service.md"
    click n11 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 1 | `cache_options`, `capture_data_effect_observations`, `capture_implementation_observations`, `capture_import_observations`, `capture_path_outcomes`, `deep`, `helper_cache_dir`, `implementation_cache_artifacts`, `include_empty`, `include_plugins`, `include_tests`, `job_request` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_prepare_sync_run` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `_preflight_bootstrap_analysis` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) | 1 |
| `_collect_runtime` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `_build_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_coerce_inventory_request` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_coerce_inventory_request` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_inventory_helper_cache_dir` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_inventory_or_exit` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_load_inventory_cache_state` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_prepare_inventory_build_context` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_source_snapshot_for_inventory_request` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `build_extract_payload` | call | [extraction_service](../modules/extraction_service.md) | 2 |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
