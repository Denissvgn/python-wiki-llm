# sync_cmd Module

**Path:** `src/llm_wiki_cli/commands/sync_cmd.py`

## Description

Incremental wiki sync — update only pages whose source has changed.

Workflow:
    1. Classify the wiki lifecycle, loading a managed manifest, safely seeding a
       legacy wiki with ``index.md``, or routing pristine/partial targets to
       bootstrap/migration before source extraction.
    2. Hash every source file in the current AST inventory.
    3. Compute a diff: new / changed / unchanged / removed files, moved classes.
    4. Apply changes surgically: regenerate pages for new/changed files, add a
       deprecation warning to pages whose source was removed, skip everything else.
    5. Rebuild index.md and append a log entry if anything changed.
    6. Save the updated manifest.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `__version__` |
| `..config` | `validate_path`, `validate_source_root` |
| `..services.api_contracts` | `ApiContractError`, `attach_routes_to_entry_points`, `build_api_contracts`, `load_openapi_document`, `render_api_contracts_markdown` |
| `..services.bootstrap_runtime` | `_build_entity_relationship_summary_map`, `_build_relationships`, `_generate_dependencies_md`, `_generate_entity_md`, `_generate_flow_md`, `_generate_index_md`, `_generate_load_order_md`, `_generate_module_md`, `_generate_workflow_md`, `_generate_infrastructure_md`, `_generated_diagram_style`, `_module_name_from_path`, `_page_name_for_module`, `_source_snapshot_log_lines`, `build_entity_occurrence_page_map`, `build_entity_page_map`, `build_module_page_map` |
| `..services.data_flow` | `analyze_data_flow`, `analyze_data_flow_detailed`, `build_data_flow_context` |
| `..services.dependencies` | `analyze_dependencies`, `build_dependency_observations`, `build_external_dependency_observations` |
| `..services.entrypoints` | `build_flow`, `build_flow_detailed`, `entry_points_from_detailed_observations`, `get_detailed_entry_points`, `read_console_scripts` |
| `..services.extraction_jobs` | `ExtractionJobPlan`, `ExtractionJobRequest`, `extraction_job_request_from_args`, `print_extraction_job_plan` |
| `..services.extraction_service` | `InventoryResult`, `get_call_graph`, `get_inventory_result`, `get_docker_inventory`, `print_inventory_failures`, `resolve_call_observations`, `resolve_call_edges` |
| `..services.infrastructure_inventory` | `get_yaml_infrastructure_inventory`, `infrastructure_display_label` |
| `..services.infrastructure_sync` | `InfrastructureSyncError`, `InfrastructureSyncPlan`, `build_infrastructure_sync_plan`, `with_infrastructure_deselection_generation_input`, `with_infrastructure_generation_input` |
| `..services.inventory_cache` | `InventoryCacheOptions`, `InventoryCacheStats`, `format_cache_stats` |
| `..services.io` | `read_md`, `write_md` |
| `..services.knowledge_artifacts` | `ArtifactWriteState`, `KnowledgeCommitResult` |
| `..services.knowledge_envelope` | `RepositoryEvidence` |
| `..services.knowledge_evidence` | `hash_file`, `is_valid_sha256`, `semantic_hash_for_file` |
| `..services.knowledge_governance` | `GOVERNANCE_FILENAME`, `GovernanceError`, `load_governance` |
| `..services.knowledge_orchestration` | `RUNTIME_GENERATION_OPTION_DEFAULTS`, `RuntimeKnowledgeInputs`, `collect_runtime_repository_evidence`, `committed_governance_bundle_id`, `committed_runtime_provenance`, `finalize_runtime_knowledge`, `runtime_generation_options`, `runtime_generation_options_hash`, `runtime_source_snapshot_hash` |
| `..services.markdown_sections` | `format_table_row`, `is_placeholder_description`, `is_table_separator`, `normalize_markdown`, `preserve_index_custom_sections`, `preserve_level_two_section_exact`, `preserve_table_description_cells`, `replace_section_body`, `section_body`, `section_bounds`, `semantic_table_key`, `should_preserve_semantic_value`, `split_table_row`, `table_description_cells`, `trim_blank_lines` |
| `..services.module_maps` | `build_module_dependency_maps` |
| `..services.paths` | `is_test_source_path`, `portable_source_root_label` |
| `..services.plugins` | `runtime_plugin_fallback_root`, `runtime_project_plugins_enabled` |
| `..services.section_ownership` | `SemanticMergeResult`, `merge_entity_semantics`, `merge_module_semantics`, `merge_semantic_markdown`, `replace_generated_section` |
| `..services.source_selection` | `SourceSelectionError`, `SourceSelectionPolicy`, `path_is_selected`, `resolve_source_selection`, `validate_persisted_source_selection_identity` |
| `..services.source_snapshot` | `SourceSnapshot`, `build_source_snapshot`, `format_unsupported_source_summary`, `unsupported_source_summary` |
| `..services.sync_analysis` | `SyncDiff`, `compute_sync_diff` |
| `..services.sync_manifest` | `EVIDENCE_NOT_RECORDED`, `MANIFEST_FILENAME`, `MANIFEST_REPAIR_UNAVAILABLE`, `MANIFEST_STATE_UNAVAILABLE`, `MANIFEST_VERSION`, `SourceSelectionPruneResult`, `SyncManifest`, `prune_manifest_for_source_selection`, `retained_concept_page_paths` |
| `..services.wiki_lifecycle` | `WikiLifecycleState`, `bootstrap_guidance`, `classify_wiki_lifecycle`, `migration_guidance` |
| `..services.wiki_surface` | `PageKind`, `WikiSurfaceError`, `canonical_path`, `collect_wiki_pages`, `mcp_uri` |
| `..services.wiki_surface_index` | `SURFACE_INDEX_FILENAME`, `WIKI_SURFACE_INDEX_SCHEMA_VERSION`, `evaluate_surface_index` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `copy` | `deepcopy` |
| `dataclasses` | `dataclass`, `field`, `replace` |
| `datetime` | `date` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `shutil` | `shutil` |
| `sys` | `sys` |
| `tempfile` | `tempfile` |
| `typing` | `Callable`, `Iterable`, `Mapping`, `Optional` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/commands/sync_cmd.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/sync_cmd.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (1) |
| Outbound | `src` (29) |

> All 30 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [GeneratedSurfacePruneError](../entities/GeneratedSurfacePruneError.md) | 255 | `ValueError` | A stale generated page cannot be removed without explicit authority. |
| [SyncRuntimeRefreshError](../entities/SyncRuntimeRefreshError.md) | 259 | `ValueError` | A runtime-basis transition cannot be applied in the requested mode. |
| [SyncResult](../entities/SyncResult.md) | 589 | — | — |
| [_ApplyDiffContext](../entities/ApplyDiffContext.md) | 627 | — | — |
| [_GeneratedSectionContext](../entities/GeneratedSectionContext.md) | 645 | — | — |
| [_SyncRunOptions](../entities/SyncRunOptions.md) | 1572 | — | — |
| [_SyncPageMaps](../entities/SyncPageMaps.md) | 1595 | — | — |
| [_ExtractedSyncInventory](../entities/ExtractedSyncInventory.md) | 1602 | — | — |
| [_SyncEntryPointAnalysis](../entities/SyncEntryPointAnalysis.md) | 1608 | — | — |
| [_RuntimeGraphObservations](../entities/RuntimeGraphObservations.md) | 1614 | — | — |
| [_SurfaceInitializationPlan](../entities/SurfaceInitializationPlan.md) | 1630 | — | — |
| [_PreparedSyncRun](../entities/PreparedSyncRun.md) | 1673 | — | — |
| [_GeneratedSurfaceTransition](../entities/GeneratedSurfaceTransition.md) | 1695 | — | Prior ownership proof and generated pages that cross the live boundary. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_cache_options_from_args` | `(args) -> InventoryCacheOptions` | — | — |
| `_print_cache_stats` | `(stats: InventoryCacheStats \| None, *, enabled: bool) -> None` | — | — |
| `_is_valid_manifest_hash` | `(value: object) -> bool` | — | — |
| `_invalid_manifest_hash_paths` | `(manifest: 'SyncManifest') -> list[str]` | — | — |
| `_build_manifest_from_inventory` | `(inventory: dict, src_dir: str, *, entity_page_cache: dict[tuple[str, str], str] \| None = None, entity_occurrence_page_cache: dict[tuple[str, str, int], str] \| None = None, module_page_map: dict[str, str] \| None = None, surfaces: Mapping[str, Mapping] \| None = None, generation_inputs: Mapping[str, object] \| None = None, previous_manifest: SyncManifest \| None = None, retained_page_paths: Iterable[str] \| None = None, unknown_evidence_reason: str = EVIDENCE_NOT_RECORDED, source_content_hashes: Mapping[str, str] \| None = None) -> 'SyncManifest'` | — | — |
| `_normalize_md` | `(text: str) -> str` | — | — |
| `_write_md_if_changed` | `(path: Path, text: str) -> str` | — | Write markdown only when content changes. |
| `_section_bounds` | `(lines: list[str], heading: str) -> tuple[int, int, int] \| None` | — | Return ``(heading_index, body_start, body_end)`` for a level-2 heading. |
| `_trim_blank_lines` | `(lines: list[str]) -> list[str]` | — | — |
| `_section_body` | `(markdown: str, heading: str) -> str \| None` | — | — |
| `_replace_section_body` | `(markdown: str, heading: str, body: str) -> str` | — | — |
| `_preserve_level_two_section_exact` | `(existing: str, generated: str, heading: str) -> str` | — | Splice a human-owned level-two section without normalizing its body. |
| `_is_placeholder_description` | `(value: str \| None) -> bool` | — | — |
| `_should_preserve_semantic_value` | `(existing: str \| None, generated: str \| None, old_generated: str \| None) -> bool` | — | — |
| `_split_table_row` | `(line: str) -> list[str]` | — | — |
| `_format_table_row` | `(cells: list[str]) -> str` | — | — |
| `_is_table_separator` | `(cells: list[str]) -> bool` | — | — |
| `_semantic_table_key` | `(cell: str) -> str` | — | — |
| `_table_description_cells` | `(markdown: str, heading: str) -> dict[str, str]` | — | — |
| `_preserve_table_description_cells` | `(markdown: str, heading: str, descriptions: dict[str, str], old_descriptions: dict[str, str] \| None = None) -> tuple[str, int]` | — | — |
| `_merge_semantic_markdown` | `(existing: str, generated: str, table_headings: tuple[str, ...], *, old_description: str \| None = None, old_table_descriptions: dict[str, dict[str, str]] \| None = None) -> SemanticMergeResult` | — | Preserve human-written semantic fields in regenerated wiki markdown. |
| `_merge_entity_semantics` | `(existing: str, generated: str, old_semantics: dict \| None = None) -> SemanticMergeResult` | — | — |
| `_merge_module_semantics` | `(existing: str, generated: str, old_semantics: dict \| None = None) -> SemanticMergeResult` | — | — |
| `_governance_moves_for_sync` | `(diff: SyncDiff, manifest: SyncManifest, *, entity_page_cache: Mapping[tuple[str, str], str]) -> dict[str, str]` | — | Return only unambiguous old-to-current concept locator moves. |
| `_affected_source_files` | `(diff: SyncDiff) -> set[str]` | — | — |
| `_large_diff_message` | `(diff: SyncDiff, manifest: SyncManifest) -> str \| None` | — | — |
| `_large_infrastructure_message` | `(plan: InfrastructureSyncPlan) -> str \| None` | — | — |
| `_record_page_write_state` | `(result: SyncResult \| None, state: str) -> None` | — | Fold one deterministic Markdown write state into command page counters. |
| `_collision_maps` | `(inventory: dict, src_dir: str) -> tuple[set[str], set[str], dict[tuple[str, str], str]]` | — | Return (colliding_stems, colliding_cls, entity_page_name_cache). |
| `_empty_generated_section_context` | `() -> '_GeneratedSectionContext'` | — | — |
| `_has_existing_module_dependency_sections` | `(wiki_dir: Path) -> bool` | — | — |
| `_fallback_dependency_analysis` | `(options: '_SyncRunOptions', inventory: dict, source_snapshot: SourceSnapshot \| None) -> dict` | — | — |
| `_build_generated_section_context` | `(options: '_SyncRunOptions', inventory: dict, *, call_edges: list[dict] \| None = None, dependency_analysis: dict \| None = None, source_snapshot: SourceSnapshot \| None = None) -> '_GeneratedSectionContext'` | — | — |
| `_target_entities_for_diff` | `(diff: SyncDiff, inventory: dict) -> set[tuple[str, str]]` | — | — |
| `_relationships_for_targets` | `(inventory: dict, module_page_map: dict[str, str], target_entities: set[tuple[str, str]]) -> dict` | — | — |
| `_refresh_files_for_diff` | `(diff: SyncDiff) -> list[str]` | — | — |
| `_file_entity_page_map` | `(filepath: str, file_data: dict, entity_page_cache: dict[tuple[str, str], str], entity_occurrence_page_cache: dict[tuple[str, str, int], str] \| None = None) -> dict[str, str]` | — | — |
| `_move_renamed_entity_page` | `(wiki_dir: Path, rename: tuple[str, str] \| None, current_entity_pages: set[str]) -> None` | — | — |
| `_move_renamed_module_page` | `(wiki_dir: Path, rename: tuple[str, str] \| None, current_module_pages: set[str]) -> None` | — | — |
| `_record_page_write` | `(result: SyncResult, page_kind: str, page_name: str, write_state: str, *, metadata_only: bool) -> None` | — | — |
| `_merge_entity_page` | `(ctx: _ApplyDiffContext, entity_path: Path, generated: str, old_generated_semantics: dict, cls_name: str, result: SyncResult) -> SemanticMergeResult` | — | — |
| `_merge_module_page` | `(ctx: _ApplyDiffContext, module_path: Path, generated: str, old_generated_semantics: dict, result: SyncResult) -> SemanticMergeResult` | — | — |
| `_apply_entity_page` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult, filepath: str, cls: dict, mod_page_name: str, old_generated_semantics: dict, entity_page_name: str) -> None` | — | — |
| `_apply_module_page` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult, filepath: str, file_data: dict, mod_page_name: str, old_generated_semantics: dict, file_entity_page_map: dict[str, str]) -> None` | — | — |
| `_apply_refreshed_file_pages` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult, refresh_files: list[str]) -> None` | — | — |
| `_record_unchanged_file_skips` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult, refresh_files: list[str]) -> None` | — | — |
| `_deprecate_existing_page` | `(path: Path, result: SyncResult, page_kind: str, page_name: str) -> None` | — | — |
| `_deprecate_removed_entities` | `(wiki_dir: Path, filepath: str, old_info: dict, result: SyncResult, *, retained_page_names: frozenset[str] = frozenset()) -> None` | — | — |
| `_deprecate_removed_module` | `(wiki_dir: Path, filepath: str, old_info: dict, result: SyncResult) -> None` | — | — |
| `_deprecate_removed_files` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult) -> None` | — | — |
| `_remove_deselected_file_pages` | `(ctx: _ApplyDiffContext, filepath: str, old_info: Mapping[str, object], result: SyncResult) -> None` | — | Remove generated pages whose still-existing source left the policy set. |
| `_moved_entity_retained_page_names` | `(ctx: _ApplyDiffContext, diff: SyncDiff, old_source_path: str, old_info: Mapping[str, object]) -> frozenset[str]` | — | Return moved entity pages whose current path rule keeps the locator. |
| `_removed_source_info_from_mappings` | `(manifest: SyncManifest, source_path: str) -> dict` | — | Recover page coordinates for a repair-pending removed source. |
| `_replace_generated_section` | `(existing: str, generated: str, heading: str) -> str` | — | — |
| `_record_generated_section_write` | `(result: SyncResult, diff: SyncDiff, filepath: str, page_kind: str, section_label: str, page_name: str) -> None` | — | — |
| `_refresh_entity_relationship_sections` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult) -> None` | — | — |
| `_refresh_module_dependency_sections` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult) -> None` | — | — |
| `_refresh_generated_sections` | `(ctx: _ApplyDiffContext, diff: SyncDiff, result: SyncResult) -> None` | — | — |
| `_apply_diff_page_maps` | `(inventory: dict, src_dir: str, entity_page_cache: dict[tuple[str, str], str] \| None, entity_occurrence_page_cache: dict[tuple[str, str, int], str] \| None, module_page_map: dict[str, str] \| None) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str, int], str], dict[str, str]]` | — | — |
| `_build_apply_diff_context` | `(*, wiki_dir: Path, src_dir: str, inventory: dict, manifest: SyncManifest, entity_page_cache: dict[tuple[str, str], str], entity_occurrence_page_cache: dict[tuple[str, str, int], str], module_page_map: dict[str, str], relationships: dict, generated_sections: _GeneratedSectionContext \| None, diff: SyncDiff, preserve_semantic: bool, source_selection_policy: SourceSelectionPolicy \| None) -> _ApplyDiffContext` | — | — |
| `_apply_diff` | `(diff: SyncDiff, wiki_dir: Path, inventory: dict, src_dir: str, manifest: SyncManifest, *, entity_page_cache: dict[tuple[str, str], str] \| None = None, entity_occurrence_page_cache: dict[tuple[str, str, int], str] \| None = None, module_page_map: dict[str, str] \| None = None, generated_sections: _GeneratedSectionContext \| None = None, preserve_semantic: bool = True, source_selection_policy: SourceSelectionPolicy \| None = None) -> SyncResult` | — | Regenerate pages for new/changed files, deprecate pages for removed files. |
| `_removed_entity_page_name` | `(wiki_dir: Path, cls_name: str, filepath: str, old_info: dict) -> Optional[str]` | — | Resolve the existing entity page for a class whose source file was removed. |
| `_selection_pruning_has_changes` | `(prepared: _PreparedSyncRun) -> bool` | — | — |
| `_applied_sync_has_changes` | `(options: _SyncRunOptions, prepared: _PreparedSyncRun, result: SyncResult) -> bool` | — | Return whether this command mode actually changed public wiki state. |
| `_updated_surface_policies` | `(options: _SyncRunOptions, manifest: 'SyncManifest') -> tuple[dict[str, dict], bool]` | — | — |
| `_surface_policy` | `(surfaces: Mapping[str, Mapping], key: str) -> Mapping \| None` | — | — |
| `_filtered_surface_inventory` | `(inventory: dict, *, exclude_tests: bool) -> dict` | — | — |
| `_flow_plan` | `(options: _SyncRunOptions, surfaces: Mapping[str, Mapping], entry_points: list[dict], *, allow_legacy_creation: bool) -> tuple[tuple[dict, ...], tuple[dict, ...], int]` | — | — |
| `_dependency_plan` | `(options: _SyncRunOptions, surfaces: Mapping[str, Mapping], inventory: dict, *, source_snapshot: SourceSnapshot \| None = None) -> tuple[dict, dict \| None, tuple[str, ...], tuple[str, ...], int]` | — | — |
| `_build_surface_initialization_plan` | `(options: _SyncRunOptions, manifest: 'SyncManifest', inventory: dict, entry_points: list[dict], *, source_changed: bool, api_contracts: dict \| None, generation_inputs: Mapping[str, object], source_snapshot: SourceSnapshot \| None = None) -> _SurfaceInitializationPlan` | — | — |
| `_large_surface_message` | `(plan: _SurfaceInitializationPlan, wiki_dir: Path, *, removed_pages: int = 0) -> str \| None` | — | — |
| `_exit_if_large_unforced_surface_plan` | `(options: _SyncRunOptions, plan: _SurfaceInitializationPlan, *, removed_pages: int = 0) -> None` | — | — |
| `_print_dry_run_plan` | `(options: _SyncRunOptions, diff: 'SyncDiff', application_diff: 'SyncDiff', plan: _SurfaceInitializationPlan, infrastructure_plan: InfrastructureSyncPlan, source_selection_prune: SourceSelectionPruneResult, manifest: SyncManifest, *, seed_manifest: bool, repair_only: bool, runtime_provenance_changed: bool) -> None` | — | — |
| `_surface_args` | `(value: object) -> frozenset[str]` | — | — |
| `_flow_category_args` | `(value: object) -> frozenset[str] \| None` | — | — |
| `_manifest_openapi_path` | `(manifest: 'SyncManifest') -> str \| None` | — | Return the persisted OpenAPI path, rejecting malformed v4 state. |
| `_resolve_openapi_generation_input` | `(options: _SyncRunOptions, manifest: 'SyncManifest', source_snapshot: SourceSnapshot) -> tuple[str \| None, dict[str, object]]` | — | Validate OpenAPI state before inventory/cache writes and update metadata. |
| `_linked_api_contracts` | `(contracts: Mapping[str, object], entry_points: Iterable[Mapping[str, object]]) -> dict` | — | Attach stable flow ids to operations with statically linked handlers. |
| `_sync_run_options_from_args` | `(args) -> _SyncRunOptions` | — | — |
| `_load_or_seed_manifest` | `(options: _SyncRunOptions) -> tuple[Optional['SyncManifest'], bool]` | — | — |
| `_validate_persisted_source_selection` | `(options: _SyncRunOptions, manifest: SyncManifest \| None) -> None` | — | — |
| `_extract_current_inventory` | `(options: _SyncRunOptions, *, source_snapshot: SourceSnapshot \| None = None) -> _ExtractedSyncInventory` | — | — |
| `_prepare_sync_page_maps` | `(inventory: dict) -> _SyncPageMaps` | — | — |
| `_compute_sync_diff` | `(manifest: 'SyncManifest', inventory: dict, options: _SyncRunOptions, page_maps: _SyncPageMaps, source_content_hashes: Mapping[str, str]) -> 'SyncDiff'` | — | — |
| `_generator_refresh_diff` | `(diff: 'SyncDiff', inventory: Mapping[str, Mapping]) -> 'SyncDiff'` | — | Return an apply-only diff that regenerates every live managed concept page. |
| `_mark_pending_repair_sources_changed` | `(manifest: SyncManifest, inventory: Mapping[str, Mapping], diff: 'SyncDiff') -> None` | — | Force one trusted regeneration after a provenance-only repair. |
| `_exit_if_large_unforced_diff` | `(options: _SyncRunOptions, diff: 'SyncDiff', manifest: 'SyncManifest', inventory_result: InventoryResult, infrastructure_plan: InfrastructureSyncPlan, *, include_infrastructure: bool = True) -> None` | — | — |
| `_apply_sync_changes` | `(options: _SyncRunOptions, manifest: 'SyncManifest', inventory: dict, diff: 'SyncDiff', page_maps: _SyncPageMaps, surface_plan: _SurfaceInitializationPlan, graph_observations: _RuntimeGraphObservations, infrastructure_plan: InfrastructureSyncPlan, source_snapshot: SourceSnapshot, inventory_result: InventoryResult, source_selection_prune: SourceSelectionPruneResult, *, log_diff: SyncDiff \| None = None, apply_infrastructure: bool = True) -> 'SyncResult'` | — | — |
| `_apply_source_selection_prune` | `(wiki_dir: Path, prune: SourceSelectionPruneResult, page_maps: _SyncPageMaps, result: SyncResult) -> None` | — | — |
| `_planned_generated_surface_prune` | `(wiki_dir: Path, source_snapshot: SourceSnapshot, inventory: Mapping[str, Mapping], graph_observations: _RuntimeGraphObservations, *, force: bool = False, defer_detector_retirement: bool = False) -> _GeneratedSurfaceTransition` | — | Prove managed live workflows and generated pages absent from the live set. |
| `_generated_surface_pages_without_index` | `(wiki_dir: Path) -> tuple[str, ...]` | — | Return recognizable generated flow/workflow pages lacking ownership state. |
| `_has_generated_surface_shape` | `(kind: PageKind, markdown: str) -> bool` | — | — |
| `_has_neutral_generated_behavior` | `(kind: PageKind, markdown: str) -> bool` | — | — |
| `_apply_surface_page_changes` | `(options: _SyncRunOptions, inventory: dict, page_maps: _SyncPageMaps, surface_plan: _SurfaceInitializationPlan, *, graph_observations: _RuntimeGraphObservations \| None = None, source_snapshot: SourceSnapshot \| None = None, result: SyncResult \| None = None) -> None` | — | — |
| `_detect_sync_entry_points` | `(inventory: dict, src_dir: str, *, source_snapshot: SourceSnapshot \| None = None) -> _SyncEntryPointAnalysis` | — | — |
| `_selected_sync_flow_entries` | `(options: _SyncRunOptions, surface_plan: _SurfaceInitializationPlan) -> list[dict]` | — | — |
| `_canonical_sync_surface_flow_targets` | `(options: _SyncRunOptions, entry_points: list[dict], surface_plan: _SurfaceInitializationPlan) -> list[dict]` | — | Select detected metadata for extant and about-to-be-created flow pages. |
| `_canonical_surface_flow_entries` | `(inventory: Mapping[str, Mapping], entry_points: list[dict], rendering_flows: list[dict], rendering_data_flows: list[dict]) -> list[dict]` | — | Project sync observations into bootstrap's canonical flow metadata. |
| `_build_sync_graph_observations` | `(options: _SyncRunOptions, inventory: dict, source_snapshot: SourceSnapshot, entry_points: list[dict], entrypoint_observations: dict, surface_plan: _SurfaceInitializationPlan, dependency_analysis: dict \| None, *, data_effect_observations: Mapping \| None = None, import_observations: Mapping \| None = None) -> _RuntimeGraphObservations` | — | — |
| `_print_sync_summary` | `(result: 'SyncResult', diff: 'SyncDiff', infrastructure_plan: InfrastructureSyncPlan \| None = None) -> None` | — | — |
| `_print_surface_summary` | `(plan: _SurfaceInitializationPlan) -> None` | — | — |
| `_discover_infrastructure_plan` | `(source_snapshot: SourceSnapshot, generation_inputs: Mapping[str, object]) -> InfrastructureSyncPlan` | — | — |
| `_with_planned_infrastructure_state` | `(plan: _SurfaceInitializationPlan, infrastructure_plan: InfrastructureSyncPlan) -> _SurfaceInitializationPlan` | — | — |
| `_with_planned_infrastructure_deselection_state` | `(plan: _SurfaceInitializationPlan, infrastructure_plan: InfrastructureSyncPlan) -> _SurfaceInitializationPlan` | — | — |
| `_prepare_sync_run` | `(options: _SyncRunOptions) -> _PreparedSyncRun \| None` | — | — |
| `_preflight_sync_governance` | `(wiki_dir: Path, manifest: SyncManifest) -> None` | — | Reject corrupt or missing committed governance before page mutation. |
| `_infrastructure_page_path` | `(wiki_dir: Path, record: Mapping[str, object]) -> Path` | — | — |
| `_merge_infrastructure_notes` | `(existing: str \| None, generated: str) -> str` | — | — |
| `_record_infrastructure_write` | `(result: SyncResult, state: str, *, label: str) -> None` | — | — |
| `_write_current_infrastructure_page` | `(options: _SyncRunOptions, plan: InfrastructureSyncPlan, result: SyncResult, source_path: str, *, module_page_map: Mapping[str, str], unsupported_sources: Mapping[str, Mapping[str, object]], semantic_source: Path \| None = None) -> Path` | — | — |
| `_infrastructure_tombstone_markdown` | `(source_path: str, record: Mapping[str, object]) -> str` | — | — |
| `_qualify_infrastructure_page_drift` | `(options: _SyncRunOptions, plan: InfrastructureSyncPlan, *, page_maps: _SyncPageMaps, source_snapshot: SourceSnapshot) -> InfrastructureSyncPlan` | — | Promote page drift without treating the semantic Notes body as generated. |
| `_apply_infrastructure_plan` | `(options: _SyncRunOptions, plan: InfrastructureSyncPlan, result: SyncResult, *, page_maps: _SyncPageMaps, source_snapshot: SourceSnapshot) -> None` | — | — |
| `_apply_deselected_infrastructure_pages` | `(options: _SyncRunOptions, plan: InfrastructureSyncPlan, result: SyncResult) -> None` | — | — |
| `_apply_current_infrastructure_plan` | `(options: _SyncRunOptions, plan: InfrastructureSyncPlan, result: SyncResult, *, page_maps: _SyncPageMaps, source_snapshot: SourceSnapshot) -> None` | — | — |
| `_apply_prepared_sync` | `(options: _SyncRunOptions, prepared: _PreparedSyncRun) -> SyncResult` | — | — |
| `_finalize_prepared_sync` | `(options: _SyncRunOptions, prepared: _PreparedSyncRun, result: SyncResult, *, target_wiki_dir: Path \| None = None, dry_run: bool = False) -> KnowledgeCommitResult` | — | — |
| `_print_selection_prune_summary` | `(prepared: _PreparedSyncRun) -> None` | — | — |
| `_print_sync_artifact_actions` | `(result: KnowledgeCommitResult) -> None` | — | — |
| `_run_sync_dry_run` | `(options: _SyncRunOptions, prepared: _PreparedSyncRun) -> None` | — | — |
| `_unsafe_dry_run_symlink` | `(wiki_dir: Path) -> str \| None` | — | Return the first symlink that would escape an isolated preview tree. |
| `_enforce_sync_write_safety` | `(options: _SyncRunOptions, prepared: _PreparedSyncRun) -> None` | — | Apply broad-change guards before a prepared sync can mutate the wiki. |
| `run` | `(args) -> None` | — | — |
| `_preserve_index_custom_sections` | `(old_md: str, new_md: str) -> str` | — | — |
| `_overlay_live_index_metadata` | `(existing: list[dict], live: Iterable[Mapping], *, key: str) -> list[dict]` | — | Retain existing page coverage while preferring canonical live metadata. |
| `_sync_workflow_index_entries` | `(wiki_dir: Path, inventory: dict) -> list[dict]` | — | — |
| `_sync_flow_index_entries` | `(wiki_dir: Path, graph_observations: _RuntimeGraphObservations, *, source_overrides: Mapping[str, str] \| None = None) -> list[dict]` | — | — |
| `_retained_initialization_source_overrides` | `(options: _SyncRunOptions, plan: _SurfaceInitializationPlan) -> dict[str, str]` | — | Keep prior generated ownership for surfaces deferred by initialization. |
| `_initialization_flow_entries` | `(options: _SyncRunOptions, graph_observations: _RuntimeGraphObservations, plan: _SurfaceInitializationPlan) -> list[dict]` | — | Retain prior rich flow metadata unless flow initialization replaces it. |
| `_sync_infrastructure_index_entries` | `(wiki_dir: Path, plan: InfrastructureSyncPlan) -> list[dict]` | — | — |
| `_initialization_infrastructure_index_entries` | `(wiki_dir: Path, plan: InfrastructureSyncPlan) -> list[dict]` | — | Retain the persisted infrastructure metadata while source work is deferred. |
| `_rebuild_index` | `(wiki_dir: Path, inventory: dict, src_dir: str, *, entity_page_cache: dict[tuple[str, str], str] \| None = None, entity_occurrence_page_cache: dict[tuple[str, str, int], str] \| None = None, module_page_map: dict[str, str] \| None = None, preserve_semantic: bool = True, workflow_entries: list[dict] \| None = None, flow_entries: list[dict] \| None = None, infra_entries: list[dict] \| None = None) -> str` | — | Regenerate index.md from the live inventory. |
| `_rebuild_surface_only_index` | `(wiki_dir: Path, manifest: SyncManifest, *, preserve_semantic: bool = True, workflow_entries: list[dict] \| None = None, flow_entries: list[dict] \| None = None, infra_entries: list[dict] \| None = None, log_present: bool \| None = None) -> str` | — | Re-index only pages already present during source-deferred backfill. |
| `_list_existing_pages` | `(directory: Path, extra_key: str) -> list[dict]` | — | Return a list of ``{"name": stem}`` dicts for every .md file in *directory*. |
| `_markdown_title` | `(path: Path) -> str` | — | — |
| `_list_existing_architecture_pages` | `(wiki_dir: Path) -> list[dict]` | — | Return ``{"name", "page"}`` entries for architecture pages present on disk. |
| `_generated_page_entry` | `(path: Path) -> str` | — | Return a generated flow/workflow entry point without interpreting prose. |
| `_generated_page_code_field` | `(path: Path, label: str) -> str` | — | Return one exact backtick-delimited generated metadata field. |
| `_list_existing_workflow_pages` | `(directory: Path) -> list[dict]` | — | Return disk-backed workflow metadata used by source-deferred indexing. |
| `_list_existing_infrastructure_pages` | `(directory: Path) -> list[dict]` | — | Return disk-backed infrastructure metadata during source deferral. |
| `_list_existing_flow_pages` | `(directory: Path, *, source_overrides: Mapping[str, str] \| None = None) -> list[dict]` | — | Return disk-backed flow metadata for generated index reconstruction. |
| `_preserve_flow_behavior` | `(old_md: str, new_md: str) -> str` | — | Carry a human-edited ``## Behavior`` section into regenerated flow md. |
| `_api_operations_for_flow` | `(contracts: Mapping[str, object] \| None, entry_point: Mapping[str, object]) -> list[dict]` | — | — |
| `_regenerate_workflow_pages` | `(options: _SyncRunOptions, inventory: dict, module_page_map: dict[str, str], *, workflows_enabled: bool, managed_page_paths: frozenset[str], new_page_paths: frozenset[str], result: SyncResult \| None = None) -> int` | — | Refresh proven generated workflows and create explicitly planned pages. |
| `_regenerate_flow_pages` | `(options: _SyncRunOptions, inventory: dict, module_page_map: dict[str, str], *, entry_points: list[dict] \| None = None, allow_create: bool = False, api_contracts: Mapping[str, object] \| None = None, data_flow_enabled: bool = True, call_edges: list[dict] \| None = None, evaluated_flows: list[dict] \| None = None, evaluated_data_flows: list[dict] \| None = None, source_snapshot: SourceSnapshot \| None = None, managed_page_paths: frozenset[str] = frozenset(), new_page_paths: frozenset[str] = frozenset(), result: SyncResult \| None = None) -> int` | — | Regenerate flow pages from the current inventory, preserving Behavior. |
| `_regenerate_api_contracts_page` | `(options: _SyncRunOptions, page_maps: _SyncPageMaps, plan: _SurfaceInitializationPlan, *, result: SyncResult \| None = None) -> int` | — | Regenerate the canonical mixed API surface while preserving Notes. |
| `_preserve_notes` | `(old_md: str, new_md: str) -> str` | — | Carry a human-edited ``## Notes`` section into regenerated architecture md. |
| `_regenerate_dependency_pages` | `(options: _SyncRunOptions, inventory: dict, module_page_map: dict[str, str], *, dependency_analysis: dict \| None = None, source_snapshot: SourceSnapshot \| None = None, target_pages: Iterable[str] \| None = None, detail: str = 'auto', result: SyncResult \| None = None) -> int` | — | Regenerate dependencies.md / load-order.md, preserving ``## Notes``. |
| `_append_log` | `(wiki_dir: Path, src_dir: str, diff: SyncDiff, result: SyncResult, *, source_snapshot: SourceSnapshot, generation_inputs: Mapping[str, object], plugin_lock_path: str \| None, plugin_lock_hash: str \| None, surface_plan: _SurfaceInitializationPlan \| None = None, infrastructure_plan: InfrastructureSyncPlan \| None = None, source_selection_prune: SourceSelectionPruneResult \| None = None, source_changes_applied: bool = True, infrastructure_changes_applied: bool = True) -> None` | — | — |
