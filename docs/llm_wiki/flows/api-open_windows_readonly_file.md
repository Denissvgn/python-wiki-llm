# open_windows_readonly_file

**Entry point:** `open_windows_readonly_file` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as open_windows_readonly_file
    participant p1 as WindowsFileGuardError
    participant p2 as _open_windows_readonly_file_handle
    participant p3 as WinDLL
    participant p4 as create_file
    participant p5 as _windows_api_path
    participant p6 as abspath
    participant p7 as fspath
    participant p8 as startswith
    participant p9 as HANDLE
    participant p10 as WinError
    participant p11 as get_last_error
    participant p12 as int
    participant p13 as get_file_type
    participant p14 as _ByHandleFileInformation
    participant p15 as get_information
    participant p16 as byref
    participant p17 as _verify_windows_handle_restrictive_dacl
    p0->>p1: WindowsFileGuardError
    p0->>p2: _open_windows_readonly_file_handle
    p2-->>p3: WinDLL
    p2-->>p4: create_file
    p2->>p5: _windows_api_path
    p5-->>p6: abspath
    p5-->>p7: fspath
    p5-->>p8: startswith
    p5-->>p8: startswith
    p2-->>p9: HANDLE
    p2-->>p10: WinError
    p2-->>p11: get_last_error
    p2->>p1: WindowsFileGuardError
    p2-->>p12: int
    p2-->>p12: int
    p2-->>p13: get_file_type
    p2->>p1: WindowsFileGuardError
    p2-->>p14: _ByHandleFileInformation
    p2-->>p15: get_information
    p2-->>p16: byref
    p2-->>p10: WinError
    p2-->>p11: get_last_error
    p2->>p1: WindowsFileGuardError
    p2-->>p12: int
    p2->>p1: WindowsFileGuardError
    p2-->>p12: int
    p2->>p1: WindowsFileGuardError
    p2->>p17: _verify_windows_handle_restrictive_dacl
    p17-->>p3: WinDLL
    p17-->>p3: WinDLL
```

> Call sequence diagram shows 30 of 168 interactions; 138 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. open_windows_readonly_file"]
    s2["2. WindowsFileGuardError"]
    s3["3. _open_windows_readonly_file_handle"]
    s4["4. WinDLL"]
    s5["5. create_file"]
    s6["6. _windows_api_path"]
    s7["7. abspath"]
    s8["8. fspath"]
    s9["9. startswith"]
    s10["10. startswith"]
    s11["11. HANDLE"]
    s12["12. WinError"]
    s1 -->|"WindowsFileGuardError('Windows read-only file guards are unavailable on this platform.')"| s2
    s1 -->|"_open_windows_readonly_file_handle(Path(...), require_restrictive_dacl=True)"| s3
    s3 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s4
    s3 -. "create_file(_windows_api_path(...), ..., 1, None, 3, ..., None)" .-> s5
    s3 -->|"_windows_api_path(path)"| s6
    s6 -. "os.path.abspath(os.fspath(...))" .-> s7
    s6 -. "os.fspath(path)" .-> s8
    s6 -. "value.startswith('\\\\?\\')" .-> s9
    s6 -. "value.startswith('\\\\')" .-> s10
    s3 -. "wintypes.HANDLE(...)" .-> s11
    s3 -. "ctypes.WinError(ctypes.get_last_error(...))" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `open_windows_readonly_file` | `path: Path`, `require_restrictive_dacl: bool` | `os`, `os`, `os`, `os`, `WindowsIdentityUnavailableError`, `WindowsFileGuardError` | - | - |
| `WindowsFileGuardError` | - | - | - | - |
| `_open_windows_readonly_file_handle` | `path: Path`, `require_restrictive_dacl: bool` | - | `create_file.argtypes`, `create_file.restype`, `get_file_type.argtypes`, `get_file_type.restype`, `get_information.argtypes`, `get_information.restype` | `native_handle` |
| `WinDLL` | - | - | - | - |
| `create_file` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `startswith` | - | - | - | - |
| `startswith` | - | - | - | - |
| `HANDLE` | - | - | - | - |
| `WinError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| open_windows_readonly_file | WindowsFileGuardError | 333 | `WindowsFileGuardError('Windows read-only file guards are unavailable on this platform.')` |
| open_windows_readonly_file | _open_windows_readonly_file_handle | 338 | `_open_windows_readonly_file_handle(Path(...), require_restrictive_dacl=True)` |
| _open_windows_readonly_file_handle | WinDLL | 394 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _open_windows_readonly_file_handle | create_file | 409 | `create_file(_windows_api_path(...), ..., 1, None, 3, ..., None)` |
| _open_windows_readonly_file_handle | _windows_api_path | 410 | `_windows_api_path(path)` |
| _windows_api_path | abspath | 1285 | `os.path.abspath(os.fspath(...))` |
| _windows_api_path | fspath | 1285 | `os.fspath(path)` |
| _windows_api_path | startswith | 1286 | `value.startswith('\\\\?\\')` |
| _windows_api_path | startswith | 1288 | `value.startswith('\\\\')` |
| _open_windows_readonly_file_handle | HANDLE | 418 | `wintypes.HANDLE(...)` |
| _open_windows_readonly_file_handle | WinError | 420 | `ctypes.WinError(ctypes.get_last_error(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_open_windows_readonly_file_handle` | `ctypes.WinDLL` | 394 |
| unresolved_call | `_open_windows_readonly_file_handle` | `create_file` | 409 |
| external_call | `_windows_api_path` | `os.path.abspath` | 1285 |
| external_call | `_windows_api_path` | `os.fspath` | 1285 |
| unresolved_call | `_windows_api_path` | `value.startswith` | 1286 |
| unresolved_call | `_windows_api_path` | `value.startswith` | 1288 |
| external_call | `_open_windows_readonly_file_handle` | `wintypes.HANDLE` | 418 |
| external_call | `_open_windows_readonly_file_handle` | `ctypes.WinError` | 420 |
| step_limit | `open_windows_readonly_file` | `first 12 steps` | 0 |

## Behavior

This flow starts at `open_windows_readonly_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
