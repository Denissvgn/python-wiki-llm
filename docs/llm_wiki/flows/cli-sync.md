# sync

**Entry point:** `run` (`cli`)
**Source:** [sync_cmd](../modules/sync_cmd.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [api_contracts](../modules/api_contracts.md), and 71 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [api_contracts](../modules/api_contracts.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [current_contracts](../modules/current_contracts.md)
- [data_flow](../modules/data_flow.md)
- [dockerfile_parser](../modules/dockerfile_parser.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [normalization_diagnostics](../modules/normalization_diagnostics.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [runtime_output](../modules/runtime_output.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_generated_sections](../modules/sync_generated_sections.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_recovery](../modules/sync_recovery.md)
- [sync_retained_links](../modules/sync_retained_links.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)
- [yaml_formats](../modules/yaml_formats.md)
- [yaml_syntax](../modules/yaml_syntax.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _sync_run_options_from_args
    participant p2 as maintenance_write_operation
    participant p3 as _run_sync_options
    participant p4 as _absolute_path
    participant p5 as _prepare_sync_run
    participant p6 as guard_maintenance_owner
    participant p7 as governance_writer_lock
    participant p8 as storage_writer_lock
    participant p9 as prepare_boundary
    participant p10 as snapshot_wiki
    participant p11 as _cache_options_from_args
    participant p12 as _recovery_directory
    participant p13 as extraction_job_request_from_args
    participant p14 as save_recovery_snapshot
    participant p15 as report_capture
    participant p16 as _print_cache_stats
    participant p17 as _run_prepared_sync
    participant p18 as repair_paths
    participant p19 as validate_source_root
    participant p20 as cache_options_from_args
    participant p21 as validate_path
    participant p22 as assert_no_pending_page_moves
    participant p23 as _require
    participant p24 as ensure_guarded_directory
    participant p25 as _load_or_seed_manifest
    participant p26 as _repair_path
    participant p27 as guard_incomplete_bootstrap
    participant p28 as load_adoption_marker
    participant p29 as print (src/llm_wiki_cli/commands/sync_cmd.py:run)
    participant p30 as application.changed_files.extend
    p0->>p1: _sync_run_options_from_args
    p0->>p2: maintenance_write_operation
    p0->>p3: _run_sync_options
    p2->>p4: _absolute_path
    p3->>p5: _prepare_sync_run
    p2->>p6: guard_maintenance_owner
    p2->>p7: governance_writer_lock
    p2->>p8: storage_writer_lock
    p3->>p9: prepare_boundary
    p2->>p10: snapshot_wiki
    p1->>p11: _cache_options_from_args
    p2->>p12: _recovery_directory
    p1->>p13: extraction_job_request_from_args
    p2->>p14: save_recovery_snapshot
    p3->>p15: report_capture
    p3->>p16: _print_cache_stats
    p3->>p17: _run_prepared_sync
    p1->>p18: repair_paths
    p1->>p19: validate_source_root
    p11->>p20: cache_options_from_args
    p19->>p21: validate_path
    p5->>p22: assert_no_pending_page_moves
    p9->>p23: _require
    p14->>p24: ensure_guarded_directory
    p5->>p25: _load_or_seed_manifest
    p18->>p26: _repair_path
    p6->>p27: guard_incomplete_bootstrap
    p6->>p28: load_adoption_marker
    p0-->>p29: print (src/llm_wiki_cli/commands/sync_cmd.py:run)(..., file=sys.stderr)
    p3-->>p30: application.changed_files.extend(selected)
```

> Call sequence diagram shows 30 of 6153 interactions; 6123 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 2166 (2165 omitted); unresolved 1 of 1849 (1848 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/commands/sync_cmd.py:_sync_run_options_from_args` | 2 | - | external | 43 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | - | external | 8 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | [src/llm_wiki_cli/services/runtime_output.py](../modules/runtime_output.md) | internal | 2 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | [src/llm_wiki_cli/services/inventory_cache.py](../modules/inventory_cache.md) | internal | 1 |
| `src/llm_wiki_cli/commands/sync_cmd.py:_sync_run_options_from_args` | 2 | [src/llm_wiki_cli/services/inventory_cache.py](../modules/inventory_cache.md) | internal | 1 |
| `src/llm_wiki_cli/services/extraction_jobs.py:extraction_job_request_from_args` | 28 | - | external | 5 |
| `src/llm_wiki_cli/services/extraction_jobs.py:extraction_job_request_from_args` | 28 | [src/llm_wiki_cli/services/extraction_jobs.py](../modules/extraction_jobs.md) | internal | 1 |
> Omission summary shows 8 of 1376 groups; 1368 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _sync_run_options_from_args"]
    s3["3. getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s4["4. Path (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s5["5. getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s6["6. bool (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s7["7. getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s8["8. bool (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s9["9. getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)"]
    s10["10. _cache_options_from_args"]
    s11["11. cache_options_from_args"]
    s12["12. bool (src/llm_wiki_cli/services…y:cache_options_from_args)"]
    s1 -->|"_sync_run_options_from_args(args)"| s2
    s2 -. "getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'src_dir', '.')" .-> s3
    s2 -. "Path (src/llm_wiki_cli/commands…ync_run_options_from_args)(getattr(...))" .-> s4
    s2 -. "getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'wiki_dir', 'docs/llm_wiki')" .-> s5
    s2 -. "bool (src/llm_wiki_cli/commands…ync_run_options_from_args)(getattr(...))" .-> s6
    s2 -. "getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'dry_run', False)" .-> s7
    s2 -. "bool (src/llm_wiki_cli/commands…ync_run_options_from_args)(getattr(...))" .-> s8
    s2 -. "getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'no_plugins', False)" .-> s9
    s2 -->|"_cache_options_from_args(args)"| s10
    s10 -->|"cache_options_from_args(args)"| s11
    s11 -. "bool (src/llm_wiki_cli/services…y:cache_options_from_args)(getattr(...))" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s2 -. "output print" .-> b1
    b2["output print"]
    s2 -. "output print" .-> b2
    b3["output print"]
    s2 -. "output print" .-> b3
    b4["output print"]
    s2 -. "output print" .-> b4
    click s1 "../modules/sync_cmd.md"
    click s2 "../modules/sync_cmd.md"
    click s10 "../modules/sync_cmd.md"
    click s11 "../modules/inventory_cache.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `options.wiki_dir`, `options.dry_run`, `sys` | - | - |
| `_sync_run_options_from_args` | `args` | `ScopedRepairError`, `sys`, `sys`, `sys`, `sys`, `print_extraction_job_plan` | - | `_SyncRunOptions(...)` |
| `getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `Path (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `bool (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `bool (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)` | - | - | - | - |
| `_cache_options_from_args` | `args` | - | - | `cache_options_from_args(...)` |
| `cache_options_from_args` | `args` | `stderr_warning` | - | `InventoryCacheOptions(...)` |
| `bool (src/llm_wiki_cli/services…y:cache_options_from_args)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _sync_run_options_from_args | 5380 | `_sync_run_options_from_args(args)` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2425 | `getattr(args, 'src_dir', '.')` |
| _sync_run_options_from_args | Path (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2426 | `Path(getattr(...))` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2426 | `getattr(args, 'wiki_dir', 'docs/llm_wiki')` |
| _sync_run_options_from_args | bool (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2427 | `bool(getattr(...))` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2427 | `getattr(args, 'dry_run', False)` |
| _sync_run_options_from_args | bool (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2428 | `bool(getattr(...))` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2428 | `getattr(args, 'no_plugins', False)` |
| _sync_run_options_from_args | _cache_options_from_args | 2429 | `_cache_options_from_args(args)` |
| _cache_options_from_args | cache_options_from_args | 306 | `cache_options_from_args(args)` |
| cache_options_from_args | bool (src/llm_wiki_cli/services…y:cache_options_from_args) | 312 | `bool(getattr(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 5387 |
| output | `print` | `_sync_run_options_from_args` | 2454 |
| output | `print` | `_sync_run_options_from_args` | 2457 |
| output | `print` | `_sync_run_options_from_args` | 2463 |
| output | `print` | `_sync_run_options_from_args` | 2469 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_sync_run_options_from_args` | `getattr` | 2425 |
| external_call | `_sync_run_options_from_args` | `getattr` | 2426 |
| external_call | `_sync_run_options_from_args` | `getattr` | 2427 |
| external_call | `_sync_run_options_from_args` | `getattr` | 2428 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Classifies the wiki lifecycle, validates the persisted source-selection and
generation policy, captures one live source snapshot, and computes source,
infrastructure, and optional-surface changes. Dry-run prints the complete plan;
broad unforced updates stop before page application. An applied run preserves supported
semantic prose, rebuilds navigation, appends the log, and commits mutually
consistent generated state so repeating the same command converges to no work.

Removed declarations in surviving documentable modules are retained as qualified
source history. Exact recorded owner revival can restore live generation without
inventing lifecycle or approval. Previously owned empty modules receive scoped parser qualification; their
module page remains current while removed declarations become retained history.
Parser/coverage gaps and ambiguous duplicate custody still stop before writes.

An applied operation retains exact bytes and identities for newly created
Markdown pages. Rejected publication emits the recovery journal hash and leaves
mandatory ownership checks active. Explicit `maintenance recover-new-pages`
previews and removes only unchanged new pages before retry; readers and sync
never perform that recovery implicitly. Adopted full-preimage recovery remains
available independently.

Broad-update errors distinguish source changes from additional generator
refresh inputs and expose bounded path samples with omitted counts. A copied,
platform-quoted preview preserves the caller's roots and planning bindings;
dry-run reveals every affected input path and its source-change reason. Source
inputs are not rewritten, and a preview never grants broad-write approval.

After successful staging, a broad preview explains how to explicitly authorize
the reviewed update by replacing dry-run with force. Force computes a fresh plan;
source, helper, selection, provider or wiki changes require renewed preview and
review. Matching generated page writes are skipped, while changed generated
content and current evidence are committed through the existing owning path.
The normal repeat run leaves active wiki state unchanged; adopted maintenance
may separately capture a recovery preimage outside the wiki. Ownership,
integrity and explicit recovery requirements remain active throughout.

Current deep normalization can also schedule an unchanged source with captured
invalid evidence for an owning refresh. The preview distinguishes this from
source edits and generator transitions, and broad guards remain active. Full
reconciliation replaces only evidence supported by fresh observations, including
same-version repairs, without a fabricated source edit or a scoped-write promise.

An explicit `--no-plugins --repair-evidence` request limits application to selected
unchanged sources with complete current producer commitments and adopted custody.
A producer transition must reproduce retained known observations. Identical
executable observations can re-anchor to their actual captured issuer, reopening
review without losing history or acknowledging it.
It repairs existing module/entity evidence together and preserves other unknowns.
Full discovery, analysis, graph reconciliation, native artifacts, an isolated
preflight copy and recovery preimages still require global work. Wider logical or
typed-graph changes refuse; broad review remains active. A matching known selected
basis causes no scoped publication, and success does not certify unselected
source evidence. Repeat strict validation after the repair.

Help connects captured evidence diagnosis and raw inspection to previewing the
ordinary owning update. Broad changes still require review and explicit authority;
force is never implied by a failure or an upgrade. Fresh malformed evidence stays
blocking. After repair, supported prose review, re-anchor and strict validation
retain their established ownership and integrity checks.
