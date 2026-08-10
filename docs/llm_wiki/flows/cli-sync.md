# sync

**Entry point:** `run` (`cli`)
**Source:** [sync_cmd](../modules/sync_cmd.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 39 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
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
- [markdown_sections](../modules/markdown_sections.md)
- [module_maps](../modules/module_maps.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [relationships](../modules/relationships.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _sync_run_options_from_args
    participant p2 as getattr
    participant p3 as Path
    participant p4 as bool
    participant p5 as _cache_options_from_args
    participant p6 as InventoryCacheOptions
    participant p7 as extraction_job_request_from_args
    participant p8 as max
    participant p9 as int
    participant p10 as ExtractionJobRequest
    p0->>p1: _sync_run_options_from_args
    p1-->>p2: getattr
    p1-->>p3: Path
    p1-->>p2: getattr
    p1-->>p4: bool
    p1-->>p2: getattr
    p1-->>p4: bool
    p1-->>p2: getattr
    p1->>p5: _cache_options_from_args
    p5-->>p4: bool
    p5-->>p2: getattr
    p5->>p6: InventoryCacheOptions
    p5-->>p4: bool
    p5-->>p2: getattr
    p5-->>p4: bool
    p5-->>p2: getattr
    p5-->>p2: getattr
    p1->>p6: InventoryCacheOptions
    p1-->>p4: bool
    p1-->>p2: getattr
    p1-->>p2: getattr
    p1->>p7: extraction_job_request_from_args
    p7-->>p8: max
    p7-->>p9: int
    p7-->>p2: getattr
    p7-->>p2: getattr
    p7-->>p9: int
    p7->>p10: ExtractionJobRequest
    p1-->>p2: getattr
    p1-->>p2: getattr
```

> Call sequence diagram shows 30 of 5498 interactions; 5468 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _sync_run_options_from_args"]
    s3["3. getattr"]
    s4["4. Path"]
    s5["5. getattr"]
    s6["6. bool"]
    s7["7. getattr"]
    s8["8. bool"]
    s9["9. getattr"]
    s10["10. _cache_options_from_args"]
    s11["11. bool"]
    s12["12. getattr"]
    s1 -->|"_sync_run_options_from_args(args)"| s2
    s2 -. "getattr(args, 'src_dir', '.')" .-> s3
    s2 -. "Path(getattr(...))" .-> s4
    s2 -. "getattr(args, 'wiki_dir', 'docs/llm_wiki')" .-> s5
    s2 -. "bool(getattr(...))" .-> s6
    s2 -. "getattr(args, 'dry_run', False)" .-> s7
    s2 -. "bool(getattr(...))" .-> s8
    s2 -. "getattr(args, 'no_plugins', False)" .-> s9
    s2 -->|"_cache_options_from_args(args)"| s10
    s10 -. "bool(getattr(...))" .-> s11
    s10 -. "getattr(args, 'cache_stats', False)" .-> s12
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
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `ApiContractError`, `GeneratedSurfacePruneError`, `GovernanceError`, `InfrastructureSyncError`, `SyncRuntimeRefreshError`, `sys`, `options.dry_run` | - | `none`, `none` |
| `_sync_run_options_from_args` | `args` | `sys`, `sys`, `sys`, `print_extraction_job_plan` | - | `_SyncRunOptions(...)` |
| `getattr` | - | - | - | - |
| `Path` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `_cache_options_from_args` | `args` | - | - | `InventoryCacheOptions(...)` |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _sync_run_options_from_args | 4464 | `_sync_run_options_from_args(args)` |
| _sync_run_options_from_args | getattr | 2272 | `getattr(args, 'src_dir', '.')` |
| _sync_run_options_from_args | Path | 2273 | `Path(getattr(...))` |
| _sync_run_options_from_args | getattr | 2273 | `getattr(args, 'wiki_dir', 'docs/llm_wiki')` |
| _sync_run_options_from_args | bool | 2274 | `bool(getattr(...))` |
| _sync_run_options_from_args | getattr | 2274 | `getattr(args, 'dry_run', False)` |
| _sync_run_options_from_args | bool | 2275 | `bool(getattr(...))` |
| _sync_run_options_from_args | getattr | 2275 | `getattr(args, 'no_plugins', False)` |
| _sync_run_options_from_args | _cache_options_from_args | 2276 | `_cache_options_from_args(args)` |
| _cache_options_from_args | bool | 264 | `bool(getattr(...))` |
| _cache_options_from_args | getattr | 264 | `getattr(args, 'cache_stats', False)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 4474 |
| output | `print` | `_sync_run_options_from_args` | 2293 |
| output | `print` | `_sync_run_options_from_args` | 2299 |
| output | `print` | `_sync_run_options_from_args` | 2305 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_sync_run_options_from_args` | `getattr` | 2272 |
| unresolved_call | `_sync_run_options_from_args` | `getattr` | 2273 |
| unresolved_call | `_sync_run_options_from_args` | `getattr` | 2274 |
| unresolved_call | `_sync_run_options_from_args` | `getattr` | 2275 |
| unresolved_call | `_cache_options_from_args` | `getattr` | 264 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Classifies the wiki lifecycle, validates the persisted source-selection and
generation policy, captures one live source snapshot, and computes source,
infrastructure, and optional-surface changes. Dry-run prints the complete plan;
broad unforced updates stop before writes. An applied run preserves supported
semantic prose, rebuilds navigation, appends the log, and commits mutually
consistent generated state so repeating the same command converges to no work.
