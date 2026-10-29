# open_windows_guarded_lock_file

**Entry point:** `open_windows_guarded_lock_file` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as open_windows_guarded_lock_file
    participant p1 as _private_windows_security_attributes
    participant p2 as _assert_windows_regular_file_handle
    participant p3 as _verify_windows_handle_restrictive_dacl
    participant p4 as WindowsFileGuardError
    participant p5 as _windows_api_path
    participant p6 as _close_windows_handle
    participant p7 as _windows_handle_information
    participant p8 as _current_windows_user_sid
    participant p9 as _windows_sid_string
    participant p10 as WindowsSecurityGuardError
    participant p11 as ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file)
    participant p12 as create_file
    participant p13 as ctypes.set_last_error
    participant p14 as Path
    participant p15 as ctypes.byref (src/llm_wiki_cli/services…windows_guarded_lock_file)
    participant p16 as ctypes.get_last_error (src/llm_wiki_cli/services…windows_guarded_lock_file)
    participant p17 as wintypes.HANDLE (src/llm_wiki_cli/services…windows_guarded_lock_file)
    participant p18 as ctypes.WinError (src/llm_wiki_cli/services…windows_guarded_lock_file)
    participant p19 as int (src/llm_wiki_cli/services…windows_guarded_lock_file)
    participant p20 as str
    participant p21 as msvcrt.open_osfhandle
    participant p22 as getattr
    participant p23 as ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)
    participant p24 as os.path.abspath
    participant p25 as ctypes.WinDLL (src/llm_wiki_cli/services…s_handle_restrictive_dacl)
    participant p26 as os.fspath
    participant p27 as int (src/llm_wiki_cli/services…ndows_regular_file_handle)
    p0->>p1: _private_windows_security_attributes
    p0->>p2: _assert_windows_regular_file_handle
    p0->>p3: _verify_windows_handle_restrictive_dacl
    p0->>p4: WindowsFileGuardError
    p0->>p5: _windows_api_path
    p0->>p6: _close_windows_handle
    p2->>p7: _windows_handle_information
    p1->>p8: _current_windows_user_sid
    p8->>p9: _windows_sid_string
    p1->>p10: WindowsSecurityGuardError
    p0-->>p11: ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file)('kernel32', use_last_error=True)
    p0-->>p12: create_file(_windows_api_path(...), ..., ..., ctypes.byref(...), 4, ..., None)
    p0-->>p13: ctypes.set_last_error(0)
    p0-->>p14: Path(path)
    p0-->>p15: ctypes.byref (src/llm_wiki_cli/services…windows_guarded_lock_file)(security)
    p0-->>p16: ctypes.get_last_error (src/llm_wiki_cli/services…windows_guarded_lock_file)
    p0-->>p17: wintypes.HANDLE (src/llm_wiki_cli/services…windows_guarded_lock_file)(...)
    p0-->>p18: ctypes.WinError (src/llm_wiki_cli/services…windows_guarded_lock_file)(last_error)
    p0-->>p19: int (src/llm_wiki_cli/services…windows_guarded_lock_file)(handle)
    p0-->>p14: Path(path)
    p0-->>p20: str(path)
    p0-->>p21: msvcrt.open_osfhandle(native_handle, ...)
    p0-->>p22: getattr(os, 'O_BINARY', 0)
    p0-->>p22: getattr(os, 'O_NOINHERIT', 0)
    p1-->>p23: ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('advapi32', use_last_error=True)
    p5-->>p24: os.path.abspath(os.fspath(...))
    p3-->>p25: ctypes.WinDLL (src/llm_wiki_cli/services…s_handle_restrictive_dacl)('advapi32', use_last_error=True)
    p1-->>p23: ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('kernel32', use_last_error=True)
    p5-->>p26: os.fspath(path)
    p2-->>p27: int (src/llm_wiki_cli/services…ndows_regular_file_handle)(information.dwFileAttributes)
```

> Call sequence diagram shows 30 of 169 interactions; 139 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 112 (93 omitted); unresolved 1 of 21 (20 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:_private_windows_security_attributes` | 4 | - | external | 7 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 9 | - | external | 19 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 9 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 9 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_sid_string` | 35 | - | external | 8 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_sid_string` | 35 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_sid_string` | 35 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_close_windows_handle` | 48 | - | external | 2 |
> Omission summary shows 8 of 20 groups; 12 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 37; effect analysis evaluated: 13, partial: 0, unavailable: 24. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `open_windows_guarded_lock_file` | `available` | `evaluated` | `available` |
| `WindowsFileGuardError` | `unavailable` | `unavailable` | `unavailable` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_private_windows_security_attributes` | `available` | `evaluated` | `available` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_current_windows_user_sid` | `available` | `evaluated` | `available` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. open_windows_guarded_lock_file"]
    s2["2. WindowsFileGuardError"]
    s3["3. ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file)"]
    s4["4. _private_windows_security_attributes"]
    s5["5. ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s6["6. ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s7["7. ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s8["8. ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s9["9. _current_windows_user_sid"]
    s10["10. ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)"]
    s11["11. ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)"]
    s12["12. ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)"]
    s1 -->|"WindowsFileGuardError('Guarded Windows lock files are unavailable on this platform.')"| s2
    s1 -. "ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file)('kernel32', use_last_error=True)" .-> s3
    s1 -->|"_private_windows_security_attributes(directory=False)"| s4
    s4 -. "ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('advapi32', use_last_error=True)" .-> s5
    s4 -. "ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('kernel32', use_last_error=True)" .-> s6
    s4 -. "ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)(wintypes.LPVOID)" .-> s7
    s4 -. "ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)(wintypes.DWORD)" .-> s8
    s4 -->|"_current_windows_user_sid(data not statically known)"| s9
    s9 -. "ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)('advapi32', use_last_error=True)" .-> s10
    s9 -. "ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)('kernel32', use_last_error=True)" .-> s11
    s9 -. "ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)(wintypes.HANDLE)" .-> s12
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
| `ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file)` | - | - | - | - |
| `_private_windows_security_attributes` | `directory: bool` | - | `convert.argtypes`, `convert.restype`, `local_free.argtypes`, `local_free.restype` | - |
| `ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `_current_windows_user_sid` | - | `ctypes` | `open_process_token.argtypes`, `open_process_token.restype`, `get_token_information.argtypes`, `get_token_information.restype`, `get_current_process.argtypes`, `get_current_process.restype` | `_windows_sid_string(...)` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)` | - | - | - | - |
| `ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)` | - | - | - | - |
| `ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| open_windows_guarded_lock_file | WindowsFileGuardError | 625 | `WindowsFileGuardError('Guarded Windows lock files are unavailable on this platform.')` |
| open_windows_guarded_lock_file | ctypes.WinDLL (src/llm_wiki_cli/services…windows_guarded_lock_file) | 630 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| open_windows_guarded_lock_file | _private_windows_security_attributes | 644 | `_private_windows_security_attributes(directory=False)` |
| _private_windows_security_attributes | ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes) | 955 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _private_windows_security_attributes | ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes) | 956 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _private_windows_security_attributes | ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes) | 961 | `ctypes.POINTER(wintypes.LPVOID)` |
| _private_windows_security_attributes | ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes) | 962 | `ctypes.POINTER(wintypes.DWORD)` |
| _private_windows_security_attributes | _current_windows_user_sid | 976 | `_current_windows_user_sid(data not statically known)` |
| _current_windows_user_sid | ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid) | 1004 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _current_windows_user_sid | ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid) | 1005 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _current_windows_user_sid | ctypes.POINTER (src/llm_wiki_cli/services…_current_windows_user_sid) | 1010 | `ctypes.POINTER(wintypes.HANDLE)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `open_windows_guarded_lock_file` | `ctypes.WinDLL` | 630 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 955 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 956 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 961 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 962 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 1004 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 1005 |
| external_call | `_current_windows_user_sid` | `ctypes.POINTER` | 1010 |
| step_limit | `open_windows_guarded_lock_file` | `first 12 steps` | 0 |

## Behavior

This flow starts at `open_windows_guarded_lock_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
