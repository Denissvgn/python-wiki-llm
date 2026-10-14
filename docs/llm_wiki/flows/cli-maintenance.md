# maintenance

**Entry point:** `run` (`cli`)
**Source:** [maintenance_cmd](../modules/maintenance_cmd.md)
**Modules touched:** [api](../modules/api.md), [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [config](../modules/config.md), and 54 more

**Complete modules touched:**

- [api](../modules/api.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_cmd](../modules/maintenance_cmd.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_queue](../modules/maintenance_queue.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [plugins](../modules/plugins.md)
- [python_implementation](../modules/python_implementation.md)
- [request_json](../modules/request_json.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [storage_spool](../modules/storage_spool.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as adopt_maintenance
    participant p2 as get_maintenance_status
    participant p3 as acknowledge_maintenance
    participant p4 as load_request
    participant p5 as recover_maintenance
    participant p6 as _capture_options
    participant p7 as _render_status
    participant p8 as adopt_maintenance_authority
    participant p9 as _validate_wiki_dir
    participant p10 as get_maintenance_status_authority
    participant p11 as recover_maintenance_authority
    participant p12 as acknowledge_maintenance_authority
    participant p13 as _absolute_path
    participant p14 as _validate_status_request
    participant p15 as _outside_recovery
    participant p16 as load_recovery_snapshot
    participant p17 as governance_writer_lock
    participant p18 as storage_writer_lock
    participant p19 as load_adoption_marker
    participant p20 as guard_maintenance_owner
    participant p21 as capture_committed_knowledge
    participant p22 as build_maintenance_status
    participant p23 as snapshot_wiki
    participant p24 as _capture_basis
    participant p25 as _capture
    participant p26 as _native_prose_coherent
    participant p27 as maintenance_write_operation
    participant p28 as capture_maintenance_observations
    participant p29 as print
    participant p30 as result.get
    p0->>p1: adopt_maintenance
    p0->>p2: get_maintenance_status
    p0->>p3: acknowledge_maintenance
    p0->>p4: load_request
    p0->>p5: recover_maintenance
    p0->>p6: _capture_options
    p0->>p7: _render_status
    p1->>p8: adopt_maintenance_authority
    p1->>p9: _validate_wiki_dir
    p2->>p10: get_maintenance_status_authority
    p5->>p11: recover_maintenance_authority
    p3->>p12: acknowledge_maintenance_authority
    p8->>p13: _absolute_path
    p10->>p14: _validate_status_request
    p8->>p15: _outside_recovery
    p11->>p16: load_recovery_snapshot
    p8->>p17: governance_writer_lock
    p8->>p18: storage_writer_lock
    p8->>p19: load_adoption_marker
    p8->>p20: guard_maintenance_owner
    p10->>p21: capture_committed_knowledge
    p10->>p22: build_maintenance_status
    p8->>p23: snapshot_wiki
    p8->>p24: _capture_basis
    p8->>p25: _capture
    p10->>p26: _native_prose_coherent
    p12->>p27: maintenance_write_operation
    p8->>p28: capture_maintenance_observations
    p0-->>p29: print(json.dumps(...))
    p7-->>p30: result.get('requires_sync')
```

> Call sequence diagram shows 30 of 2364 interactions; 2334 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 778 (777 omitted); unresolved 1 of 515 (514 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/api.py:adopt_maintenance` | 2 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 7 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 7 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 10 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 10 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 7 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 7 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/maintenance_service.py:adopt_maintenance_authority` | 6 | [src/llm_wiki_cli/services/knowledge_storage_io.py](../modules/knowledge_storage_io.md) | internal | 1 |
> Omission summary shows 8 of 568 groups; 560 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. adopt_maintenance"]
    s3["3. type (src/llm_wiki_cli/api.py:adopt_maintenance)"]
    s4["4. ValueError (src/llm_wiki_cli/api.py:adopt_maintenance)"]
    s5["5. cast (src/llm_wiki_cli/api.py:adopt_maintenance)"]
    s6["6. adopt_maintenance_authority"]
    s7["7. _absolute_path"]
    s8["8. Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)"]
    s9["9. os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)"]
    s10["10. first_unsafe_path_component"]
    s11["11. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s12["12. os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s1 -->|"adopt_maintenance(args.src_dir, args.wiki_dir, recovery_dir=args.recovery_dir, manifest_format=args.manifest_format, **=_capture_options(...))"| s2
    s2 -. "type (src/llm_wiki_cli/api.py:adopt_maintenance)(allow_external_src)" .-> s3
    s2 -. "ValueError (src/llm_wiki_cli/api.py:adopt_maintenance)('Unsupported maintenance adoption options')" .-> s4
    s2 -. "cast (src/llm_wiki_cli/api.py:adopt_maintenance)(MaintenanceAdoptionResult, adopt_maintenance_authority(...))" .-> s5
    s2 -->|"adopt_maintenance_authority(…)"| s6
    s6 -->|"_absolute_path(wiki_dir)"| s7
    s7 -. "Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)(os.path.abspath(...))" .-> s8
    s7 -. "os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)(path)" .-> s9
    s7 -->|"first_unsafe_path_component(path)"| s10
    s10 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s11
    s10 -. "os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)(path)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["mutation generation_inputs.pop"]
    s6 -. "mutation generation_inputs.pop" .-> b4
    b5["mutation extensions.pop"]
    s6 -. "mutation extensions.pop" .-> b5
    b6["mutation pending_parts.pop"]
    s10 -. "mutation pending_parts.pop" .-> b6
    click s1 "../modules/maintenance_cmd.md"
    click s2 "../modules/api.md"
    click s6 "../modules/maintenance_service.md"
    click s7 "../modules/knowledge_storage_io.md"
    click s10 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | - | - | - |
| `adopt_maintenance` | `src_dir: str`, `wiki_dir: str`, `recovery_dir: str \| Path`, `manifest_format: Literal['v7', 'indexed-v8'] \| None`, `source_selection: str \| Path \| None`, `helper_cache_dir: str \| None`, `allow_external_src: bool` | `MaintenanceAdoptionResult` | - | `cast(...)` |
| `type (src/llm_wiki_cli/api.py:adopt_maintenance)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/api.py:adopt_maintenance)` | - | - | - | - |
| `cast (src/llm_wiki_cli/api.py:adopt_maintenance)` | - | - | - | - |
| `adopt_maintenance_authority` | `src_dir`, `wiki_dir`, `recovery_dir`, `manifest_format`, `fault_injector`, `_captured`, `capture_options` | - | `basis.source_snapshot`, `after[...]` | `{...}`, `{...}` |
| `_absolute_path` | `path: Path` | - | - | `path` |
| `Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | adopt_maintenance | 58 | `api.adopt_maintenance(args.src_dir, args.wiki_dir, recovery_dir=args.recovery_dir, manifest_format=args.manifest_format, **=_capture_options(...))` |
| adopt_maintenance | type (src/llm_wiki_cli/api.py:adopt_maintenance) | 1590 | `type(allow_external_src)` |
| adopt_maintenance | ValueError (src/llm_wiki_cli/api.py:adopt_maintenance) | 1591 | `ValueError('Unsupported maintenance adoption options')` |
| adopt_maintenance | cast (src/llm_wiki_cli/api.py:adopt_maintenance) | 1592 | `cast(MaintenanceAdoptionResult, adopt_maintenance_authority(...))` |
| adopt_maintenance | adopt_maintenance_authority | 1592 | `adopt_maintenance_authority(src_dir, _validate_wiki_dir(...), recovery_dir=recovery_dir, manifest_format=manifest_format, source_selection=source_selection, helper_cache_dir=helper_cache_dir, allow_external_src=allow_external_src)` |
| adopt_maintenance_authority | _absolute_path | 83 | `_absolute_path(wiki_dir)` |
| _absolute_path | Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path) | 49 | `Path(os.path.abspath(...))` |
| _absolute_path | os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path) | 49 | `os.path.abspath(path)` |
| _absolute_path | first_unsafe_path_component | 50 | `first_unsafe_path_component(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `os.fspath(path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 96 |
| output | `print` | `run` | 112 |
| output | `print` | `run` | 124 |
| output | `print` | `run` | 126 |
| mutation | `generation_inputs.pop` | `adopt_maintenance_authority` | 113 |
| mutation | `extensions.pop` | `adopt_maintenance_authority` | 116 |
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `adopt_maintenance` | `type` | 1590 |
| external_call | `adopt_maintenance` | `ValueError` | 1591 |
| external_call | `adopt_maintenance` | `cast` | 1592 |
| external_call | `_absolute_path` | `os.path.abspath` | 49 |
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
