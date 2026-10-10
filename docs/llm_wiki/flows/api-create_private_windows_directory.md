# create_private_windows_directory

**Entry point:** `create_private_windows_directory` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as create_private_windows_directory
    participant p1 as WindowsDirectoryGuardError
    participant p2 as ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)
    participant p3 as Path (src/llm_wiki_cli/services…private_windows_directory)
    participant p4 as uuid.uuid4
    participant p5 as _private_windows_security_attributes
    participant p6 as create_directory
    participant p7 as _windows_api_path
    participant p8 as ctypes.byref (src/llm_wiki_cli/services…private_windows_directory)
    participant p9 as ctypes.WinError (src/llm_wiki_cli/services…private_windows_directory)
    participant p10 as ctypes.get_last_error (src/llm_wiki_cli/services…private_windows_directory)
    participant p11 as _open_windows_directory_guard
    participant p12 as _close_windows_handle
    participant p13 as move_windows_path_write_through
    participant p14 as remove_directory
    participant p15 as ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)
    participant p16 as os.path.abspath
    participant p17 as ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p18 as WindowsDurabilityError
    participant p19 as os.fspath
    participant p20 as create_file
    participant p21 as ctypes.WinDLL (src/llm_wiki_cli/services…indows_path_write_through)
    participant p22 as ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)
    p0->>p1: WindowsDirectoryGuardError
    p0-->>p2: ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)('kernel32', use_last_error=True)
    p0-->>p3: Path (src/llm_wiki_cli/services…private_windows_directory)(path)
    p0-->>p4: uuid.uuid4
    p0->>p5: _private_windows_security_attributes
    p0-->>p6: create_directory(_windows_api_path(...), ctypes.byref(...))
    p0->>p7: _windows_api_path
    p0-->>p8: ctypes.byref (src/llm_wiki_cli/services…private_windows_directory)(security)
    p0-->>p9: ctypes.WinError (src/llm_wiki_cli/services…private_windows_directory)(ctypes.get_last_error(...))
    p0-->>p10: ctypes.get_last_error (src/llm_wiki_cli/services…private_windows_directory)
    p0->>p1: WindowsDirectoryGuardError
    p0->>p11: _open_windows_directory_guard
    p0->>p12: _close_windows_handle
    p0->>p13: move_windows_path_write_through
    p0->>p11: _open_windows_directory_guard
    p0->>p12: _close_windows_handle
    p0-->>p14: remove_directory(_windows_api_path(...))
    p0->>p7: _windows_api_path
    p0-->>p10: ctypes.get_last_error (src/llm_wiki_cli/services…private_windows_directory)
    p0-->>p9: ctypes.WinError (src/llm_wiki_cli/services…private_windows_directory)(error_number)
    p0->>p1: WindowsDirectoryGuardError
    p5-->>p15: ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('advapi32', use_last_error=True)
    p7-->>p16: os.path.abspath(os.fspath(...))
    p11-->>p17: ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)('kernel32', use_last_error=True)
    p13->>p18: WindowsDurabilityError
    p5-->>p15: ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('kernel32', use_last_error=True)
    p7-->>p19: os.fspath(path)
    p11-->>p20: create_file(_windows_api_path(...), desired_access, ..., None, _OPEN_EXISTING, ..., None)
    p13-->>p21: ctypes.WinDLL (src/llm_wiki_cli/services…indows_path_write_through)('kernel32', use_last_error=True)
    p5-->>p22: ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)(wintypes.LPVOID)
```

> Call sequence diagram shows 30 of 190 interactions; 160 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 119 (104 omitted); unresolved 3 of 23 (20 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:_private_windows_security_attributes` | 6 | - | external | 6 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_private_windows_security_attributes` | 6 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 11 | - | external | 19 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 11 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 11 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 5 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_sid_string` | 37 | - | external | 8 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_sid_string` | 37 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_sid_string` | 37 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
> Omission summary shows 8 of 21 groups; 13 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. create_private_windows_directory"]
    s2["2. WindowsDirectoryGuardError"]
    s3["3. ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)"]
    s4["4. Path (src/llm_wiki_cli/services…private_windows_directory)"]
    s5["5. uuid.uuid4"]
    s6["6. _private_windows_security_attributes"]
    s7["7. ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s8["8. ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s9["9. ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s10["10. ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)"]
    s11["11. _current_windows_user_sid"]
    s12["12. ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)"]
    s1 -->|"WindowsDirectoryGuardError('Private Windows directory creation is unavailable on this platform.')"| s2
    s1 -. "ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)('kernel32', use_last_error=True)" .-> s3
    s1 -. "Path (src/llm_wiki_cli/services…private_windows_directory)(path)" .-> s4
    s1 -. "uuid.uuid4(data not statically known)" .-> s5
    s1 -->|"_private_windows_security_attributes(directory=True)"| s6
    s6 -. "ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('advapi32', use_last_error=True)" .-> s7
    s6 -. "ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)('kernel32', use_last_error=True)" .-> s8
    s6 -. "ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)(wintypes.LPVOID)" .-> s9
    s6 -. "ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)(wintypes.DWORD)" .-> s10
    s6 -->|"_current_windows_user_sid(data not statically known)"| s11
    s11 -. "ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)('advapi32', use_last_error=True)" .-> s12
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
| `ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…private_windows_directory)` | - | - | - | - |
| `uuid.uuid4` | - | - | - | - |
| `_private_windows_security_attributes` | `directory: bool` | - | `convert.argtypes`, `convert.restype`, `local_free.argtypes`, `local_free.restype` | - |
| `ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes)` | - | - | - | - |
| `_current_windows_user_sid` | - | `ctypes` | `open_process_token.argtypes`, `open_process_token.restype`, `get_token_information.argtypes`, `get_token_information.restype`, `get_current_process.argtypes`, `get_current_process.restype` | `_windows_sid_string(...)` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| create_private_windows_directory | WindowsDirectoryGuardError | 509 | `WindowsDirectoryGuardError('Private Windows directory creation is unavailable on this platform.')` |
| create_private_windows_directory | ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory) | 514 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| create_private_windows_directory | Path (src/llm_wiki_cli/services…private_windows_directory) | 522 | `Path(path)` |
| create_private_windows_directory | uuid.uuid4 | 523 | `uuid.uuid4(data not statically known)` |
| create_private_windows_directory | _private_windows_security_attributes | 526 | `_private_windows_security_attributes(directory=True)` |
| _private_windows_security_attributes | ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes) | 955 | `ctypes.WinDLL('advapi32', use_last_error=True)` |
| _private_windows_security_attributes | ctypes.WinDLL (src/llm_wiki_cli/services…ndows_security_attributes) | 956 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _private_windows_security_attributes | ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes) | 961 | `ctypes.POINTER(wintypes.LPVOID)` |
| _private_windows_security_attributes | ctypes.POINTER (src/llm_wiki_cli/services…ndows_security_attributes) | 962 | `ctypes.POINTER(wintypes.DWORD)` |
| _private_windows_security_attributes | _current_windows_user_sid | 976 | `_current_windows_user_sid(data not statically known)` |
| _current_windows_user_sid | ctypes.WinDLL (src/llm_wiki_cli/services…_current_windows_user_sid) | 1004 | `ctypes.WinDLL('advapi32', use_last_error=True)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `create_private_windows_directory` | `ctypes.WinDLL` | 514 |
| external_call | `create_private_windows_directory` | `uuid.uuid4` | 523 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 955 |
| external_call | `_private_windows_security_attributes` | `ctypes.WinDLL` | 956 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 961 |
| external_call | `_private_windows_security_attributes` | `ctypes.POINTER` | 962 |
| external_call | `_current_windows_user_sid` | `ctypes.WinDLL` | 1004 |
| step_limit | `create_private_windows_directory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `create_private_windows_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
