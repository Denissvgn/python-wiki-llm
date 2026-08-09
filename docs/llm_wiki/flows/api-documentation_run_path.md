# documentation_run_path

**Entry point:** `documentation_run_path` (`api`)
**Source:** [workspace](../modules/workspace.md)
**Modules touched:** [documentation_run_contracts](../modules/documentation_run_contracts.md), [workspace](../modules/workspace.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as documentation_run_path
    participant p1 as _resolve_workspace_root_argument
    participant p2 as Path
    participant p3 as abspath
    participant p4 as fspath
    participant p5 as expanduser
    participant p6 as lexists
    participant p7 as lstat
    participant p8 as DocumentationIntegrityError
    participant p9 as bool
    participant p10 as getattr
    participant p11 as S_ISLNK
    participant p12 as S_ISDIR
    participant p13 as resolve
    participant p14 as _assert_existing_workspace_layout_safe
    participant p15 as _assert_safe_workspace_directory
    p0->>p1: _resolve_workspace_root_argument
    p1-->>p2: Path
    p1-->>p3: abspath
    p1-->>p4: fspath
    p1-->>p5: expanduser
    p1-->>p2: Path
    p1-->>p6: lexists
    p1-->>p7: lstat
    p1->>p8: DocumentationIntegrityError
    p1-->>p9: bool
    p1-->>p10: getattr
    p1-->>p9: bool
    p1-->>p10: getattr
    p1-->>p11: S_ISLNK
    p1->>p8: DocumentationIntegrityError
    p1-->>p12: S_ISDIR
    p1->>p8: DocumentationIntegrityError
    p1-->>p13: resolve
    p1-->>p6: lexists
    p1->>p14: _assert_existing_workspace_layout_safe
    p14-->>p6: lexists
    p14->>p15: _assert_safe_workspace_directory
    p15-->>p7: lstat
    p15->>p8: DocumentationIntegrityError
    p15-->>p9: bool
    p15-->>p10: getattr
    p15-->>p9: bool
    p15-->>p10: getattr
    p15-->>p11: S_ISLNK
    p15->>p8: DocumentationIntegrityError
```

> Call sequence diagram shows 30 of 82 interactions; 52 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. documentation_run_path"]
    s2["2. _resolve_workspace_root_argument"]
    s3["3. Path"]
    s4["4. abspath"]
    s5["5. fspath"]
    s6["6. expanduser"]
    s7["7. Path"]
    s8["8. lexists"]
    s9["9. lstat"]
    s10["10. DocumentationIntegrityError"]
    s11["11. bool"]
    s12["12. getattr"]
    s1 -->|"_resolve_workspace_root_argument(workspace)"| s2
    s2 -. "Path(os.path.abspath(...))" .-> s3
    s2 -. "os.path.abspath(os.fspath(...))" .-> s4
    s2 -. "os.fspath(...)" .-> s5
    s2 -. "Path(workspace).expanduser(data not statically known)" .-> s6
    s2 -. "Path(workspace)" .-> s7
    s2 -. "os.path.lexists(requested)" .-> s8
    s2 -. "requested.lstat(data not statically known)" .-> s9
    s2 -->|"DocumentationIntegrityError(...)"| s10
    s2 -. "bool(getattr(...))" .-> s11
    s2 -. "getattr(entry_stat, 'st_reparse_tag', 0)" .-> s12
    click s1 "../modules/workspace.md"
    click s2 "../modules/workspace.md"
    click s10 "../modules/documentation_run_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `documentation_run_path` | `workspace: str \| Path` | - | - | `...` |
| `_resolve_workspace_root_argument` | `workspace: str \| Path` | - | - | `resolved` |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `lexists` | - | - | - | - |
| `lstat` | - | - | - | - |
| `DocumentationIntegrityError` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| documentation_run_path | _resolve_workspace_root_argument | 10 | `_resolve_workspace_root_argument(workspace)` |
| _resolve_workspace_root_argument | Path | 102 | `Path(os.path.abspath(...))` |
| _resolve_workspace_root_argument | abspath | 102 | `os.path.abspath(os.fspath(...))` |
| _resolve_workspace_root_argument | fspath | 102 | `os.fspath(...)` |
| _resolve_workspace_root_argument | expanduser | 102 | `Path(workspace).expanduser(data not statically known)` |
| _resolve_workspace_root_argument | Path | 102 | `Path(workspace)` |
| _resolve_workspace_root_argument | lexists | 103 | `os.path.lexists(requested)` |
| _resolve_workspace_root_argument | lstat | 105 | `requested.lstat(data not statically known)` |
| _resolve_workspace_root_argument | DocumentationIntegrityError | 107 | `DocumentationIntegrityError(...)` |
| _resolve_workspace_root_argument | bool | 110 | `bool(getattr(...))` |
| _resolve_workspace_root_argument | getattr | 110 | `getattr(entry_stat, 'st_reparse_tag', 0)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.abspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.fspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `Path(workspace).expanduser` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.lexists` | 103 |
| unresolved_call | `_resolve_workspace_root_argument` | `requested.lstat` | 105 |
| unresolved_call | `_resolve_workspace_root_argument` | `getattr` | 110 |
| step_limit | `documentation_run_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `documentation_run_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
