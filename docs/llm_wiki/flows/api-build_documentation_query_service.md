# build_documentation_query_service

**Entry point:** `build_documentation_query_service` (`api`)
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
    participant p0 as build_documentation_query_service
    participant p1 as validate_source_root
    participant p2 as validate_path
    participant p3 as PathValidationError
    participant p4 as resolve
    participant p5 as cwd
    participant p6 as relative_to
    participant p7 as expanduser
    participant p8 as Path
    participant p9 as is_absolute
    participant p10 as is_dir
    participant p11 as abspath
    participant p12 as windows_current_user_sid
    participant p13 as WindowsSecurityGuardError
    participant p14 as _current_windows_user_sid
    participant p15 as WinDLL
    participant p16 as POINTER
    participant p17 as HANDLE
    participant p18 as open_process_token
    participant p19 as get_current_process
    participant p20 as byref
    p0->>p1: validate_source_root
    p1->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p6: relative_to
    p2->>p3: PathValidationError
    p1-->>p7: expanduser
    p1-->>p8: Path
    p1-->>p9: is_absolute
    p1-->>p5: cwd
    p1-->>p4: resolve
    p1->>p3: PathValidationError
    p1-->>p10: is_dir
    p1->>p3: PathValidationError
    p1-->>p8: Path
    p1-->>p11: abspath
    p1->>p12: windows_current_user_sid
    p12->>p13: WindowsSecurityGuardError
    p12->>p14: _current_windows_user_sid
    p14-->>p15: WinDLL
    p14-->>p15: WinDLL
    p14-->>p16: POINTER
    p14-->>p16: POINTER
    p14-->>p17: HANDLE
    p14-->>p18: open_process_token
    p14-->>p19: get_current_process
    p14-->>p20: byref
```

> Call sequence diagram shows 30 of 481 interactions; 451 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_documentation_query_service"]
    s2["2. validate_source_root"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. resolve"]
    s6["6. cwd"]
    s7["7. resolve"]
    s8["8. cwd"]
    s9["9. relative_to"]
    s10["10. PathValidationError"]
    s11["11. expanduser"]
    s12["12. Path"]
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)"| s2
    s2 -->|"validate_path(path, label)"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve(data not statically known)" .-> s7
    s3 -. "Path.cwd(data not statically known)" .-> s8
    s3 -. "resolved.relative_to(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s2 -. "Path(path).expanduser(data not statically known)" .-> s11
    s2 -. "Path(path)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/config.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_documentation_query_service` | `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `extract_cmd`, `extract_cmd`, `extract_cmd`, `build_flow`, `evaluate_surface_index`, `context_cmd`, `context_cmd`, `analyze_dependencies` | - | `build_live_documentation_query_service(...)` |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_documentation_query_service | validate_source_root | 858 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)` |
| validate_source_root | validate_path | 156 | `validate_path(path, label)` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 134 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 136 | `PathValidationError(...)` |
| validate_source_root | expanduser | 159 | `Path(path).expanduser(data not statically known)` |
| validate_source_root | Path | 159 | `Path(path)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 134 |
| unresolved_call | `validate_source_root` | `Path(path).expanduser` | 159 |
| step_limit | `build_documentation_query_service` | `first 12 steps` | 0 |
| truncated_flow | `build_documentation_query_service` | `depth limit` | 0 |

## Behavior

This flow starts at `build_documentation_query_service` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
