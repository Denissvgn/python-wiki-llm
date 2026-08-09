# build_api_contracts

**Entry point:** `build_api_contracts` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [imports](../modules/imports.md), [source_selection](../modules/source_selection.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_api_contracts
    participant p1 as load_openapi_document
    participant p2 as _resolve_openapi_path
    participant p3 as resolve
    participant p4 as Path
    participant p5 as expanduser
    participant p6 as is_absolute
    participant p7 as as_posix
    participant p8 as relative_to
    participant p9 as abspath
    participant p10 as ApiContractError
    participant p11 as path_is_selected
    participant p12 as _selection_path
    participant p13 as _require_selection_path
    participant p14 as require_repository_relative_path
    participant p15 as SourceSelectionError
    p0->>p1: load_openapi_document
    p1->>p2: _resolve_openapi_path
    p2-->>p3: resolve
    p2-->>p4: Path
    p2-->>p5: expanduser
    p2-->>p4: Path
    p2-->>p6: is_absolute
    p2-->>p7: as_posix
    p2-->>p8: relative_to
    p2-->>p4: Path
    p2-->>p9: abspath
    p2->>p10: ApiContractError
    p2-->>p3: resolve
    p2-->>p7: as_posix
    p2-->>p8: relative_to
    p2->>p10: ApiContractError
    p2-->>p3: resolve
    p2->>p10: ApiContractError
    p2->>p11: path_is_selected
    p11->>p12: _selection_path
    p12->>p13: _require_selection_path
    p13->>p14: require_repository_relative_path
    p13->>p15: SourceSelectionError
    p13->>p15: SourceSelectionError
    p13->>p15: SourceSelectionError
    p13->>p15: SourceSelectionError
    p13->>p15: SourceSelectionError
    p13->>p15: SourceSelectionError
    p13->>p15: SourceSelectionError
    p12->>p15: SourceSelectionError
```

> Call sequence diagram shows 30 of 573 interactions; 543 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_api_contracts"]
    s2["2. load_openapi_document"]
    s3["3. _resolve_openapi_path"]
    s4["4. resolve"]
    s5["5. Path"]
    s6["6. expanduser"]
    s7["7. Path"]
    s8["8. is_absolute"]
    s9["9. as_posix"]
    s10["10. relative_to"]
    s11["11. Path"]
    s12["12. abspath"]
    s1 -->|"load_openapi_document(openapi_file, source_root=source_root, source_snapshot=source_snapshot)"| s2
    s2 -->|"_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)"| s3
    s3 -. "Path(source_root).resolve(data not statically known)" .-> s4
    s3 -. "Path(source_root)" .-> s5
    s3 -. "Path(path).expanduser(data not statically known)" .-> s6
    s3 -. "Path(path)" .-> s7
    s3 -. "candidate.is_absolute(data not statically known)" .-> s8
    s3 -. "Path(os.path.abspath(candidate)).relative_to(root).as_posix(data not statically known)" .-> s9
    s3 -. "Path(os.path.abspath(candidate)).relative_to(root)" .-> s10
    s3 -. "Path(os.path.abspath(...))" .-> s11
    s3 -. "os.path.abspath(candidate)" .-> s12
    b0["filesystem_read resolved.read_bytes"]
    s2 -. "filesystem_read resolved.read_bytes" .-> b0
    click s1 "../modules/api_contracts.md"
    click s2 "../modules/api_contracts.md"
    click s3 "../modules/api_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_api_contracts` | `inventory: Mapping[str, Mapping[str, Any]]`, `openapi_file: str \| Path \| None`, `source_root: str \| Path`, `source_snapshot: SourceSnapshot \| None` | - | - | `static`, `_reconcile_openapi(...)` |
| `load_openapi_document` | `path: str \| Path`, `source_root: str \| Path`, `source_snapshot: SourceSnapshot \| None` | `_OPENAPI_INPUT_LIMIT`, `json`, `json`, `yaml`, `Mapping`, `Mapping` | - | `{...}` |
| `_resolve_openapi_path` | `path: str \| Path`, `source_root: str \| Path`, `source_snapshot: SourceSnapshot \| None` | `SourceSelectionError` | - | `(...)` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `as_posix` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_api_contracts | load_openapi_document | 1818 | `load_openapi_document(openapi_file, source_root=source_root, source_snapshot=source_snapshot)` |
| load_openapi_document | _resolve_openapi_path | 1258 | `_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)` |
| _resolve_openapi_path | resolve | 1186 | `Path(source_root).resolve(data not statically known)` |
| _resolve_openapi_path | Path | 1186 | `Path(source_root)` |
| _resolve_openapi_path | expanduser | 1187 | `Path(path).expanduser(data not statically known)` |
| _resolve_openapi_path | Path | 1187 | `Path(path)` |
| _resolve_openapi_path | is_absolute | 1188 | `candidate.is_absolute(data not statically known)` |
| _resolve_openapi_path | as_posix | 1191 | `Path(os.path.abspath(candidate)).relative_to(root).as_posix(data not statically known)` |
| _resolve_openapi_path | relative_to | 1191 | `Path(os.path.abspath(candidate)).relative_to(root)` |
| _resolve_openapi_path | Path | 1191 | `Path(os.path.abspath(...))` |
| _resolve_openapi_path | abspath | 1191 | `os.path.abspath(candidate)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `resolved.read_bytes` | `load_openapi_document` | 1265 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_openapi_path` | `Path(source_root).resolve` | 1186 |
| unresolved_call | `_resolve_openapi_path` | `Path(path).expanduser` | 1187 |
| unresolved_call | `_resolve_openapi_path` | `candidate.is_absolute` | 1188 |
| unresolved_call | `_resolve_openapi_path` | `Path(os.path.abspath(candidate)).relative_to(root).as_posix` | 1191 |
| unresolved_call | `_resolve_openapi_path` | `Path(os.path.abspath(candidate)).relative_to` | 1191 |
| external_call | `_resolve_openapi_path` | `os.path.abspath` | 1191 |
| step_limit | `build_api_contracts` | `first 12 steps` | 0 |
| truncated_flow | `build_api_contracts` | `depth limit` | 0 |

## Behavior

This flow starts at `build_api_contracts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
