# open_windows_guarded_lock_file

**Entry point:** `open_windows_guarded_lock_file` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as open_windows_guarded_lock_file
    participant p1 as WindowsFileGuardError
    participant p2 as WinDLL
    participant p3 as _private_windows_security_attributes
    participant p4 as POINTER
    participant p5 as _current_windows_user_sid
    participant p6 as HANDLE
    participant p7 as open_process_token
    participant p8 as get_current_process
    participant p9 as byref
    participant p10 as WinError
    participant p11 as get_last_error
    participant p12 as WindowsSecurityGuardError
    participant p13 as DWORD
    participant p14 as get_token_information
    participant p15 as create_string_buffer
    p0->>p1: WindowsFileGuardError
    p0-->>p2: WinDLL
    p0->>p3: _private_windows_security_attributes
    p3-->>p2: WinDLL
    p3-->>p2: WinDLL
    p3-->>p4: POINTER
    p3-->>p4: POINTER
    p3->>p5: _current_windows_user_sid
    p5-->>p2: WinDLL
    p5-->>p2: WinDLL
    p5-->>p4: POINTER
    p5-->>p4: POINTER
    p5-->>p6: HANDLE
    p5-->>p7: open_process_token
    p5-->>p8: get_current_process
    p5-->>p9: byref
    p5-->>p10: WinError
    p5-->>p11: get_last_error
    p5->>p12: WindowsSecurityGuardError
    p5-->>p13: DWORD
    p5-->>p14: get_token_information
    p5-->>p9: byref
    p5-->>p10: WinError
    p5-->>p11: get_last_error
    p5->>p12: WindowsSecurityGuardError
    p5-->>p15: create_string_buffer
    p5-->>p14: get_token_information
    p5-->>p9: byref
    p5-->>p10: WinError
    p5-->>p11: get_last_error
```

> Call sequence diagram shows 30 of 169 interactions; 139 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. open_windows_guarded_lock_file"]
    s2["2. WindowsFileGuardError"]
    s3["3. WinDLL"]
    s4["4. _private_windows_security_attributes"]
    s5["5. WinDLL"]
    s6["6. WinDLL"]
    s7["7. POINTER"]
    s8["8. POINTER"]
    s9["9. _current_windows_user_sid"]
    s10["10. WinDLL"]
    s11["11. WinDLL"]
    s12["12. POINTER"]
    s1 -->|"WindowsFileGuardError('Guarded Windows lock files are unavailable on this platform.')"| s2
    s1 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s3
    s1 -->|"_private_windows_security_attributes(directory=False)"| s4
    s4 -. "ctypes.WinDLL('advapi32', use_last_error=True)" .-> s5
    s4 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s6
    s4 -. "ctypes.POINTER(wintypes.LPVOID)" .-> s7
    s4 -. "ctypes.POINTER(wintypes.DWORD)" .-> s8
    s4 -->|"_current_windows_user_sid(data not statically known)"| s9
    s9 -. "ctypes.WinDLL('advapi32', use_last_error=True)" .-> s10
    s9 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s11
    s9 -. "ctypes.POINTER(wintypes.HANDLE)" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s4 "../modules/filesystem_guard.md"
    click s9 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `open_windows_guarded_lock_file` | `path: Path` | `os`, `os` | `create_file.argtypes`, `create_file.restype` | `(...)` |
| `WindowsFileGuardError` | - | - | - | - |
| `WinDLL` | - | - | - | - |
| `_private_windows_security_attributes` | `directory: bool` | - | `convert.argtypes`, `convert.restype`, `local_free.argtypes`, `local_free.restype` | - |
| `WinDLL` | - | - | - | - |
| `WinDLL` | - | - | - | - |
| `POINTER` | - | - | - | - |
| `POINTER` | - | - | - | - |
| `_current_windows_user_sid` | - | `ctypes` | `open_process_token.argtypes`, `open_process_token.restype`, `get_token_information.argtypes`, `get_token_information.restype`, `get_current_process.argtypes`, `get_current_process.restype` | `_windows_sid_string(...)` |
| `WinDLL` | - | - | - | - |
| `WinDLL` | - | - | - | - |
| `POINTER` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| open_windows_guarded_lock_file | WindowsFileGuardError | 600 | `WindowsFileGuardError('Guarded Windows lock files are unavailable on this platform.')` |
| open_windows_guarded_lock_file | WinDLL | 605 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| open_windows_guarded_lock_file | _private_windows_security_attributes | 619 | `_private_windows_security_attributes(directory=False)` |
| _private_windows_security_attributes | WinDLL | 930 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _private_windows_security_attributes | WinDLL | 931 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _private_windows_security_attributes | POINTER | 936 | `ctypes.POINTER(wintypes.LPVOID)` |
| _private_windows_security_attributes | POINTER | 937 | `ctypes.POINTER(wintypes.DWORD)` |
| _private_windows_security_attributes | _current_windows_user_sid | 951 | `_current_windows_user_sid(data not statically known)` |
| _current_windows_user_sid | WinDLL | 979 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _current_windows_user_sid | WinDLL | 980 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _current_windows_user_sid | POINTER | 985 | `ctypes.POINTER(wintypes.HANDLE)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `open_windows_guarded_lock_file` | `ctypes.WinDLL` | 605 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 930 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 931 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 936 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 937 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 979 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 980 |
| external_call | `_current_windows_user_sid` | `ctypes.POINTER` | 985 |
| step_limit | `open_windows_guarded_lock_file` | `first 12 steps` | 0 |

## Behavior

This flow starts at `open_windows_guarded_lock_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
