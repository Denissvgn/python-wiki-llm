# load_openapi_document

**Entry point:** `load_openapi_document` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [source_selection](../modules/source_selection.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_openapi_document
    participant p1 as _resolve_openapi_path
    participant p2 as resolve
    participant p3 as Path
    participant p4 as expanduser
    participant p5 as is_absolute
    participant p6 as as_posix
    participant p7 as relative_to
    participant p8 as abspath
    participant p9 as ApiContractError
    participant p10 as path_is_selected
    participant p11 as _selection_path
    participant p12 as _require_selection_path
    participant p13 as require_repository_relative_path
    participant p14 as isinstance
    participant p15 as strip
    participant p16 as any
    participant p17 as ord
    participant p18 as startswith
    participant p19 as match
    participant p20 as split
    p0->>p1: _resolve_openapi_path
    p1-->>p2: resolve
    p1-->>p3: Path
    p1-->>p4: expanduser
    p1-->>p3: Path
    p1-->>p5: is_absolute
    p1-->>p6: as_posix
    p1-->>p7: relative_to
    p1-->>p3: Path
    p1-->>p8: abspath
    p1->>p9: ApiContractError
    p1-->>p2: resolve
    p1-->>p6: as_posix
    p1-->>p7: relative_to
    p1->>p9: ApiContractError
    p1-->>p2: resolve
    p1->>p9: ApiContractError
    p1->>p10: path_is_selected
    p10->>p11: _selection_path
    p11->>p12: _require_selection_path
    p12->>p13: require_repository_relative_path
    p13-->>p14: isinstance
    p13-->>p15: strip
    p13-->>p16: any
    p13-->>p17: ord
    p13-->>p17: ord
    p13-->>p18: startswith
    p13-->>p18: startswith
    p13-->>p19: match
    p13-->>p20: split
```

> Call sequence diagram shows 30 of 95 interactions; 65 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_openapi_document"]
    s2["2. _resolve_openapi_path"]
    s3["3. resolve"]
    s4["4. Path"]
    s5["5. expanduser"]
    s6["6. Path"]
    s7["7. is_absolute"]
    s8["8. as_posix"]
    s9["9. relative_to"]
    s10["10. Path"]
    s11["11. abspath"]
    s12["12. ApiContractError"]
    s1 -->|"_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)"| s2
    s2 -. "Path(source_root).resolve(data not statically known)" .-> s3
    s2 -. "Path(source_root)" .-> s4
    s2 -. "Path(path).expanduser(data not statically known)" .-> s5
    s2 -. "Path(path)" .-> s6
    s2 -. "candidate.is_absolute(data not statically known)" .-> s7
    s2 -. "Path(os.path.abspath(candidate)).relative_to(root).as_posix(data not statically known)" .-> s8
    s2 -. "Path(os.path.abspath(candidate)).relative_to(root)" .-> s9
    s2 -. "Path(os.path.abspath(...))" .-> s10
    s2 -. "os.path.abspath(candidate)" .-> s11
    s2 -->|"ApiContractError(...)"| s12
    b0["filesystem_read resolved.read_bytes"]
    s1 -. "filesystem_read resolved.read_bytes" .-> b0
    click s1 "../modules/api_contracts.md"
    click s2 "../modules/api_contracts.md"
    click s12 "../modules/api_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `ApiContractError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _resolve_openapi_path | ApiContractError | 1193 | `ApiContractError(...)` |

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
| step_limit | `load_openapi_document` | `first 12 steps` | 0 |
| truncated_flow | `load_openapi_document` | `depth limit` | 0 |

## Behavior

This flow starts at `load_openapi_document` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
