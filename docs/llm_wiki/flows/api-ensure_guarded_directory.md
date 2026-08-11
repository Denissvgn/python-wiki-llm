# ensure_guarded_directory

**Entry point:** `ensure_guarded_directory` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as ensure_guarded_directory
    participant p1 as Path
    participant p2 as is_absolute
    participant p3 as OSError
    participant p4 as guard_windows_directory_chain
    participant p5 as WindowsDirectoryGuardError
    participant p6 as abspath
    participant p7 as fspath
    participant p8 as append
    participant p9 as _open_windows_directory_guard
    participant p10 as WinDLL
    participant p11 as create_file
    participant p12 as _windows_api_path
    participant p13 as startswith
    participant p14 as HANDLE
    participant p15 as get_last_error
    participant p16 as WinError
    participant p17 as _WindowsDirectoryGuardUnavailableError
    participant p18 as _ByHandleFileInformation
    participant p19 as get_information
    participant p20 as byref
    p0-->>p1: Path
    p0-->>p2: is_absolute
    p0-->>p3: OSError
    p0-->>p1: Path
    p0->>p4: guard_windows_directory_chain
    p4->>p5: WindowsDirectoryGuardError
    p4-->>p1: Path
    p4-->>p6: abspath
    p4-->>p7: fspath
    p4->>p5: WindowsDirectoryGuardError
    p4-->>p1: Path
    p4-->>p8: append
    p4->>p9: _open_windows_directory_guard
    p9-->>p10: WinDLL
    p9-->>p11: create_file
    p9->>p12: _windows_api_path
    p12-->>p6: abspath
    p12-->>p7: fspath
    p12-->>p13: startswith
    p12-->>p13: startswith
    p9-->>p14: HANDLE
    p9-->>p15: get_last_error
    p9-->>p16: WinError
    p9->>p17: _WindowsDirectoryGuardUnavailableError
    p9->>p5: WindowsDirectoryGuardError
    p9-->>p18: _ByHandleFileInformation
    p9-->>p19: get_information
    p9-->>p20: byref
    p9-->>p16: WinError
    p9-->>p15: get_last_error
```

> Call sequence diagram shows 30 of 230 interactions; 200 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. ensure_guarded_directory"]
    s2["2. Path"]
    s3["3. is_absolute"]
    s4["4. OSError"]
    s5["5. Path"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path"]
    s9["9. abspath"]
    s10["10. fspath"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path"]
    s1 -. "Path(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError(...)" .-> s4
    s1 -. "Path(target.anchor)" .-> s5
    s1 -->|"guard_windows_directory_chain(Path(...), ..., create_missing=True)"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath(os.fspath(...))" .-> s9
    s6 -. "os.fspath(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path(root_path.anchor)" .-> s12
    b0["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b0
    b1["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b2
    click s1 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `ensure_guarded_directory` | `path: Path`, `mode: int` | `os`, `os`, `os`, `os` | - | `target`, `target`, `target` |
| `Path` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `Path` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| ensure_guarded_directory | Path | 1631 | `Path(path)` |
| ensure_guarded_directory | is_absolute | 1632 | `target.is_absolute(data not statically known)` |
| ensure_guarded_directory | OSError | 1633 | `OSError(...)` |
| ensure_guarded_directory | Path | 1634 | `Path(target.anchor)` |
| ensure_guarded_directory | guard_windows_directory_chain | 1637 | `guard_windows_directory_chain(Path(...), ..., create_missing=True)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | abspath | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | fspath | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path | 179 | `Path(root_path.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `ensure_guarded_directory` | `target.is_absolute` | 1632 |
| unresolved_call | `ensure_guarded_directory` | `OSError` | 1633 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `ensure_guarded_directory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `ensure_guarded_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
