# create_private_windows_directory

**Entry point:** `create_private_windows_directory` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as create_private_windows_directory
    participant p1 as WindowsDirectoryGuardError
    participant p2 as WinDLL
    participant p3 as Path
    participant p4 as uuid4
    participant p5 as _private_windows_security_attributes
    participant p6 as POINTER
    participant p7 as _current_windows_user_sid
    participant p8 as HANDLE
    participant p9 as open_process_token
    participant p10 as get_current_process
    participant p11 as byref
    participant p12 as WinError
    participant p13 as get_last_error
    participant p14 as WindowsSecurityGuardError
    participant p15 as DWORD
    participant p16 as get_token_information
    participant p17 as create_string_buffer
    p0->>p1: WindowsDirectoryGuardError
    p0-->>p2: WinDLL
    p0-->>p3: Path
    p0-->>p4: uuid4
    p0->>p5: _private_windows_security_attributes
    p5-->>p2: WinDLL
    p5-->>p2: WinDLL
    p5-->>p6: POINTER
    p5-->>p6: POINTER
    p5->>p7: _current_windows_user_sid
    p7-->>p2: WinDLL
    p7-->>p2: WinDLL
    p7-->>p6: POINTER
    p7-->>p6: POINTER
    p7-->>p8: HANDLE
    p7-->>p9: open_process_token
    p7-->>p10: get_current_process
    p7-->>p11: byref
    p7-->>p12: WinError
    p7-->>p13: get_last_error
    p7->>p14: WindowsSecurityGuardError
    p7-->>p15: DWORD
    p7-->>p16: get_token_information
    p7-->>p11: byref
    p7-->>p12: WinError
    p7-->>p13: get_last_error
    p7->>p14: WindowsSecurityGuardError
    p7-->>p17: create_string_buffer
    p7-->>p16: get_token_information
    p7-->>p11: byref
```

> Call sequence diagram shows 30 of 190 interactions; 160 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. create_private_windows_directory"]
    s2["2. WindowsDirectoryGuardError"]
    s3["3. WinDLL"]
    s4["4. Path"]
    s5["5. uuid4"]
    s6["6. _private_windows_security_attributes"]
    s7["7. WinDLL"]
    s8["8. WinDLL"]
    s9["9. POINTER"]
    s10["10. POINTER"]
    s11["11. _current_windows_user_sid"]
    s12["12. WinDLL"]
    s1 -->|"WindowsDirectoryGuardError('Private Windows directory creation is unavailable on this platform.')"| s2
    s1 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s3
    s1 -. "Path(path)" .-> s4
    s1 -. "uuid.uuid4(data not statically known)" .-> s5
    s1 -->|"_private_windows_security_attributes(directory=True)"| s6
    s6 -. "ctypes.WinDLL('advapi32', use_last_error=True)" .-> s7
    s6 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s8
    s6 -. "ctypes.POINTER(wintypes.LPVOID)" .-> s9
    s6 -. "ctypes.POINTER(wintypes.DWORD)" .-> s10
    s6 -->|"_current_windows_user_sid(data not statically known)"| s11
    s11 -. "ctypes.WinDLL('advapi32', use_last_error=True)" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `create_private_windows_directory` | `path: Path` | `os` | `create_directory.argtypes`, `create_directory.restype`, `remove_directory.argtypes`, `remove_directory.restype` | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `WinDLL` | - | - | - | - |
| `Path` | - | - | - | - |
| `uuid4` | - | - | - | - |
| `_private_windows_security_attributes` | `directory: bool` | - | `convert.argtypes`, `convert.restype`, `local_free.argtypes`, `local_free.restype` | - |
| `WinDLL` | - | - | - | - |
| `WinDLL` | - | - | - | - |
| `POINTER` | - | - | - | - |
| `POINTER` | - | - | - | - |
| `_current_windows_user_sid` | - | `ctypes` | `open_process_token.argtypes`, `open_process_token.restype`, `get_token_information.argtypes`, `get_token_information.restype`, `get_current_process.argtypes`, `get_current_process.restype` | `_windows_sid_string(...)` |
| `WinDLL` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| create_private_windows_directory | WindowsDirectoryGuardError | 484 | `WindowsDirectoryGuardError('Private Windows directory creation is unavailable on this platform.')` |
| create_private_windows_directory | WinDLL | 489 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| create_private_windows_directory | Path | 497 | `Path(path)` |
| create_private_windows_directory | uuid4 | 498 | `uuid.uuid4(data not statically known)` |
| create_private_windows_directory | _private_windows_security_attributes | 501 | `_private_windows_security_attributes(directory=True)` |
| _private_windows_security_attributes | WinDLL | 930 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _private_windows_security_attributes | WinDLL | 931 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _private_windows_security_attributes | POINTER | 936 | `ctypes.POINTER(wintypes.LPVOID)` |
| _private_windows_security_attributes | POINTER | 937 | `ctypes.POINTER(wintypes.DWORD)` |
| _private_windows_security_attributes | _current_windows_user_sid | 951 | `_current_windows_user_sid(data not statically known)` |
| _current_windows_user_sid | WinDLL | 979 | `ctypes.WinDLL('advapi32', use_last_error=True)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `create_private_windows_directory` | `ctypes.WinDLL` | 489 |
| external_call | `create_private_windows_directory` | `uuid.uuid4` | 498 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 930 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 931 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 936 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 937 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 979 |
| step_limit | `create_private_windows_directory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `create_private_windows_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
