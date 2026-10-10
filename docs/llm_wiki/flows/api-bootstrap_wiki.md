# bootstrap_wiki

**Entry point:** `bootstrap_wiki` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), and 31 more

**Complete modules touched:**

- [api](../modules/api.md)
- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as bootstrap_wiki
    participant p1 as BootstrapRequest
    participant p2 as execute_bootstrap
    participant p3 as InvalidRequestError
    participant p4 as str (src/llm_wiki_cli/api.py:bootstrap_wiki)
    participant p5 as WorkspaceStateError
    participant p6 as io.StringIO
    participant p7 as _bootstrap_run_options_from_request
    participant p8 as _execute_bootstrap_options
    participant p9 as Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)
    participant p10 as guard_maintenance_owner
    participant p11 as Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request)
    participant p12 as _preflight_public_bootstrap
    participant p13 as Path (src/llm_wiki_cli/services…_run_options_from_request)
    participant p14 as source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request)
    participant p15 as _preflight_bootstrap_source_selection
    participant p16 as BootstrapContractError
    participant p17 as maintenance_write_operation
    participant p18 as Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1)
    participant p19 as _execute_bootstrap_options_locked
    participant p20 as Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1)
    participant p21 as BootstrapRequestError
    participant p22 as bool (src/llm_wiki_cli/services…_run_options_from_request)
    participant p23 as _BootstrapRunOptions
    participant p24 as str (src/llm_wiki_cli/services…_run_options_from_request)
    p0->>p1: BootstrapRequest
    p0->>p2: execute_bootstrap
    p0->>p3: InvalidRequestError
    p0-->>p4: str (src/llm_wiki_cli/api.py:bootstrap_wiki)(exc)
    p0->>p5: WorkspaceStateError
    p0-->>p4: str (src/llm_wiki_cli/api.py:bootstrap_wiki)(exc)
    p0->>p5: WorkspaceStateError
    p0-->>p4: str (src/llm_wiki_cli/api.py:bootstrap_wiki)(exc)
    p2-->>p6: io.StringIO
    p2->>p7: _bootstrap_run_options_from_request
    p2->>p8: _execute_bootstrap_options
    p7-->>p9: Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request)
    p8->>p10: guard_maintenance_owner
    p7-->>p11: Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request)
    p8->>p12: _preflight_public_bootstrap
    p7-->>p13: Path (src/llm_wiki_cli/services…_run_options_from_request)(request.source_root)
    p8->>p12: _preflight_public_bootstrap
    p7-->>p14: source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request)
    p8->>p15: _preflight_bootstrap_source_selection
    p7->>p16: BootstrapContractError
    p8->>p17: maintenance_write_operation
    p7-->>p18: Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1)
    p8->>p19: _execute_bootstrap_options_locked
    p7-->>p20: Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1)
    p7-->>p13: Path (src/llm_wiki_cli/services…_run_options_from_request)(request.wiki_root)
    p7->>p21: BootstrapRequestError
    p7->>p21: BootstrapRequestError
    p7-->>p22: bool (src/llm_wiki_cli/services…_run_options_from_request)(...)
    p7->>p23: _BootstrapRunOptions
    p7-->>p24: str (src/llm_wiki_cli/services…_run_options_from_request)(source_root)
```

> Call sequence diagram shows 30 of 1054 interactions; 1024 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 317 (309 omitted); unresolved 5 of 243 (238 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/bootstrap_runtime.py:_bootstrap_run_options_from_request` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/maintenance_protocol.py:guard_maintenance_owner` | 21 | [src/llm_wiki_cli/services/knowledge_storage_io.py](../modules/knowledge_storage_io.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 22 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 22 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 25 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 25 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 22 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 22 | - | unresolved | 3 |
> Omission summary shows 8 of 277 groups; 269 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
| bootstrap_wiki | BootstrapRequest | 1092 | `BootstrapRequest(source_root=source_root, wiki_root=wiki_root, depth=depth, skip_workflows=skip_workflows, skip_flows=skip_flows, skip_data_flow=skip_data_flow, skip_dependencies=skip_dependencies, api_contracts=api_contracts, openapi_file=openapi_file, dependency_graph_detail=dependency_graph_detail, overwrite=overwrite, source_adapter=True, helper_cache_dir=helper_cache_dir, include_tests=include_tests, trust_source_plugins=trust_source_plugins, source_selection=source_selection)` |
| bootstrap_wiki | execute_bootstrap | 1111 | `bootstrap_cmd.execute_bootstrap(request)` |
| execute_bootstrap | io.StringIO | 6409 | `io.StringIO(data not statically known)` |
| execute_bootstrap | _bootstrap_run_options_from_request | 6410 | `_bootstrap_run_options_from_request(request, progress_stream=stream)` |
| _bootstrap_run_options_from_request | Path(…).expanduser().resolve (src/llm_wiki_cli/services…_run_options_from_request) | 4564 | `Path(request.source_root).expanduser().resolve(data not statically known)` |
| _bootstrap_run_options_from_request | Path(…).expanduser (src/llm_wiki_cli/services…_run_options_from_request) | 4564 | `Path(request.source_root).expanduser(data not statically known)` |
| _bootstrap_run_options_from_request | Path (src/llm_wiki_cli/services…_run_options_from_request) | 4564 | `Path(request.source_root)` |
| _bootstrap_run_options_from_request | source_root.is_dir (src/llm_wiki_cli/services…_run_options_from_request) | 4565 | `source_root.is_dir(data not statically known)` |
| _bootstrap_run_options_from_request | BootstrapContractError | 4566 | `BootstrapContractError(...)` |
| _bootstrap_run_options_from_request | Path(…).expanduser().resolve (src/llm_wiki_cli/services…n_options_from_request, 1) | 4569 | `Path(request.wiki_root).expanduser().resolve(data not statically known)` |
| _bootstrap_run_options_from_request | Path(…).expanduser (src/llm_wiki_cli/services…n_options_from_request, 1) | 4569 | `Path(request.wiki_root).expanduser(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `execute_bootstrap` | `io.StringIO` | 6409 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.source_root).expanduser().resolve` | 4564 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.source_root).expanduser` | 4564 |
| unresolved_call | `_bootstrap_run_options_from_request` | `source_root.is_dir` | 4565 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.wiki_root).expanduser().resolve` | 4569 |
| unresolved_call | `_bootstrap_run_options_from_request` | `Path(request.wiki_root).expanduser` | 4569 |
| step_limit | `bootstrap_wiki` | `first 12 steps` | 0 |
| truncated_flow | `bootstrap_wiki` | `depth limit` | 0 |

## Behavior

Creates a frozen `BootstrapRequest` and executes the same deterministic
first-use generator as the CLI. The library boundary always enables source-
adapter behavior, so it writes within the wiki target without installing agent
instructions in the source project. Request errors become
`InvalidRequestError`; target or service-state failures become
`WorkspaceStateError`; success returns a typed `BootstrapResult`.
