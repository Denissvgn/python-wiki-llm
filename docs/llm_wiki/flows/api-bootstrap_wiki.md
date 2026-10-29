# bootstrap_wiki

**Entry point:** `bootstrap_wiki` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [api_contracts](../modules/api_contracts.md), [bootstrap_recovery](../modules/bootstrap_recovery.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), and 39 more

**Complete modules touched:**

- [api](../modules/api.md)
- [api_contracts](../modules/api_contracts.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [current_contracts](../modules/current_contracts.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [module_maps](../modules/module_maps.md)
- [paths](../modules/paths.md)
- [relationships](../modules/relationships.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as bootstrap_wiki
    participant p1 as execute_bootstrap
    participant p2 as BootstrapRequest
    participant p3 as InvalidRequestError
    participant p4 as WorkspaceStateError
    participant p5 as _bootstrap_run_options_from_request
    participant p6 as _execute_bootstrap_options
    participant p7 as pending_bootstrap
    participant p8 as guard_maintenance_owner
    participant p9 as _preflight_public_bootstrap
    participant p10 as maintenance_write_operation
    participant p11 as bootstrap_write_operation
    participant p12 as _preflight_bootstrap_source_selection
    participant p13 as _execute_bootstrap_options_locked
    participant p14 as _load_record
    participant p15 as _preflight_bootstrap_governance
    participant p16 as _first_use_guidance
    participant p17 as guard_incomplete_bootstrap
    participant p18 as _is_pristine_bootstrap_target
    participant p19 as resolve_source_selection
    participant p20 as load_adoption_marker
    participant p21 as governance_writer_lock
    participant p22 as validate_persisted_source_selection_identity
    participant p23 as _start_bootstrap
    participant p24 as SyncManifest.load
    participant p25 as storage_writer_lock
    participant p26 as _extract_bootstrap_inventory
    participant p27 as _recover
    participant p28 as snapshot_wiki
    participant p29 as str (src/llm_wiki_cli/api.py:bootstrap_wiki)
    participant p30 as Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)
    p0->>p1: execute_bootstrap
    p0->>p2: BootstrapRequest
    p0->>p3: InvalidRequestError
    p0->>p4: WorkspaceStateError
    p1->>p5: _bootstrap_run_options_from_request
    p1->>p6: _execute_bootstrap_options
    p6->>p7: pending_bootstrap
    p6->>p8: guard_maintenance_owner
    p6->>p9: _preflight_public_bootstrap
    p6->>p10: maintenance_write_operation
    p6->>p11: bootstrap_write_operation
    p6->>p12: _preflight_bootstrap_source_selection
    p6->>p13: _execute_bootstrap_options_locked
    p7->>p14: _load_record
    p13->>p15: _preflight_bootstrap_governance
    p9->>p16: _first_use_guidance
    p8->>p17: guard_incomplete_bootstrap
    p9->>p18: _is_pristine_bootstrap_target
    p12->>p19: resolve_source_selection
    p8->>p20: load_adoption_marker
    p10->>p21: governance_writer_lock
    p12->>p22: validate_persisted_source_selection_identity
    p13->>p23: _start_bootstrap
    p8->>p24: SyncManifest.load
    p10->>p25: storage_writer_lock
    p13->>p26: _extract_bootstrap_inventory
    p11->>p27: _recover
    p10->>p28: snapshot_wiki
    p0-->>p29: str (src/llm_wiki_cli/api.py:bootstrap_wiki)(exc)
    p5-->>p30: Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)
```

> Call sequence diagram shows 30 of 1308 interactions; 1278 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 408 (407 omitted); unresolved 1 of 290 (289 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/bootstrap_runtime.py:execute_bootstrap` | 3 | - | external | 1 |
| `src/llm_wiki_cli/services/bootstrap_runtime.py:_bootstrap_run_options_from_request` | 5 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/bootstrap_runtime.py:_bootstrap_run_options_from_request` | 5 | - | external | 5 |
| `src/llm_wiki_cli/services/bootstrap_runtime.py:_bootstrap_run_options_from_request` | 5 | [src/llm_wiki_cli/services/bootstrap_service.py](../modules/bootstrap_service.md) | internal | 3 |
| `src/llm_wiki_cli/services/bootstrap_runtime.py:_bootstrap_run_options_from_request` | 5 | [src/llm_wiki_cli/services/bootstrap_runtime.py](../modules/bootstrap_runtime.md) | internal | 1 |
| `src/llm_wiki_cli/services/bootstrap_recovery.py:_load_record` | 22 | [src/llm_wiki_cli/services/bootstrap_recovery.py](../modules/bootstrap_recovery.md) | internal | 5 |
| `src/llm_wiki_cli/services/bootstrap_recovery.py:_record_path` | 23 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 1 |
| `src/llm_wiki_cli/services/bootstrap_recovery.py:_record_path` | 23 | - | unresolved | 2 |
> Omission summary shows 8 of 344 groups; 336 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 611; effect analysis evaluated: 491, partial: 0, unavailable: 120. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `bootstrap_wiki` | `available` | `evaluated` | `available` |
| `BootstrapRequest` | `unavailable` | `unavailable` | `unavailable` |
| `execute_bootstrap` | `available` | `evaluated` | `available` |
| `io.StringIO` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_bootstrap_run_options_from_request` | `available` | `evaluated` | `available` |
| `Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `Path (src/llm_wiki_cli/services…_run_options_from_request)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `BootstrapContractError` | `unavailable` | `unavailable` | `unavailable` |
| `Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1)` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. bootstrap_wiki"]
    s2["2. BootstrapRequest"]
    s3["3. execute_bootstrap"]
    s4["4. io.StringIO"]
    s5["5. _bootstrap_run_options_from_request"]
    s6["6. Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)"]
    s7["7. Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request)"]
    s8["8. Path (src/llm_wiki_cli/services…_run_options_from_request)"]
    s9["9. source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request)"]
    s10["10. BootstrapContractError"]
    s11["11. Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1)"]
    s12["12. Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1)"]
    s1 -->|"BootstrapRequest(…)"| s2
    s1 -->|"execute_bootstrap(request)"| s3
    s3 -. "io.StringIO(data not statically known)" .-> s4
    s3 -->|"_bootstrap_run_options_from_request(request, progress_stream=stream)"| s5
    s5 -. "Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)(data not statically known)" .-> s6
    s5 -. "Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request)(data not statically known)" .-> s7
    s5 -. "Path (src/llm_wiki_cli/services…_run_options_from_request)(request.source_root)" .-> s8
    s5 -. "source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request)(data not statically known)" .-> s9
    s5 -->|"BootstrapContractError(...)"| s10
    s5 -. "Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1)(data not statically known)" .-> s11
    s5 -. "Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1)(data not statically known)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/bootstrap_service.md"
    click s3 "../modules/bootstrap_runtime.md"
    click s5 "../modules/bootstrap_runtime.md"
    click s10 "../modules/bootstrap_service.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `bootstrap_wiki` | `source_root: str`, `wiki_root: str`, `depth: str`, `skip_workflows: bool`, `skip_flows: bool`, `skip_data_flow: bool`, `skip_dependencies: bool`, `api_contracts: bool` | `BootstrapRequestError`, `BootstrapContractError`, `BootstrapServiceError` | - | `bootstrap_cmd.execute_bootstrap(...)` |
| `BootstrapRequest` | - | - | - | - |
| `execute_bootstrap` | `request: BootstrapRequest`, `progress_stream: TextIO \| None` | - | - | `_execute_bootstrap_options(...)` |
| `io.StringIO` | - | - | - | - |
| `_bootstrap_run_options_from_request` | `request: BootstrapRequest`, `progress_stream: TextIO` | - | - | `_BootstrapRunOptions(...)` |
| `Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)` | - | - | - | - |
| `Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…_run_options_from_request)` | - | - | - | - |
| `source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request)` | - | - | - | - |
| `BootstrapContractError` | - | - | - | - |
| `Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1)` | - | - | - | - |
| `Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| bootstrap_wiki | BootstrapRequest | 1098 | `BootstrapRequest(source_root=source_root, wiki_root=wiki_root, depth=depth, skip_workflows=skip_workflows, skip_flows=skip_flows, skip_data_flow=skip_data_flow, skip_dependencies=skip_dependencies, api_contracts=api_contracts, openapi_file=openapi_file, dependency_graph_detail=dependency_graph_detail, overwrite=overwrite, source_adapter=True, helper_cache_dir=helper_cache_dir, include_tests=include_tests, trust_source_plugins=trust_source_plugins, source_selection=source_selection, knowledge_format=knowledge_format)` |
| bootstrap_wiki | execute_bootstrap | 1118 | `bootstrap_cmd.execute_bootstrap(request)` |
| execute_bootstrap | io.StringIO | 6769 | `io.StringIO(data not statically known)` |
| execute_bootstrap | _bootstrap_run_options_from_request | 6770 | `_bootstrap_run_options_from_request(request, progress_stream=stream)` |
| _bootstrap_run_options_from_request | Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request) | 4861 | `Path(request.source_root).expanduser().resolve(data not statically known)` |
| _bootstrap_run_options_from_request | Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request) | 4861 | `Path(request.source_root).expanduser(data not statically known)` |
| _bootstrap_run_options_from_request | Path (src/llm_wiki_cli/services…_run_options_from_request) | 4861 | `Path(request.source_root)` |
| _bootstrap_run_options_from_request | source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request) | 4862 | `source_root.is_dir(data not statically known)` |
| _bootstrap_run_options_from_request | BootstrapContractError | 4863 | `BootstrapContractError(...)` |
| _bootstrap_run_options_from_request | Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1) | 4866 | `Path(request.wiki_root).expanduser().resolve(data not statically known)` |
| _bootstrap_run_options_from_request | Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1) | 4866 | `Path(request.wiki_root).expanduser(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `execute_bootstrap` | `io.StringIO` | 6769 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.source_root).expanduser().resolve` | 4861 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.source_root).expanduser` | 4861 |
| unresolved_call | `_bootstrap_run_options_from_request` | `source_root.is_dir` | 4862 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.wiki_root).expanduser().resolve` | 4866 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.wiki_root).expanduser` | 4866 |
| step_limit | `bootstrap_wiki` | `first 12 steps` | 0 |
| truncated_flow | `bootstrap_wiki` | `depth limit` | 0 |

## Behavior

Creates a frozen `BootstrapRequest` and executes the same deterministic
first-use generator as the CLI. The library boundary always enables source-
adapter behavior, so it writes within the wiki target without installing agent
instructions in the source project. Request errors become
`InvalidRequestError`; target or service-state failures become
`WorkspaceStateError`; success returns a typed `BootstrapResult`.
