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
    participant p2 as Path(…).resolve
    participant p3 as Path
    participant p4 as Path(…).expanduser
    participant p5 as candidate.is_absolute
    participant p6 as Path(…).relative_to(…).as_posix
    participant p7 as Path(…).relative_to
    participant p8 as os.path.abspath
    participant p9 as ApiContractError
    participant p10 as candidate.resolve
    participant p11 as resolved.relative_to(…).as_posix
    participant p12 as resolved.relative_to
    participant p13 as source_snapshot.root.resolve
    participant p14 as path_is_selected
    participant p15 as _selection_path
    participant p16 as _require_selection_path
    participant p17 as require_repository_relative_path
    participant p18 as isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p19 as value.strip
    participant p20 as any (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p21 as ord
    participant p22 as value.startswith
    participant p23 as _WINDOWS_DRIVE_PREFIX_RE.match
    participant p24 as value.split
    p0->>p1: _resolve_openapi_path
    p1-->>p2: Path(…).resolve
    p1-->>p3: Path
    p1-->>p4: Path(…).expanduser
    p1-->>p3: Path
    p1-->>p5: candidate.is_absolute
    p1-->>p6: Path(…).relative_to(…).as_posix
    p1-->>p7: Path(…).relative_to
    p1-->>p3: Path
    p1-->>p8: os.path.abspath
    p1->>p9: ApiContractError
    p1-->>p10: candidate.resolve
    p1-->>p11: resolved.relative_to(…).as_posix
    p1-->>p12: resolved.relative_to
    p1->>p9: ApiContractError
    p1-->>p13: source_snapshot.root.resolve
    p1->>p9: ApiContractError
    p1->>p14: path_is_selected
    p14->>p15: _selection_path
    p15->>p16: _require_selection_path
    p16->>p17: require_repository_relative_path
    p17-->>p18: isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    p17-->>p19: value.strip
    p17-->>p20: any (src/llm_wiki_cli/services…e_repository_relative_path)
    p17-->>p21: ord
    p17-->>p21: ord
    p17-->>p22: value.startswith
    p17-->>p22: value.startswith
    p17-->>p23: _WINDOWS_DRIVE_PREFIX_RE.match
    p17-->>p24: value.split
```

> Call sequence diagram shows 30 of 95 interactions; 65 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_openapi_document"]
    s2["2. _resolve_openapi_path"]
    s3["3. Path(…).resolve"]
    s4["4. Path"]
    s5["5. Path(…).expanduser"]
    s6["6. Path"]
    s7["7. candidate.is_absolute"]
    s8["8. Path(…).relative_to(…).as_posix"]
    s9["9. Path(…).relative_to"]
    s10["10. Path"]
    s11["11. os.path.abspath"]
    s12["12. ApiContractError"]
    s1 -->|"_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)"| s2
    s2 -. "Path(…).resolve(data not statically known)" .-> s3
    s2 -. "Path(source_root)" .-> s4
    s2 -. "Path(…).expanduser(data not statically known)" .-> s5
    s2 -. "Path(path)" .-> s6
    s2 -. "candidate.is_absolute(data not statically known)" .-> s7
    s2 -. "Path(…).relative_to(…).as_posix(data not statically known)" .-> s8
    s2 -. "Path(…).relative_to(root)" .-> s9
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
| `Path(…).resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `Path(…).expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `candidate.is_absolute` | - | - | - | - |
| `Path(…).relative_to(…).as_posix` | - | - | - | - |
| `Path(…).relative_to` | - | - | - | - |
| `Path` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `ApiContractError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_openapi_document | _resolve_openapi_path | 1259 | `_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)` |
| _resolve_openapi_path | Path(…).resolve | 1187 | `Path(source_root).resolve(data not statically known)` |
| _resolve_openapi_path | Path | 1187 | `Path(source_root)` |
| _resolve_openapi_path | Path(…).expanduser | 1188 | `Path(path).expanduser(data not statically known)` |
| _resolve_openapi_path | Path | 1188 | `Path(path)` |
| _resolve_openapi_path | candidate.is_absolute | 1189 | `candidate.is_absolute(data not statically known)` |
| _resolve_openapi_path | Path(…).relative_to(…).as_posix | 1192 | `Path(os.path.abspath(candidate)).relative_to(root).as_posix(data not statically known)` |
| _resolve_openapi_path | Path(…).relative_to | 1192 | `Path(os.path.abspath(candidate)).relative_to(root)` |
| _resolve_openapi_path | Path | 1192 | `Path(os.path.abspath(...))` |
| _resolve_openapi_path | os.path.abspath | 1192 | `os.path.abspath(candidate)` |
| _resolve_openapi_path | ApiContractError | 1194 | `ApiContractError(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `resolved.read_bytes` | `load_openapi_document` | 1266 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_openapi_path` | `Path(source_root).resolve` | 1187 |
| unresolved_call | `_resolve_openapi_path` | `Path(path).expanduser` | 1188 |
| unresolved_call | `_resolve_openapi_path` | `candidate.is_absolute` | 1189 |
| unresolved_call | `_resolve_openapi_path` | `Path(os.path.abspath(candidate)).relative_to(root).as_posix` | 1192 |
| unresolved_call | `_resolve_openapi_path` | `Path(os.path.abspath(candidate)).relative_to` | 1192 |
| external_call | `_resolve_openapi_path` | `os.path.abspath` | 1192 |
| step_limit | `load_openapi_document` | `first 12 steps` | 0 |
| truncated_flow | `load_openapi_document` | `depth limit` | 0 |

## Behavior

This flow starts at `load_openapi_document` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
