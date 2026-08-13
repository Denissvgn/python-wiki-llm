# guarded_tree_manifest

**Entry point:** `guarded_tree_manifest` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as guarded_tree_manifest
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
    participant p21 as _close_windows_handle
    p0-->>p1: Path
    p0-->>p2: is_absolute
    p0-->>p3: OSError
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
    p9->>p21: _close_windows_handle
```

> Call sequence diagram shows 30 of 335 interactions; 305 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. guarded_tree_manifest"]
    s2["2. Path"]
    s3["3. is_absolute"]
    s4["4. OSError"]
    s5["5. guard_windows_directory_chain"]
    s6["6. WindowsDirectoryGuardError"]
    s7["7. Path"]
    s8["8. abspath"]
    s9["9. fspath"]
    s10["10. WindowsDirectoryGuardError"]
    s11["11. Path"]
    s12["12. append"]
    s1 -. "Path(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError(...)" .-> s4
    s1 -->|"guard_windows_directory_chain(Path(...), ...)"| s5
    s5 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s6
    s5 -. "Path(os.path.abspath(...))" .-> s7
    s5 -. "os.path.abspath(os.fspath(...))" .-> s8
    s5 -. "os.fspath(root)" .-> s9
    s5 -->|"WindowsDirectoryGuardError(...)"| s10
    s5 -. "Path(root_path.anchor)" .-> s11
    s5 -. "handles.append(_open_windows_directory_guard(...))" .-> s12
    b0["mutation handles.append"]
    s5 -. "mutation handles.append" .-> b0
    b1["mutation handles.append"]
    s5 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s5 -. "mutation handles.append" .-> b2
    click s1 "../modules/filesystem_guard.md"
    click s5 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s10 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `guarded_tree_manifest` | `path: Path` | `os`, `os`, `os`, `os` | - | `_guarded_tree_manifest_windows_path(...)`, `_guarded_tree_manifest_posix_fd(...)` |
| `Path` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| guarded_tree_manifest | Path | 1509 | `Path(path)` |
| guarded_tree_manifest | is_absolute | 1510 | `target.is_absolute(data not statically known)` |
| guarded_tree_manifest | OSError | 1511 | `OSError(...)` |
| guarded_tree_manifest | guard_windows_directory_chain | 1513 | `guard_windows_directory_chain(Path(...), ...)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | abspath | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | fspath | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path | 179 | `Path(root_path.anchor)` |
| guard_windows_directory_chain | append | 182 | `handles.append(_open_windows_directory_guard(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `guarded_tree_manifest` | `target.is_absolute` | 1510 |
| unresolved_call | `guarded_tree_manifest` | `OSError` | 1511 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `guarded_tree_manifest` | `first 12 steps` | 0 |

## Behavior

This flow starts at `guarded_tree_manifest` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
