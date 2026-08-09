# verify_windows_restrictive_dacl

**Entry point:** `verify_windows_restrictive_dacl` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verify_windows_restrictive_dacl
    participant p1 as WindowsSecurityGuardError
    participant p2 as lstat
    participant p3 as Path
    participant p4 as S_ISDIR
    participant p5 as _open_windows_directory_guard
    participant p6 as WinDLL
    participant p7 as create_file
    participant p8 as _windows_api_path
    participant p9 as abspath
    participant p10 as fspath
    participant p11 as startswith
    participant p12 as HANDLE
    participant p13 as get_last_error
    participant p14 as WinError
    participant p15 as _WindowsDirectoryGuardUnavailableError
    participant p16 as WindowsDirectoryGuardError
    participant p17 as _ByHandleFileInformation
    participant p18 as get_information
    participant p19 as byref
    participant p20 as _close_windows_handle
    participant p21 as close_handle
    participant p22 as int
    p0->>p1: WindowsSecurityGuardError
    p0-->>p2: lstat
    p0-->>p3: Path
    p0->>p1: WindowsSecurityGuardError
    p0-->>p4: S_ISDIR
    p0->>p5: _open_windows_directory_guard
    p5-->>p6: WinDLL
    p5-->>p7: create_file
    p5->>p8: _windows_api_path
    p8-->>p9: abspath
    p8-->>p10: fspath
    p8-->>p11: startswith
    p8-->>p11: startswith
    p5-->>p12: HANDLE
    p5-->>p13: get_last_error
    p5-->>p14: WinError
    p5->>p15: _WindowsDirectoryGuardUnavailableError
    p5->>p16: WindowsDirectoryGuardError
    p5-->>p17: _ByHandleFileInformation
    p5-->>p18: get_information
    p5-->>p19: byref
    p5-->>p14: WinError
    p5-->>p13: get_last_error
    p5->>p20: _close_windows_handle
    p20-->>p6: WinDLL
    p20-->>p21: close_handle
    p20-->>p12: HANDLE
    p5-->>p22: int
    p5->>p16: WindowsDirectoryGuardError
    p5-->>p22: int
```

> Call sequence diagram shows 30 of 183 interactions; 153 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verify_windows_restrictive_dacl"]
    s2["2. WindowsSecurityGuardError"]
    s3["3. lstat"]
    s4["4. Path"]
    s5["5. WindowsSecurityGuardError"]
    s6["6. S_ISDIR"]
    s7["7. _open_windows_directory_guard"]
    s8["8. WinDLL"]
    s9["9. create_file"]
    s10["10. _windows_api_path"]
    s11["11. abspath"]
    s12["12. fspath"]
    s1 -->|"WindowsSecurityGuardError('Windows DACL verification is unavailable on this platform.')"| s2
    s1 -. "Path(path).lstat(data not statically known)" .-> s3
    s1 -. "Path(path)" .-> s4
    s1 -->|"WindowsSecurityGuardError(...)"| s5
    s1 -. "stat.S_ISDIR(payload.st_mode)" .-> s6
    s1 -->|"_open_windows_directory_guard(Path(...), require_restrictive_dacl=True)"| s7
    s7 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s8
    s7 -. "create_file(_windows_api_path(...), desired_access, ..., None, _OPEN_EXISTING, ..., None)" .-> s9
    s7 -->|"_windows_api_path(path)"| s10
    s10 -. "os.path.abspath(os.fspath(...))" .-> s11
    s10 -. "os.fspath(path)" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s5 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s10 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verify_windows_restrictive_dacl` | `path: Path` | `os` | - | `none` |
| `WindowsSecurityGuardError` | - | - | - | - |
| `lstat` | - | - | - | - |
| `Path` | - | - | - | - |
| `WindowsSecurityGuardError` | - | - | - | - |
| `S_ISDIR` | - | - | - | - |
| `_open_windows_directory_guard` | `path: Path`, `require_restrictive_dacl: bool` | `_FILE_LIST_DIRECTORY`, `_FILE_READ_ATTRIBUTES`, `_READ_CONTROL`, `_FILE_SHARE_READ`, `_FILE_SHARE_WRITE`, `_OPEN_EXISTING`, `_FILE_FLAG_BACKUP_SEMANTICS`, `_FILE_FLAG_OPEN_REPARSE_POINT` | `create_file.argtypes`, `create_file.restype`, `get_information.argtypes`, `get_information.restype` | `int(...)` |
| `WinDLL` | - | - | - | - |
| `create_file` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verify_windows_restrictive_dacl | WindowsSecurityGuardError | 706 | `WindowsSecurityGuardError('Windows DACL verification is unavailable on this platform.')` |
| verify_windows_restrictive_dacl | lstat | 709 | `Path(path).lstat(data not statically known)` |
| verify_windows_restrictive_dacl | Path | 709 | `Path(path)` |
| verify_windows_restrictive_dacl | WindowsSecurityGuardError | 711 | `WindowsSecurityGuardError(...)` |
| verify_windows_restrictive_dacl | S_ISDIR | 714 | `stat.S_ISDIR(payload.st_mode)` |
| verify_windows_restrictive_dacl | _open_windows_directory_guard | 715 | `_open_windows_directory_guard(Path(...), require_restrictive_dacl=True)` |
| _open_windows_directory_guard | WinDLL | 230 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _open_windows_directory_guard | create_file | 254 | `create_file(_windows_api_path(...), desired_access, ..., None, _OPEN_EXISTING, ..., None)` |
| _open_windows_directory_guard | _windows_api_path | 255 | `_windows_api_path(path)` |
| _windows_api_path | abspath | 1285 | `os.path.abspath(os.fspath(...))` |
| _windows_api_path | fspath | 1285 | `os.fspath(path)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `verify_windows_restrictive_dacl` | `Path(path).lstat` | 709 |
| external_call | `verify_windows_restrictive_dacl` | `stat.S_ISDIR` | 714 |
| external_call | `_open_windows_directory_guard` | `ctypes.WinDLL` | 230 |
| unresolved_call | `_open_windows_directory_guard` | `create_file` | 254 |
| external_call | `_windows_api_path` | `os.path.abspath` | 1285 |
| external_call | `_windows_api_path` | `os.fspath` | 1285 |
| step_limit | `verify_windows_restrictive_dacl` | `first 12 steps` | 0 |

## Behavior

This flow starts at `verify_windows_restrictive_dacl` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
