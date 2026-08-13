# guard_windows_directory_chain

**Entry point:** `guard_windows_directory_chain` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as guard_windows_directory_chain
    participant p1 as WindowsDirectoryGuardError
    participant p2 as Path
    participant p3 as abspath
    participant p4 as fspath
    participant p5 as append
    participant p6 as _open_windows_directory_guard
    participant p7 as WinDLL
    participant p8 as create_file
    participant p9 as _windows_api_path
    participant p10 as startswith
    participant p11 as HANDLE
    participant p12 as get_last_error
    participant p13 as WinError
    participant p14 as _WindowsDirectoryGuardUnavailableError
    participant p15 as _ByHandleFileInformation
    participant p16 as get_information
    participant p17 as byref
    participant p18 as _close_windows_handle
    participant p19 as close_handle
    participant p20 as int
    p0->>p1: WindowsDirectoryGuardError
    p0-->>p2: Path
    p0-->>p3: abspath
    p0-->>p4: fspath
    p0->>p1: WindowsDirectoryGuardError
    p0-->>p2: Path
    p0-->>p5: append
    p0->>p6: _open_windows_directory_guard
    p6-->>p7: WinDLL
    p6-->>p8: create_file
    p6->>p9: _windows_api_path
    p9-->>p3: abspath
    p9-->>p4: fspath
    p9-->>p10: startswith
    p9-->>p10: startswith
    p6-->>p11: HANDLE
    p6-->>p12: get_last_error
    p6-->>p13: WinError
    p6->>p14: _WindowsDirectoryGuardUnavailableError
    p6->>p1: WindowsDirectoryGuardError
    p6-->>p15: _ByHandleFileInformation
    p6-->>p16: get_information
    p6-->>p17: byref
    p6-->>p13: WinError
    p6-->>p12: get_last_error
    p6->>p18: _close_windows_handle
    p18-->>p7: WinDLL
    p18-->>p19: close_handle
    p18-->>p11: HANDLE
    p6-->>p20: int
```

> Call sequence diagram shows 30 of 212 interactions; 182 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. guard_windows_directory_chain"]
    s2["2. WindowsDirectoryGuardError"]
    s3["3. Path"]
    s4["4. abspath"]
    s5["5. fspath"]
    s6["6. WindowsDirectoryGuardError"]
    s7["7. Path"]
    s8["8. append"]
    s9["9. _open_windows_directory_guard"]
    s10["10. WinDLL"]
    s11["11. create_file"]
    s12["12. _windows_api_path"]
    s1 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s2
    s1 -. "Path(os.path.abspath(...))" .-> s3
    s1 -. "os.path.abspath(os.fspath(...))" .-> s4
    s1 -. "os.fspath(root)" .-> s5
    s1 -->|"WindowsDirectoryGuardError(...)"| s6
    s1 -. "Path(root_path.anchor)" .-> s7
    s1 -. "handles.append(_open_windows_directory_guard(...))" .-> s8
    s1 -->|"_open_windows_directory_guard(current)"| s9
    s9 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s10
    s9 -. "create_file(_windows_api_path(...), desired_access, ..., None, _OPEN_EXISTING, ..., None)" .-> s11
    s9 -->|"_windows_api_path(path)"| s12
    b0["mutation handles.append"]
    s1 -. "mutation handles.append" .-> b0
    b1["mutation handles.append"]
    s1 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s1 -. "mutation handles.append" .-> b2
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s9 "../modules/filesystem_guard.md"
    click s12 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `append` | - | - | - | - |
| `_open_windows_directory_guard` | `path: Path`, `require_restrictive_dacl: bool` | `_FILE_LIST_DIRECTORY`, `_FILE_READ_ATTRIBUTES`, `_READ_CONTROL`, `_FILE_SHARE_READ`, `_FILE_SHARE_WRITE`, `_OPEN_EXISTING`, `_FILE_FLAG_BACKUP_SEMANTICS`, `_FILE_FLAG_OPEN_REPARSE_POINT` | `create_file.argtypes`, `create_file.restype`, `get_information.argtypes`, `get_information.restype` | `int(...)` |
| `WinDLL` | - | - | - | - |
| `create_file` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | abspath | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | fspath | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path | 179 | `Path(root_path.anchor)` |
| guard_windows_directory_chain | append | 182 | `handles.append(_open_windows_directory_guard(...))` |
| guard_windows_directory_chain | _open_windows_directory_guard | 182 | `_open_windows_directory_guard(current)` |
| _open_windows_directory_guard | WinDLL | 235 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _open_windows_directory_guard | create_file | 259 | `create_file(_windows_api_path(...), desired_access, ..., None, _OPEN_EXISTING, ..., None)` |
| _open_windows_directory_guard | _windows_api_path | 260 | `_windows_api_path(path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| external_call | `_open_windows_directory_guard` | `ctypes.WinDLL` | 235 |
| unresolved_call | `_open_windows_directory_guard` | `create_file` | 259 |
| step_limit | `guard_windows_directory_chain` | `first 12 steps` | 0 |

## Behavior

This flow starts at `guard_windows_directory_chain` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
