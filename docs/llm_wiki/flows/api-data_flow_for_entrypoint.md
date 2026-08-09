# data_flow_for_entrypoint

**Entry point:** `data_flow_for_entrypoint` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [documentation_queries](../modules/documentation_queries.md), and 6 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as data_flow_for_entrypoint
    participant p1 as cast
    participant p2 as _run_query
    participant p3 as callback
    participant p4 as InvalidRequestError
    participant p5 as str
    participant p6 as _query_service
    participant p7 as build_documentation_query_service
    participant p8 as validate_source_root
    participant p9 as validate_path
    participant p10 as PathValidationError
    participant p11 as resolve
    participant p12 as cwd
    participant p13 as relative_to
    participant p14 as expanduser
    participant p15 as Path
    participant p16 as is_absolute
    participant p17 as is_dir
    participant p18 as abspath
    participant p19 as windows_current_user_sid
    participant p20 as WindowsSecurityGuardError
    p0-->>p1: cast
    p0->>p2: _run_query
    p2-->>p3: callback
    p2->>p4: InvalidRequestError
    p2-->>p5: str
    p0-->>p0: data_flow_for_entrypoint
    p0->>p6: _query_service
    p6->>p4: InvalidRequestError
    p6->>p7: build_documentation_query_service
    p7->>p8: validate_source_root
    p8->>p9: validate_path
    p9->>p10: PathValidationError
    p9-->>p11: resolve
    p9-->>p12: cwd
    p9-->>p11: resolve
    p9-->>p12: cwd
    p9-->>p13: relative_to
    p9->>p10: PathValidationError
    p8-->>p14: expanduser
    p8-->>p15: Path
    p8-->>p16: is_absolute
    p8-->>p12: cwd
    p8-->>p11: resolve
    p8->>p10: PathValidationError
    p8-->>p17: is_dir
    p8->>p10: PathValidationError
    p8-->>p15: Path
    p8-->>p18: abspath
    p8->>p19: windows_current_user_sid
    p19->>p20: WindowsSecurityGuardError
```

> Call sequence diagram shows 30 of 280 interactions; 250 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. data_flow_for_entrypoint"]
    s2["2. cast"]
    s3["3. _run_query"]
    s4["4. callback"]
    s5["5. InvalidRequestError"]
    s6["6. str"]
    s7["7. data_flow_for_entrypoint"]
    s8["8. _query_service"]
    s9["9. InvalidRequestError"]
    s10["10. build_documentation_query_service"]
    s11["11. validate_source_root"]
    s12["12. validate_path"]
    s1 -. "cast(DataFlowForEntrypointResult, _run_query(...))" .-> s2
    s1 -->|"_run_query(...)"| s3
    s3 -. "callback(data not statically known)" .-> s4
    s3 -->|"InvalidRequestError(str(...))"| s5
    s3 -. "str(exc)" .-> s6
    s1 -. "_query_service(service, src_dir=src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_se…" .-> s7
    s1 -->|"_query_service(service, src_dir=src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_se…"| s8
    s8 -->|"InvalidRequestError('source_selection cannot be combined with a prebuilt query service')"| s9
    s8 -->|"build_documentation_query_service(src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_…"| s10
    s10 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)"| s11
    s11 -->|"validate_path(path, label)"| s12
    click s1 "../modules/api.md"
    click s3 "../modules/api.md"
    click s5 "../modules/api.md"
    click s8 "../modules/api.md"
    click s9 "../modules/api.md"
    click s10 "../modules/api.md"
    click s11 "../modules/config.md"
    click s12 "../modules/config.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `data_flow_for_entrypoint` | `id_or_symbol: object`, `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `DataFlowForEntrypointResult` | - | `cast(...)` |
| `cast` | - | - | - | - |
| `_run_query` | `callback: Callable[[], dict[str, Any]]` | `DocumentationQueryError` | - | `callback(...)` |
| `callback` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `str` | - | - | - | - |
| `data_flow_for_entrypoint` | - | - | - | - |
| `_query_service` | `service: DocumentationGraphQueryService \| None`, `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | - | - | `service`, `build_documentation_query_service(...)` |
| `InvalidRequestError` | - | - | - | - |
| `build_documentation_query_service` | `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `extract_cmd`, `extract_cmd`, `extract_cmd`, `build_flow`, `evaluate_surface_index`, `context_cmd`, `context_cmd`, `analyze_dependencies` | - | `build_live_documentation_query_service(...)` |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| data_flow_for_entrypoint | cast | 938 | `cast(DataFlowForEntrypointResult, _run_query(...))` |
| data_flow_for_entrypoint | _run_query | 940 | `_run_query(...)` |
| _run_query | callback | 1314 | `callback(data not statically known)` |
| _run_query | InvalidRequestError | 1316 | `InvalidRequestError(str(...))` |
| _run_query | str | 1316 | `str(exc)` |
| data_flow_for_entrypoint | data_flow_for_entrypoint | 941 | `_query_service(service, src_dir=src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection).data_flow_for_entrypoint(id_or_symbol)` |
| data_flow_for_entrypoint | _query_service | 941 | `_query_service(service, src_dir=src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection)` |
| _query_service | InvalidRequestError | 1298 | `InvalidRequestError('source_selection cannot be combined with a prebuilt query service')` |
| _query_service | build_documentation_query_service | 1302 | `build_documentation_query_service(src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection)` |
| build_documentation_query_service | validate_source_root | 858 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)` |
| validate_source_root | validate_path | 156 | `validate_path(path, label)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `data_flow_for_entrypoint` | `cast` | 938 |
| unresolved_call | `_run_query` | `callback` | 1314 |
| unresolved_call | `data_flow_for_entrypoint` | `_query_service(service, src_dir=src_dir, wiki_dir=wiki_dir, limit=limit, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection).data_flow_for_entrypoint` | 941 |
| step_limit | `data_flow_for_entrypoint` | `first 12 steps` | 0 |
| truncated_flow | `data_flow_for_entrypoint` | `depth limit` | 0 |

## Behavior

This flow starts at `data_flow_for_entrypoint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
