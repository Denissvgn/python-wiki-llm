# windows_current_user_sid

**Entry point:** `windows_current_user_sid` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as windows_current_user_sid
    participant p1 as WindowsSecurityGuardError
    participant p2 as _current_windows_user_sid
    participant p3 as WinDLL
    participant p4 as POINTER
    participant p5 as HANDLE
    participant p6 as open_process_token
    participant p7 as get_current_process
    participant p8 as byref
    participant p9 as WinError
    participant p10 as get_last_error
    participant p11 as DWORD
    participant p12 as get_token_information
    participant p13 as create_string_buffer
    participant p14 as cast
    participant p15 as _windows_sid_string
    p0->>p1: WindowsSecurityGuardError
    p0->>p2: _current_windows_user_sid
    p2-->>p3: WinDLL
    p2-->>p3: WinDLL
    p2-->>p4: POINTER
    p2-->>p4: POINTER
    p2-->>p5: HANDLE
    p2-->>p6: open_process_token
    p2-->>p7: get_current_process
    p2-->>p8: byref
    p2-->>p9: WinError
    p2-->>p10: get_last_error
    p2->>p1: WindowsSecurityGuardError
    p2-->>p11: DWORD
    p2-->>p12: get_token_information
    p2-->>p8: byref
    p2-->>p9: WinError
    p2-->>p10: get_last_error
    p2->>p1: WindowsSecurityGuardError
    p2-->>p13: create_string_buffer
    p2-->>p12: get_token_information
    p2-->>p8: byref
    p2-->>p9: WinError
    p2-->>p10: get_last_error
    p2->>p1: WindowsSecurityGuardError
    p2-->>p14: cast
    p2-->>p4: POINTER
    p2->>p15: _windows_sid_string
    p15-->>p3: WinDLL
    p15-->>p3: WinDLL
```

> Call sequence diagram shows 30 of 45 interactions; 15 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. windows_current_user_sid"]
    s2["2. WindowsSecurityGuardError"]
    s3["3. _current_windows_user_sid"]
    s4["4. WinDLL"]
    s5["5. WinDLL"]
    s6["6. POINTER"]
    s7["7. POINTER"]
    s8["8. HANDLE"]
    s9["9. open_process_token"]
    s10["10. get_current_process"]
    s11["11. byref"]
    s12["12. WinError"]
    s1 -->|"WindowsSecurityGuardError('Windows user SID lookup is unavailable on this platform.')"| s2
    s1 -->|"_current_windows_user_sid(data not statically known)"| s3
    s3 -. "ctypes.WinDLL('advapi32', use_last_error=True)" .-> s4
    s3 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s5
    s3 -. "ctypes.POINTER(wintypes.HANDLE)" .-> s6
    s3 -. "ctypes.POINTER(wintypes.DWORD)" .-> s7
    s3 -. "wintypes.HANDLE(data not statically known)" .-> s8
    s3 -. "open_process_token(get_current_process(...), 8, ctypes.byref(...))" .-> s9
    s3 -. "get_current_process(data not statically known)" .-> s10
    s3 -. "ctypes.byref(token)" .-> s11
    s3 -. "ctypes.WinError(ctypes.get_last_error(...))" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `windows_current_user_sid` | - | `os` | - | `_current_windows_user_sid(...)` |
| `WindowsSecurityGuardError` | - | - | - | - |
| `_current_windows_user_sid` | - | `ctypes` | `open_process_token.argtypes`, `open_process_token.restype`, `get_token_information.argtypes`, `get_token_information.restype`, `get_current_process.argtypes`, `get_current_process.restype` | `_windows_sid_string(...)` |
| `WinDLL` | - | - | - | - |
| `WinDLL` | - | - | - | - |
| `POINTER` | - | - | - | - |
| `POINTER` | - | - | - | - |
| `HANDLE` | - | - | - | - |
| `open_process_token` | - | - | - | - |
| `get_current_process` | - | - | - | - |
| `byref` | - | - | - | - |
| `WinError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| windows_current_user_sid | WindowsSecurityGuardError | 742 | `WindowsSecurityGuardError('Windows user SID lookup is unavailable on this platform.')` |
| windows_current_user_sid | _current_windows_user_sid | 745 | `_current_windows_user_sid(data not statically known)` |
| _current_windows_user_sid | WinDLL | 992 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _current_windows_user_sid | WinDLL | 993 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _current_windows_user_sid | POINTER | 998 | `ctypes.POINTER(wintypes.HANDLE)` |
| _current_windows_user_sid | POINTER | 1007 | `ctypes.POINTER(wintypes.DWORD)` |
| _current_windows_user_sid | HANDLE | 1014 | `wintypes.HANDLE(data not statically known)` |
| _current_windows_user_sid | open_process_token | 1015 | `open_process_token(get_current_process(...), 8, ctypes.byref(...))` |
| _current_windows_user_sid | get_current_process | 1016 | `get_current_process(data not statically known)` |
| _current_windows_user_sid | byref | 1018 | `ctypes.byref(token)` |
| _current_windows_user_sid | WinError | 1020 | `ctypes.WinError(ctypes.get_last_error(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 992 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 993 |
| external_call | `_current_windows_user_sid` | `ctypes.POINTER` | 998 |
| external_call | `_current_windows_user_sid` | `ctypes.POINTER` | 1007 |
| external_call | `_current_windows_user_sid` | `wintypes.HANDLE` | 1014 |
| unresolved_call | `_current_windows_user_sid` | `open_process_token` | 1015 |
| unresolved_call | `_current_windows_user_sid` | `get_current_process` | 1016 |
| external_call | `_current_windows_user_sid` | `ctypes.byref` | 1018 |
| external_call | `_current_windows_user_sid` | `ctypes.WinError` | 1020 |
| step_limit | `windows_current_user_sid` | `first 12 steps` | 0 |

## Behavior

This flow starts at `windows_current_user_sid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
