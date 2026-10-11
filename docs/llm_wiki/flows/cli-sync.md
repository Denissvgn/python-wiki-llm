# sync

**Entry point:** `run` (`cli`)
**Source:** [sync_cmd](../modules/sync_cmd.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 53 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
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
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)
- [runtime_output](../modules/runtime_output.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_retained_links](../modules/sync_retained_links.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _sync_run_options_from_args
    participant p2 as maintenance_write_operation
    participant p3 as _run_sync_options
    participant p4 as print (src/llm_wiki_cli/commands/sync_cmd.py:run)
    participant p5 as sys.exit (src/llm_wiki_cli/commands/sync_cmd.py:run)
    participant p6 as getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)
    participant p7 as _absolute_path
    participant p8 as _prepare_sync_run
    participant p9 as Path (src/llm_wiki_cli/commands…ync_run_options_from_args)
    participant p10 as Path (src/llm_wiki_cli/services…intenance_write_operation)
    participant p11 as print (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)
    participant p12 as guard_maintenance_owner
    participant p13 as sys.exit (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)
    participant p14 as bool (src/llm_wiki_cli/commands…ync_run_options_from_args)
    participant p15 as load_adoption_marker
    participant p16 as isinstance (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)
    participant p17 as _print_sync_artifact_actions
    participant p18 as governance_writer_lock
    participant p19 as storage_writer_lock
    participant p20 as _print_cache_stats
    participant p21 as _cache_options_from_args
    participant p22 as write_basis.assert_current
    participant p23 as InventoryCacheOptions
    p0->>p1: _sync_run_options_from_args
    p0->>p2: maintenance_write_operation
    p0->>p3: _run_sync_options
    p0-->>p4: print (src/llm_wiki_cli/commands/sync_cmd.py:run)(..., file=sys.stderr)
    p0-->>p5: sys.exit (src/llm_wiki_cli/commands/sync_cmd.py:run)(2)
    p1-->>p6: getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'src_dir', '.')
    p2->>p7: _absolute_path
    p3->>p8: _prepare_sync_run
    p1-->>p9: Path (src/llm_wiki_cli/commands…ync_run_options_from_args)(getattr(...))
    p2-->>p10: Path (src/llm_wiki_cli/services…intenance_write_operation)(wiki_dir)
    p3-->>p11: print (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)(..., file=sys.stderr)
    p1-->>p6: getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'wiki_dir', 'docs/llm_wiki')
    p2->>p12: guard_maintenance_owner
    p3-->>p13: sys.exit (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)(2)
    p1-->>p14: bool (src/llm_wiki_cli/commands…ync_run_options_from_args)(getattr(...))
    p2->>p15: load_adoption_marker
    p3-->>p16: isinstance (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)(prepared, _ReusedSync)
    p1-->>p6: getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'dry_run', False)
    p2->>p12: guard_maintenance_owner
    p3->>p17: _print_sync_artifact_actions
    p1-->>p14: bool (src/llm_wiki_cli/commands…ync_run_options_from_args)(getattr(...))
    p2->>p18: governance_writer_lock
    p3-->>p11: print (src/llm_wiki_cli/commands…_cmd.py:_run_sync_options)(...)
    p1-->>p6: getattr (src/llm_wiki_cli/commands…ync_run_options_from_args)(args, 'no_plugins', False)
    p2->>p19: storage_writer_lock
    p3->>p20: _print_cache_stats
    p1->>p21: _cache_options_from_args
    p2->>p12: guard_maintenance_owner
    p3-->>p22: write_basis.assert_current
    p1->>p23: InventoryCacheOptions
```

> Call sequence diagram shows 30 of 5019 interactions; 4989 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 14 of 1756 (1742 omitted); unresolved 1 of 1549 (1548 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/commands/sync_cmd.py:_cache_options_from_args` | 10 | [src/llm_wiki_cli/services/inventory_cache.py](../modules/inventory_cache.md) | internal | 1 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | - | external | 8 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | [src/llm_wiki_cli/services/runtime_output.py](../modules/runtime_output.md) | internal | 2 |
| `src/llm_wiki_cli/services/inventory_cache.py:cache_options_from_args` | 11 | [src/llm_wiki_cli/services/inventory_cache.py](../modules/inventory_cache.md) | internal | 1 |
| `src/llm_wiki_cli/commands/sync_cmd.py:_sync_run_options_from_args` | 2 | - | external | 31 |
| `src/llm_wiki_cli/commands/sync_cmd.py:_sync_run_options_from_args` | 2 | [src/llm_wiki_cli/services/extraction_jobs.py](../modules/extraction_jobs.md) | internal | 1 |
| `src/llm_wiki_cli/services/extraction_jobs.py:extraction_job_request_from_args` | 28 | - | external | 5 |
> Omission summary shows 8 of 1092 groups; 1084 further groups are not expanded here. Counts above include all omitted interactions.
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
    click s1 "../modules/sync_cmd.md"
    click s2 "../modules/sync_cmd.md"
    click s10 "../modules/sync_cmd.md"
    click s11 "../modules/inventory_cache.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `options.wiki_dir`, `options.dry_run`, `sys` | - | - |
| `_sync_run_options_from_args` | `args` | `sys`, `sys`, `sys`, `print_extraction_job_plan` | - | `_SyncRunOptions(...)` |
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
| run | _sync_run_options_from_args | 4871 | `_sync_run_options_from_args(args)` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2362 | `getattr(args, 'src_dir', '.')` |
| _sync_run_options_from_args | Path (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2363 | `Path(getattr(...))` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2363 | `getattr(args, 'wiki_dir', 'docs/llm_wiki')` |
| _sync_run_options_from_args | bool (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2364 | `bool(getattr(...))` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2364 | `getattr(args, 'dry_run', False)` |
| _sync_run_options_from_args | bool (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2365 | `bool(getattr(...))` |
| _sync_run_options_from_args | getattr (src/llm_wiki_cli/commands…ync_run_options_from_args) | 2365 | `getattr(args, 'no_plugins', False)` |
| _sync_run_options_from_args | _cache_options_from_args | 2366 | `_cache_options_from_args(args)` |
| _cache_options_from_args | cache_options_from_args | 291 | `cache_options_from_args(args)` |
| cache_options_from_args | bool (src/llm_wiki_cli/services…y:cache_options_from_args) | 311 | `bool(getattr(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 4878 |
| output | `print` | `_sync_run_options_from_args` | 2383 |
| output | `print` | `_sync_run_options_from_args` | 2389 |
| output | `print` | `_sync_run_options_from_args` | 2395 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_sync_run_options_from_args` | `getattr` | 2362 |
| external_call | `_sync_run_options_from_args` | `getattr` | 2363 |
| external_call | `_sync_run_options_from_args` | `getattr` | 2364 |
| external_call | `_sync_run_options_from_args` | `getattr` | 2365 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Classifies the wiki lifecycle, validates the persisted source-selection and
generation policy, captures one live source snapshot, and computes source,
infrastructure, and optional-surface changes. Dry-run prints the complete plan;
broad unforced updates stop before writes. An applied run preserves supported
semantic prose, rebuilds navigation, appends the log, and commits mutually
consistent generated state so repeating the same command converges to no work.
