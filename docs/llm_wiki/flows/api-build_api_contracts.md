# build_api_contracts

**Entry point:** `build_api_contracts` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [config](../modules/config.md), [imports](../modules/imports.md), [packages](../modules/packages.md), and 3 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [config](../modules/config.md)
- [imports](../modules/imports.md)
- [packages](../modules/packages.md)
- [python_imports](../modules/python_imports.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_api_contracts
    participant p1 as load_openapi_document
    participant p2 as _resolve_openapi_path
    participant p3 as Path(…).resolve (src/llm_wiki_cli/services….py:_resolve_openapi_path)
    participant p4 as Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)
    participant p5 as Path(…).expanduser
    participant p6 as candidate.is_absolute
    participant p7 as Path(…).relative_to(…).as_posix
    participant p8 as Path(…).relative_to
    participant p9 as os.path.abspath
    participant p10 as ApiContractError
    participant p11 as candidate.resolve
    participant p12 as resolved.relative_to(…).as_posix
    participant p13 as resolved.relative_to
    participant p14 as source_snapshot.root.resolve
    participant p15 as path_is_selected
    participant p16 as _selection_path
    participant p17 as _require_selection_path
    participant p18 as require_repository_relative_path
    participant p19 as SourceSelectionError
    p0->>p1: load_openapi_document
    p1->>p2: _resolve_openapi_path
    p2-->>p3: Path(…).resolve (src/llm_wiki_cli/services….py:_resolve_openapi_path)
    p2-->>p4: Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)
    p2-->>p5: Path(…).expanduser
    p2-->>p4: Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)
    p2-->>p6: candidate.is_absolute
    p2-->>p7: Path(…).relative_to(…).as_posix
    p2-->>p8: Path(…).relative_to
    p2-->>p4: Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)
    p2-->>p9: os.path.abspath
    p2->>p10: ApiContractError
    p2-->>p11: candidate.resolve
    p2-->>p12: resolved.relative_to(…).as_posix
    p2-->>p13: resolved.relative_to
    p2->>p10: ApiContractError
    p2-->>p14: source_snapshot.root.resolve
    p2->>p10: ApiContractError
    p2->>p15: path_is_selected
    p15->>p16: _selection_path
    p16->>p17: _require_selection_path
    p17->>p18: require_repository_relative_path
    p17->>p19: SourceSelectionError
    p17->>p19: SourceSelectionError
    p17->>p19: SourceSelectionError
    p17->>p19: SourceSelectionError
    p17->>p19: SourceSelectionError
    p17->>p19: SourceSelectionError
    p17->>p19: SourceSelectionError
    p16->>p19: SourceSelectionError
```

> Call sequence diagram shows 30 of 892 interactions; 862 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_api_contracts"]
    s2["2. load_openapi_document"]
    s3["3. _resolve_openapi_path"]
    s4["4. Path(…).resolve (src/llm_wiki_cli/services….py:_resolve_openapi_path)"]
    s5["5. Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)"]
    s6["6. Path(…).expanduser"]
    s7["7. Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)"]
    s8["8. candidate.is_absolute"]
    s9["9. Path(…).relative_to(…).as_posix"]
    s10["10. Path(…).relative_to"]
    s11["11. Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)"]
    s12["12. os.path.abspath"]
    s1 -->|"load_openapi_document(openapi_file, source_root=source_root, source_snapshot=source_snapshot)"| s2
    s2 -->|"_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)"| s3
    s3 -. "Path(…).resolve (src/llm_wiki_cli/services….py:_resolve_openapi_path)(data not statically known)" .-> s4
    s3 -. "Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)(source_root)" .-> s5
    s3 -. "Path(…).expanduser(data not statically known)" .-> s6
    s3 -. "Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)(path)" .-> s7
    s3 -. "candidate.is_absolute(data not statically known)" .-> s8
    s3 -. "Path(…).relative_to(…).as_posix(data not statically known)" .-> s9
    s3 -. "Path(…).relative_to(root)" .-> s10
    s3 -. "Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)(os.path.abspath(...))" .-> s11
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
| `Path(…).resolve (src/llm_wiki_cli/services….py:_resolve_openapi_path)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)` | - | - | - | - |
| `Path(…).expanduser` | - | - | - | - |
| `Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)` | - | - | - | - |
| `candidate.is_absolute` | - | - | - | - |
| `Path(…).relative_to(…).as_posix` | - | - | - | - |
| `Path(…).relative_to` | - | - | - | - |
| `Path (src/llm_wiki_cli/services….py:_resolve_openapi_path)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_api_contracts | load_openapi_document | 1819 | `load_openapi_document(openapi_file, source_root=source_root, source_snapshot=source_snapshot)` |
| load_openapi_document | _resolve_openapi_path | 1259 | `_resolve_openapi_path(path, source_root, source_snapshot=source_snapshot)` |
| _resolve_openapi_path | Path(…).resolve (src/llm_wiki_cli/services….py:_resolve_openapi_path) | 1187 | `Path(source_root).resolve(data not statically known)` |
| _resolve_openapi_path | Path (src/llm_wiki_cli/services….py:_resolve_openapi_path) | 1187 | `Path(source_root)` |
| _resolve_openapi_path | Path(…).expanduser | 1188 | `Path(path).expanduser(data not statically known)` |
| _resolve_openapi_path | Path (src/llm_wiki_cli/services….py:_resolve_openapi_path) | 1188 | `Path(path)` |
| _resolve_openapi_path | candidate.is_absolute | 1189 | `candidate.is_absolute(data not statically known)` |
| _resolve_openapi_path | Path(…).relative_to(…).as_posix | 1192 | `Path(os.path.abspath(candidate)).relative_to(root).as_posix(data not statically known)` |
| _resolve_openapi_path | Path(…).relative_to | 1192 | `Path(os.path.abspath(candidate)).relative_to(root)` |
| _resolve_openapi_path | Path (src/llm_wiki_cli/services….py:_resolve_openapi_path) | 1192 | `Path(os.path.abspath(...))` |
| _resolve_openapi_path | os.path.abspath | 1192 | `os.path.abspath(candidate)` |

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
| step_limit | `build_api_contracts` | `first 12 steps` | 0 |
| truncated_flow | `build_api_contracts` | `depth limit` | 0 |

## Behavior

This flow starts at `build_api_contracts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
