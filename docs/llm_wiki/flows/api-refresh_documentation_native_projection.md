# refresh_documentation_native_projection

**Entry point:** `refresh_documentation_native_projection` (`api`)
**Source:** [documentation_native](../modules/documentation_native.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [api_contracts](../modules/api_contracts.md), and 70 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [api_contracts](../modules/api_contracts.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dockerfile_parser](../modules/dockerfile_parser.md)
- [documentation_native](../modules/documentation_native.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [normalization_diagnostics](../modules/normalization_diagnostics.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_contracts](../modules/python_contracts.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [python_observations](../modules/python_observations.md)
- [section_ownership](../modules/section_ownership.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
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
    participant p0 as refresh_documentation_native_projection
    participant p1 as load_adoption_marker
    participant p2 as maintenance_write_operation
    participant p3 as _refresh_documentation_native_projection
    participant p4 as _absolute_path
    participant p5 as _validated_directory
    participant p6 as guard_maintenance_owner
    participant p7 as _refresh_manifest_version
    participant p8 as governance_writer_lock
    participant p9 as read_guarded (src/llm_wiki_cli/services/knowledge_storage_io.py)
    participant p10 as storage_writer_lock
    participant p11 as validate_maintenance_adoption
    participant p12 as snapshot_wiki
    participant p13 as canonical_bytes
    participant p14 as _validate_refresh_artifact_basis
    participant p15 as _native_source_snapshot_preflight
    participant p16 as _recovery_directory
    participant p17 as _generation_input_paths
    participant p18 as _collect_runtime
    participant p19 as _retained_empty_paths
    participant p20 as save_recovery_snapshot
    participant p21 as _page_maps
    participant p22 as _runtime_generation_options
    participant p23 as _evaluate_runtime_surface
    participant p24 as _markdown_hashes
    participant p25 as finalize_runtime_knowledge
    participant p26 as collect_runtime_repository_evidence
    participant p27 as _build_context_knowledge_view
    participant p28 as _validate_range
    participant p29 as nullcontext
    participant p30 as path.exists (src/llm_wiki_cli/services…l.py:load_adoption_marker)
    p0->>p1: load_adoption_marker
    p0->>p2: maintenance_write_operation
    p0->>p3: _refresh_documentation_native_projection
    p1->>p4: _absolute_path
    p3->>p5: _validated_directory
    p2->>p6: guard_maintenance_owner
    p3->>p7: _refresh_manifest_version
    p2->>p8: governance_writer_lock
    p1->>p9: read_guarded (src/llm_wiki_cli/services/knowledge_storage_io.py)
    p2->>p10: storage_writer_lock
    p1->>p11: validate_maintenance_adoption
    p2->>p12: snapshot_wiki
    p1->>p13: canonical_bytes
    p3->>p14: _validate_refresh_artifact_basis
    p3->>p15: _native_source_snapshot_preflight
    p2->>p16: _recovery_directory
    p3->>p17: _generation_input_paths
    p3->>p18: _collect_runtime
    p3->>p19: _retained_empty_paths
    p2->>p20: save_recovery_snapshot
    p3->>p21: _page_maps
    p3->>p22: _runtime_generation_options
    p3->>p23: _evaluate_runtime_surface
    p3->>p24: _markdown_hashes
    p3->>p25: finalize_runtime_knowledge
    p3->>p26: collect_runtime_repository_evidence
    p3->>p27: _build_context_knowledge_view
    p9->>p28: _validate_range
    p0-->>p29: nullcontext
    p1-->>p30: path.exists (src/llm_wiki_cli/services…l.py:load_adoption_marker)
```

> Call sequence diagram shows 30 of 4604 interactions; 4574 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1570 (1569 omitted); unresolved 1 of 1186 (1185 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 3 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 3 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 6 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 6 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 3 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/maintenance_protocol.py:load_adoption_marker` | 2 | - | external | 3 |
| `src/llm_wiki_cli/services/maintenance_protocol.py:load_adoption_marker` | 2 | - | unresolved | 1 |
> Omission summary shows 8 of 1123 groups; 1115 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. refresh_documentation_native_projection"]
    s2["2. load_adoption_marker"]
    s3["3. _absolute_path"]
    s4["4. Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)"]
    s5["5. os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)"]
    s6["6. first_unsafe_path_component"]
    s7["7. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s8["8. os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s9["9. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s10["10. os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s11["11. lexical.is_absolute"]
    s12["12. Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s1 -->|"load_adoption_marker(wiki_root)"| s2
    s2 -->|"_absolute_path(Path(...))"| s3
    s3 -. "Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)(os.path.abspath(...))" .-> s4
    s3 -. "os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)(path)" .-> s5
    s3 -->|"first_unsafe_path_component(path)"| s6
    s6 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s7
    s6 -. "os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)(path)" .-> s8
    s6 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))" .-> s9
    s6 -. "os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)(lexical)" .-> s10
    s6 -. "lexical.is_absolute(data not statically known)" .-> s11
    s6 -. "Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)(data not statically known)" .-> s12
    b0["mutation pending_parts.pop"]
    s6 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/documentation_native.md"
    click s2 "../modules/maintenance_protocol.md"
    click s3 "../modules/knowledge_storage_io.md"
    click s6 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `refresh_documentation_native_projection` | `source_root: str \| Path`, `wiki_root: str \| Path`, `trust_source_plugins: bool`, `helper_cache_dir: str \| Path \| None`, `source_selection: str \| Path \| None`, `fault_injector: Callable[[CommitStage], None] \| None` | - | - | `_refresh_documentation_native_projection(...)` |
| `load_adoption_marker` | `wiki_dir: str \| Path` | `ADOPTION_FILENAME` | - | `None`, `marker` |
| `_absolute_path` | `path: Path` | - | - | `path` |
| `Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| refresh_documentation_native_projection | load_adoption_marker | 316 | `load_adoption_marker(wiki_root)` |
| load_adoption_marker | _absolute_path | 85 | `_absolute_path(Path(...))` |
| _absolute_path | Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path) | 49 | `Path(os.path.abspath(...))` |
| _absolute_path | os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path) | 49 | `os.path.abspath(path)` |
| _absolute_path | first_unsafe_path_component | 50 | `first_unsafe_path_component(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component) | 66 | `Path.cwd(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_absolute_path` | `os.path.abspath` | 49 |
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 59 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 60 |
| external_call | `first_unsafe_path_component` | `Path.cwd` | 66 |
| step_limit | `refresh_documentation_native_projection` | `first 12 steps` | 0 |
| truncated_flow | `refresh_documentation_native_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `refresh_documentation_native_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
