# extraction_service Module

**Path:** `src/llm_wiki_cli/services/extraction_service.py`

## Description

Coordinates multi-language static extraction over one shared source snapshot.
It validates requests, plans built-in and trusted plugin extractors, reuses
safe inventory-cache entries, schedules only declared parallel-safe work, and
merges deterministic per-language results. Callers receive both the inventory
and explicit extractor status, cache, plugin, and source-snapshot metadata.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `EXTRACTOR_REGISTRY`, `PathValidationError`, `validate_source_paths`, `validate_source_root` |
| `..extractors.common` | `LANGUAGE_EXTENSIONS`, `filter_bundled_source_inventory`, `inventory_language_for_path`, `normalize_include_tests` |
| `..extractors.go_extractor` | `GoExtractionRequest` |
| `..extractors.haskell_extractor` | `HaskellExtractionRequest` |
| `..extractors.python_extractor` | `ComponentVisitor` |
| `..extractors.rust_extractor` | `RustExtractionRequest` |
| `.api_contracts` | `attach_routes_to_entry_points`, `build_api_contracts` |
| `.contracts` | `EXTRACT_DATA_FLOW_DETAILS_SCHEMA_VERSION`, `EXTRACT_SCHEMA_VERSION` |
| `.data_flow` | `DEFAULT_DATA_FLOW_DETAILS_FLOW_LIMIT`, `analyze_data_flow`, `analyze_data_flow_detailed`, `build_data_flow_context`, `data_flow_effective_limits` |
| `.dependencies` | `analyze_dependencies` |
| `.entrypoints` | `DEFAULT_FLOW_DEPTH`, `build_flow`, `build_flow_detailed`, `detect_entry_points`, `read_console_scripts`, `get_entry_points` |
| `.extraction_jobs` | `ExtractionJobPlan`, `ExtractionJobRequest` |
| `.imports` | `build_module_path_resolver` |
| `.inventory_cache` | `InventoryCache`, `InventoryCacheOptions`, `InventoryCacheStats`, `build_inventory_cache_key`, `is_valid_cache_entry`, `make_cache_entry` |
| `.io` | `write_text_output` |
| `.packages` | `discover_packages`, `stamp_inventory_packages` |
| `.plugins` | `get_extractor_registry`, `iter_components`, `load_entry_point`, `lock_path`, `parallel_safe_extractor_entry_points`, `runtime_project_plugins_enabled` |
| `.resource_diagnostics` | `format_resource_failure` |
| `.source_selection` | `SourceSelectionError`, `SourceSelectionPolicy`, `path_is_selected`, `resolve_source_selection`, `selection_may_contain_path` |
| `.source_snapshot` | `SourceFile`, `SourceSnapshot`, `SourceSnapshotError`, `build_source_snapshot`, `format_unsupported_source_summary`, `unsupported_source_summary` |
| `__future__` | `annotations` |
| `concurrent.futures` | `ThreadPoolExecutor` |
| `copy` | `deepcopy` |
| `dataclasses` | `dataclass`, `field` |
| `functools` | `lru_cache` |
| `hashlib` | `hashlib` |
| `importlib` | `importlib` |
| `json` | `json` |
| `pathlib` | `Path` |
| `re` | `re` |
| `shlex` | `shlex` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |
| `typing` | `Callable`, `Iterable` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/extraction_service.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/extraction_service.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (18) |
| Outbound | `src` (20) |

> All 38 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ExtractorStatus](../entities/ExtractorStatus.md) | 127 | — | — |
| [InventoryRequest](../entities/InventoryRequest.md) | 135 | — | — |
| [InventoryResult](../entities/InventoryResult.md) | 160 | — | — |
| [ExtractPayloadResult](../entities/ExtractPayloadResult.md) | 192 | — | — |
| [ExtractorFailureError](../entities/ExtractorFailureError.md) | 212 | `RuntimeError` | Raised when one or more extractors fail during payload construction. |
| [_ExtractionPlan](../entities/ExtractionPlan.md) | 237 | — | — |
| [_ExtractionOutcome](../entities/ExtractionOutcome.md) | 250 | — | — |
| [_InventoryBuildContext](../entities/InventoryBuildContext.md) | 261 | — | — |
| [_InventoryPlanningResult](../entities/InventoryPlanningResult.md) | 280 | — | — |
| [_ComposeParserState](../entities/ComposeParserState.md) | 2944 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_instantiate_extractor` | `(entry_point: str)` | — | Instantiate an extractor without using the shared instance cache. |
| `_instantiate_plugin_extractor` | `(entry_point: str, plugin_root: str \| Path)` | — | — |
| `_load_extractor` | `(entry_point: str)` | `@lru_cache(maxsize=None)` | Instantiate an extractor from a ``"module.path:ClassName"`` string. |
| `_load_plugin_extractor` | `(entry_point: str, plugin_root: str)` | — | — |
| `_extractor_failure_message` | `(result: InventoryResult) -> str` | — | — |
| `print_inventory_failures` | `(result: InventoryResult, *, file = None) -> None` | — | Print extractor failures in a consistent form. |
| `_run_extraction_plan` | `(plan: _ExtractionPlan, *, fresh_instance: bool = False) -> _ExtractionOutcome` | — | — |
| `_merge_language_inventory` | `(target: dict, source_order: list[str], *sources: dict) -> None` | — | — |
| `_coerce_inventory_request` | `(request, legacy_args: tuple, legacy_kwargs: dict) -> InventoryRequest` | — | — |
| `get_inventory_result` | `(request = _MISSING_INVENTORY_REQUEST, *legacy_args, **legacy_kwargs) -> InventoryResult` | — | Scan source files across all registered languages and return inventory. |
| `_build_inventory_result` | `(request: InventoryRequest) -> InventoryResult` | — | — |
| `_completed_inventory_result` | `(context: _InventoryBuildContext, *, inventory: dict, statuses: dict[str, ExtractorStatus], extraction_job_plan: ExtractionJobPlan, selected_plugin_components: tuple[dict, ...], producer_plugin_components: tuple[dict, ...], evaluated_source_snapshot: SourceSnapshot, outcomes_by_language: dict[str, _ExtractionOutcome]) -> InventoryResult` | — | — |
| `_python_extraction_sidecars` | `(outcomes_by_language: dict[str, _ExtractionOutcome]) -> dict` | — | — |
| `_inventory_plugin_state` | `(context: _InventoryBuildContext, statuses: dict[str, ExtractorStatus], inventory: dict) -> tuple[tuple[dict, ...], tuple[dict, ...], SourceSnapshot]` | — | — |
| `_selected_extractor_plugin_components` | `(context: _InventoryBuildContext, statuses: dict[str, ExtractorStatus]) -> tuple[dict, ...]` | — | — |
| `_snapshot_with_plugin_inventory_paths` | `(snapshot: SourceSnapshot, inventory: dict, components: tuple[dict, ...]) -> SourceSnapshot` | — | — |
| `_build_extraction_job_plan` | `(context: _InventoryBuildContext, planning: _InventoryPlanningResult) -> ExtractionJobPlan` | — | — |
| `_prepare_inventory_build_context` | `(request: InventoryRequest) -> _InventoryBuildContext` | — | — |
| `_source_snapshot_for_inventory_request` | `(request: InventoryRequest) -> SourceSnapshot` | — | — |
| `_filter_selected_inventory` | `(source_snapshot: SourceSnapshot, inventory: dict) -> dict` | — | — |
| `_captured_plugin_lock` | `(source_root: str \| Path, *, plugin_root: str \| Path = '.') -> tuple[str \| None, str \| None]` | — | Capture the exact applicable project-local plugin lock without leaking it. |
| `_selected_runtime_plugin_components` | `(source_root: str \| Path) -> tuple[tuple[dict, ...], str \| Path]` | — | Mirror source-root-first documentation-hook selection without loading it. |
| `_configured_runtime_plugin_components` | `(source_root: str \| Path) -> tuple[tuple[dict, ...], str \| Path]` | — | Use only plugins installed in the configured source boundary. |
| `_source_files_by_path` | `(source_snapshot: SourceSnapshot) -> dict[str, SourceFile]` | — | — |
| `_load_inventory_cache_state` | `(request: InventoryRequest, source_snapshot: SourceSnapshot, registry: dict[str, str], cache: InventoryCache \| None, source_file_by_path: dict[str, SourceFile]) -> tuple[dict \| None, dict[str, dict], dict[str, str]]` | — | — |
| `_plan_inventory_extractions` | `(context: _InventoryBuildContext) -> _InventoryPlanningResult` | — | — |
| `_plan_language_extraction` | `(context: _InventoryBuildContext, language: str, entry_point: str, status_by_language: dict[str, ExtractorStatus], cached_by_language: dict[str, dict]) -> _ExtractionPlan \| None` | — | — |
| `_can_use_inventory_cache` | `(context: _InventoryBuildContext, is_builtin: bool) -> bool` | — | — |
| `_fresh_inventory_source_files` | `(context: _InventoryBuildContext, language: str, source_files: list[str] \| None, cached_by_language: dict[str, dict]) -> list[str]` | — | — |
| `_record_cached_inventory_entry` | `(context: _InventoryBuildContext, cached_by_language: dict[str, dict], language: str, rel_path: str, cached_entry: dict) -> None` | — | — |
| `_record_stale_cache_entry` | `(cache: InventoryCache, cached_entry: dict, file_hash: str) -> None` | — | — |
| `_build_extraction_kwargs` | `(context: _InventoryBuildContext, language: str, is_builtin: bool, fresh_source_files: list[str]) -> dict` | — | — |
| `_build_builtin_extraction_kwargs` | `(context: _InventoryBuildContext, language: str, fresh_source_files: list[str]) -> dict` | — | — |
| `_inventory_helper_cache_dir` | `(request: InventoryRequest) -> str \| None` | — | — |
| `_run_inventory_plans` | `(plans: list[_ExtractionPlan], parallel_jobs: int) -> dict[str, _ExtractionOutcome]` | — | — |
| `_run_parallel_safe_inventory_plans` | `(parallel_safe_plans: list[_ExtractionPlan], parallel_jobs: int, outcomes_by_language: dict[str, _ExtractionOutcome]) -> None` | — | — |
| `_collect_inventory_outcomes` | `(context: _InventoryBuildContext, planning: _InventoryPlanningResult, outcomes_by_language: dict[str, _ExtractionOutcome]) -> dict[str, dict]` | — | — |
| `_update_inventory_cache_entries` | `(context: _InventoryBuildContext, plan: _ExtractionPlan, extracted: dict) -> None` | — | — |
| `_merge_inventory_results` | `(context: _InventoryBuildContext, cached_by_language: dict[str, dict], extracted_by_language: dict[str, dict]) -> dict` | — | — |
| `_ordered_inventory_statuses` | `(registry: dict[str, str], status_by_language: dict[str, ExtractorStatus]) -> dict[str, ExtractorStatus]` | — | — |
| `_save_inventory_cache` | `(context: _InventoryBuildContext, statuses: dict[str, ExtractorStatus]) -> None` | — | — |
| `_should_save_inventory_cache` | `(cache: InventoryCache) -> bool` | — | — |
| `get_inventory` | `(src_dir, deep = False, only_files = None, include_empty = False, *, source_selection: str \| Path \| None = None)` | — | Backward-compatible inventory API returning only the inventory dict. |
| `ensure_complete_inventory` | `(result: InventoryResult) -> bool` | — | Return True when all extractors that had matching source files succeeded. |
| `infer_language_from_path` | `(filepath: str) -> str \| None` | — | — |
| `languages_with_source` | `(src_dir: str, only_files: list[str] \| None = None, *, source_selection: str \| Path \| None = None) -> set[str]` | — | — |
| `_inventory_or_exit` | `(src_dir: str, *, deep: bool = False, only_files = None, include_empty: bool = False, source_selection: str \| Path \| None = None) -> dict` | — | — |
| `_git_changed_files` | `(src_dir: str) -> list[str] \| None` | — | Return files changed in the last commit, relative to *src_dir*. |
| `_git_name_status_paths` | `(output: str) -> list[str]` | — | Decode NUL-delimited name-status output, retaining both rename sides. |
| `_snapshot_path_is_selection_input` | `(snapshot: SourceSnapshot, path: str) -> bool` | — | — |
| `_partition_snapshot_git_changes` | `(changed: Iterable[str], snapshot: SourceSnapshot) -> tuple[list[str], bool]` | — | Return selected source changes and whether a selection boundary changed. |
| `filter_source_diff` | `(diff_text: str, selection_policy: SourceSelectionPolicy \| None, *, retained_roots: Iterable[str] = (), source_snapshot: SourceSnapshot \| None = None) -> str` | — | Drop configured-policy diff blocks that could disclose deselected files. |
| `_repository_relative_retained_roots` | `(retained_roots: Iterable[str], *, repository_root: Path) -> tuple[str, ...]` | — | Translate real retained paths into the source Git coordinate system. |
| `_diff_block_is_selected` | `(block: list[str], policy: SourceSelectionPolicy, retained_roots: tuple[str, ...], *, source_snapshot: SourceSnapshot \| None, source_prefix: str \| None) -> bool` | — | — |
| `_git_diff_block_paths` | `(block: list[str]) -> tuple[str, ...] \| None` | — | — |
| `_git_metadata_path` | `(value: str, *, prefixed: bool) -> str \| None \| object` | — | — |
| `_git_diff_path` | `(value: str) -> str \| None` | — | — |
| `_build_extract_source_snapshot` | `(src_root: Path, *, only_files: Iterable[str] \| None, include_tests: Iterable[str], selection_policy: SourceSelectionPolicy \| None) -> SourceSnapshot` | — | — |
| `_compact_summary_names` | `(items: Iterable, key: str \| None = None) -> list[str]` | — | — |
| `_summarize_inventory` | `(inventory: dict) -> dict` | — | Produce a compact one-line-per-symbol summary from a shallow inventory. |
| `_dependency_extract_block` | `(analysis: dict) -> dict` | — | Project dependency analysis into the public ``extract --deep`` shape. |
| `_data_flow_truncation_reason` | `(coverage: dict) -> str \| None` | — | — |
| `_public_data_flow_coverage` | `(coverage: dict) -> dict` | — | — |
| `_public_detailed_data_flow` | `(flow: dict) -> dict` | — | — |
| `_data_flow_details_contract` | `(*, deep: bool, inventory: dict, unsupported_sources: dict, flows: list[dict]) -> dict` | — | — |
| `build_extract_payload` | `(src_dir: str = '.', *, changed: bool = False, summary: bool = False, deep: bool = False, paths: list[str] \| None = None, package_filter: str \| None = None, include_empty: bool = False, helper_cache_dir: str \| None = None, include_tests: Iterable[str] \| None = None, openapi_file: str \| Path \| None = None, allow_external_src: bool = False, read_only: bool = False, include_plugins: bool = True, source_plugins_only: bool = False, source_selection: str \| Path \| None = None, source_snapshot: SourceSnapshot \| None = None) -> ExtractPayloadResult` | — | Build the stable extract JSON payload without printing or exiting. |
| `run` | `(args)` | — | — |
| `_module_name` | `(filepath: str) -> str` | — | — |
| `_build_symbol_file_index` | `(inventory: dict) -> dict[str, set[str]]` | — | — |
| `_is_test_file` | `(filepath: str) -> bool` | — | — |
| `_resolve_import_candidates` | `(imp: dict, filepath: str, symbol_to_files: dict[str, set[str]], module_resolver) -> set[str]` | — | — |
| `_resolve_imported_symbols` | `(filepath: str, imports: list[dict], symbol_to_files: dict[str, set[str]], module_resolver) -> dict[str, tuple[str, str]]` | — | — |
| `_iter_callable_components` | `(data: dict)` | — | — |
| `_function_references_symbol` | `(fn: dict, visible_name: str) -> bool` | — | — |
| `_referenced_import_chain` | `(fn: dict, imported_symbols: dict[str, tuple[str, str]]) -> tuple[set[str], list[str]]` | — | — |
| `_workflow_name` | `(fn_name: str, module_name: str) -> str` | — | — |
| `_workflow_entry` | `(filepath: str, module_name: str, fn: dict, touched_module_paths: set[str], chain: list[str]) -> tuple[str, dict]` | — | — |
| `_workflow_entries_for_file` | `(filepath: str, data: dict, imported_symbols: dict[str, tuple[str, str]]) -> dict[str, dict]` | — | — |
| `get_call_graph` | `(inventory: dict) -> dict` | — | Build cross-module call chains from a deep inventory. |
| `_file_local_symbols` | `(data: dict) -> set[str]` | — | Names of functions and classes defined in a single file entry. |
| `_caller_components` | `(data: dict)` | — | Yield ``(caller_symbol, fn, class_name)`` for every callable in a file. |
| `_attr_root` | `(attr: str) -> str` | — | — |
| `_self_method_target` | `(call: dict, class_name: str \| None, data: dict, filepath: str) -> tuple[str, str] \| None` | — | Resolve a ``self.x`` / ``cls.x`` call to a method of the same class. |
| `_call_uses_import` | `(name: str, attr: str, imported_names: set[str]) -> bool` | — | — |
| `_resolve_call` | `(call: dict, filepath: str, class_name: str \| None, data: dict, imported_internal: dict[str, tuple[str, str]], imported_names: set[str], local_symbols: set[str], symbol_to_files: dict[str, set[str]]) -> tuple[str \| None, str, str]` | — | Return ``(to_file, to_symbol, kind)`` for a single call record. |
| `_edges_for_file` | `(filepath: str, data: dict, symbol_to_files: dict[str, set[str]], module_resolver) -> list[dict]` | — | Resolve the call edges that originate in a single file entry. |
| `_detailed_import_candidates` | `(filepath: str, imports: list[dict], symbol_to_files: dict[str, set[str]], module_resolver) -> dict[str, tuple[tuple[str, str], ...]]` | — | Index every internal import candidate without collapsing ambiguity. |
| `_resolve_call_observation` | `(call: dict, filepath: str, class_name: str \| None, data: dict, imported_candidates: dict[str, tuple[tuple[str, str], ...]], imported_names: set[str], local_symbols: set[str], symbol_to_files: dict[str, set[str]]) -> tuple[str \| None, str, str, list[dict]]` | — | Resolve one call while retaining every ambiguous internal candidate. |
| `_call_observations_for_file` | `(filepath: str, data: dict, symbol_to_files: dict[str, set[str]], module_resolver) -> list[dict]` | — | — |
| `resolve_call_observations` | `(inventory: dict) -> dict` | — | Return deterministic, versioned call observations with honest ambiguity. |
| `resolve_call_edges` | `(inventory: dict) -> list[dict]` | — | Resolve captured ``calls`` records into caller→callee edges. |
| `_parse_dockerfile` | `(text: str) -> dict` | — | Parse a Dockerfile into a structured dict (line-based, no external deps). |
| `_parse_inline_yaml_list` | `(value: str) -> list[str] \| None` | — | Parse an inline YAML list like ``["CMD", "curl", "-f", "http://..."]``. |
| `_strip_yaml_quotes` | `(value: str) -> str` | — | Remove surrounding YAML quotes from a value. |
| `_compose_path_parent` | `(state: _ComposeParserState, path: list[str], *, create: bool = False)` | — | Return ``(parent_dict, final_key)`` for a nested service path. |
| `_start_compose_top_level_section` | `(state: _ComposeParserState, stripped: str, indent: int) -> bool` | — | — |
| `_start_compose_service` | `(state: _ComposeParserState, stripped: str, indent: int) -> bool` | — | — |
| `_compose_service_depth` | `(indent: int) -> int` | — | — |
| `_append_compose_list_item` | `(state: _ComposeParserState, stripped: str) -> None` | — | — |
| `_assign_compose_value` | `(parent: dict, final_key: str, value: str) -> None` | — | — |
| `_set_compose_service_key` | `(state: _ComposeParserState, stripped: str, depth: int) -> None` | — | — |
| `_parse_compose_service_line` | `(state: _ComposeParserState, stripped: str, indent: int) -> None` | — | — |
| `_collect_compose_section_name` | `(names: list[str], stripped: str, indent: int) -> None` | — | — |
| `_parse_compose` | `(text: str) -> dict` | — | Parse a docker-compose YAML file using line-based parsing (no PyYAML). |
| `_looks_like_compose` | `(text: str) -> bool` | — | Return True if the file content appears to be a docker-compose file. |
| `get_docker_inventory` | `(src_dir: str, *, source_snapshot: SourceSnapshot \| None = None) -> dict` | — | Discover and parse Dockerfiles and Compose files in the source tree. |
