# open_windows_readonly_file

**Entry point:** `open_windows_readonly_file` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as open_windows_readonly_file
    participant p1 as _open_windows_readonly_file_handle
    participant p2 as windows_object_identity
    participant p3 as WindowsFileGuardError
    participant p4 as _close_windows_handle
    participant p5 as windows_object_identity_from_values
    participant p6 as _verify_windows_handle_restrictive_dacl
    participant p7 as _current_windows_user_sid
    participant p8 as _windows_sid_string
    participant p9 as _windows_api_path
    participant p10 as WindowsIdentityUnavailableError
    participant p11 as WindowsObjectIdentity
    participant p12 as WindowsSecurityGuardError
    participant p13 as Path
    participant p14 as stream.fileno
    participant p15 as msvcrt.open_osfhandle
    participant p16 as getattr (src/llm_wiki_cli/services…pen_windows_readonly_file)
    participant p17 as os.fdopen
    participant p18 as os.fstat
    participant p19 as str (src/llm_wiki_cli/services…pen_windows_readonly_file)
    participant p20 as stream.close
    participant p21 as os.close
    participant p22 as ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle)
    participant p23 as create_file
    participant p24 as int (src/llm_wiki_cli/services…y:windows_object_identity)
    participant p25 as getattr (src/llm_wiki_cli/services…y:windows_object_identity)
    participant p26 as wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle)
    p0->>p1: _open_windows_readonly_file_handle
    p0->>p2: windows_object_identity
    p0->>p3: WindowsFileGuardError
    p0->>p4: _close_windows_handle
    p2->>p5: windows_object_identity_from_values
    p1->>p6: _verify_windows_handle_restrictive_dacl
    p6->>p7: _current_windows_user_sid
    p7->>p8: _windows_sid_string
    p1->>p9: _windows_api_path
    p5->>p10: WindowsIdentityUnavailableError
    p5->>p11: WindowsObjectIdentity
    p6->>p12: WindowsSecurityGuardError
    p0-->>p13: Path(path)
    p0-->>p14: stream.fileno
    p0-->>p13: Path(path)
    p0-->>p13: Path(path)
    p0-->>p15: msvcrt.open_osfhandle(native_handle, ...)
    p0-->>p16: getattr (src/llm_wiki_cli/services…pen_windows_readonly_file)(os, 'O_BINARY', 0)
    p0-->>p16: getattr (src/llm_wiki_cli/services…pen_windows_readonly_file)(os, 'O_NOINHERIT', 0)
    p0-->>p17: os.fdopen(descriptor, 'rb')
    p0-->>p18: os.fstat(stream.fileno(...))
    p0-->>p19: str (src/llm_wiki_cli/services…pen_windows_readonly_file)(path)
    p0-->>p19: str (src/llm_wiki_cli/services…pen_windows_readonly_file)(exc)
    p0-->>p20: stream.close
    p0-->>p21: os.close(descriptor)
    p1-->>p22: ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle)('kernel32', use_last_error=True)
    p1-->>p23: create_file(_windows_api_path(...), ..., 1, None, 3, ..., None)
    p2-->>p24: int (src/llm_wiki_cli/services…y:windows_object_identity)(getattr(...))
    p2-->>p25: getattr (src/llm_wiki_cli/services…y:windows_object_identity)(result, 'st_dev', 0)
    p1-->>p26: wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle)(...)
```

> Call sequence diagram shows 30 of 170 interactions; 140 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 109 (94 omitted); unresolved 3 of 20 (17 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 6 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_readonly_file_handle` | 3 | - | external | 10 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_readonly_file_handle` | 3 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 6 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_readonly_file_handle` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_verify_windows_handle_restrictive_dacl` | 29 | - | external | 50 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_verify_windows_handle_restrictive_dacl` | 29 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 53 | - | external | 19 |
> Omission summary shows 8 of 19 groups; 11 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 42; effect analysis evaluated: 14, partial: 1, unavailable: 27. Counts include steps omitted from the displayed trace.

Collector observations for 15 source steps with known totals: observed: 104, emitted: 102, omitted: 2. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `open_windows_readonly_file` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `WindowsFileGuardError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_open_windows_readonly_file_handle` | `available` | `evaluated` | `available` | `10` | `10` | `0` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `create_file` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_windows_api_path` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `os.path.abspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.fspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.startswith` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `value.startswith` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ctypes.WinError (src/llm_wiki_cli/services…dows_readonly_file_handle)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. open_windows_readonly_file"]
    s2["2. WindowsFileGuardError"]
    s3["3. _open_windows_readonly_file_handle"]
    s4["4. ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle)"]
    s5["5. create_file"]
    s6["6. _windows_api_path"]
    s7["7. os.path.abspath"]
    s8["8. os.fspath"]
    s9["9. value.startswith"]
    s10["10. value.startswith"]
    s11["11. wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle)"]
    s12["12. ctypes.WinError (src/llm_wiki_cli/services…dows_readonly_file_handle)"]
    s1 -->|"WindowsFileGuardError('Windows read-only file guards are unavailable on this platform.')"| s2
    s1 -->|"_open_windows_readonly_file_handle(Path(...), require_restrictive_dacl=True, require_single_link=require_single_link)"| s3
    s3 -. "ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle)('kernel32', use_last_error=True)" .-> s4
    s3 -. "create_file(_windows_api_path(...), ..., 1, None, 3, ..., None)" .-> s5
    s3 -->|"_windows_api_path(path)"| s6
    s6 -. "os.path.abspath(os.fspath(...))" .-> s7
    s6 -. "os.fspath(path)" .-> s8
    s6 -. "value.startswith('\\\\?\\')" .-> s9
    s6 -. "value.startswith('\\\\')" .-> s10
    s3 -. "wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle)(...)" .-> s11
    s3 -. "ctypes.WinError (src/llm_wiki_cli/services…dows_readonly_file_handle)(ctypes.get_last_error(...))" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `open_windows_readonly_file` | `path: Path`, `require_restrictive_dacl: bool`, `require_single_link: bool` | `os`, `os`, `os`, `os`, `WindowsIdentityUnavailableError`, `WindowsFileGuardError` | - | - |
| `WindowsFileGuardError` | - | - | - | - |
| `_open_windows_readonly_file_handle` | `path: Path`, `require_restrictive_dacl: bool`, `require_single_link: bool` | - | `create_file.argtypes`, `create_file.restype`, `get_file_type.argtypes`, `get_file_type.restype`, `get_information.argtypes`, `get_information.restype` | `native_handle` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle)` | - | - | - | - |
| `create_file` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |
| `os.path.abspath` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `value.startswith` | - | - | - | - |
| `value.startswith` | - | - | - | - |
| `wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle)` | - | - | - | - |
| `ctypes.WinError (src/llm_wiki_cli/services…dows_readonly_file_handle)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| open_windows_readonly_file | WindowsFileGuardError | 339 | `WindowsFileGuardError('Windows read-only file guards are unavailable on this platform.')` |
| open_windows_readonly_file | _open_windows_readonly_file_handle | 344 | `_open_windows_readonly_file_handle(Path(...), require_restrictive_dacl=True, require_single_link=require_single_link)` |
| _open_windows_readonly_file_handle | ctypes.WinDLL (src/llm_wiki_cli/services…dows_readonly_file_handle) | 419 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| _open_windows_readonly_file_handle | create_file | 434 | `create_file(_windows_api_path(...), ..., 1, None, 3, ..., None)` |
| _open_windows_readonly_file_handle | _windows_api_path | 435 | `_windows_api_path(path)` |
| _windows_api_path | os.path.abspath | 1310 | `os.path.abspath(os.fspath(...))` |
| _windows_api_path | os.fspath | 1310 | `os.fspath(path)` |
| _windows_api_path | value.startswith | 1311 | `value.startswith('\\\\?\\')` |
| _windows_api_path | value.startswith | 1313 | `value.startswith('\\\\')` |
| _open_windows_readonly_file_handle | wintypes.HANDLE (src/llm_wiki_cli/services…dows_readonly_file_handle) | 443 | `wintypes.HANDLE(...)` |
| _open_windows_readonly_file_handle | ctypes.WinError (src/llm_wiki_cli/services…dows_readonly_file_handle) | 445 | `ctypes.WinError(ctypes.get_last_error(...))` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_open_windows_readonly_file_handle` | `ctypes.WinDLL` | 419 |
| unresolved_call | `_open_windows_readonly_file_handle` | `create_file` | 434 |
| external_call | `_windows_api_path` | `os.path.abspath` | 1310 |
| external_call | `_windows_api_path` | `os.fspath` | 1310 |
| unresolved_call | `_windows_api_path` | `value.startswith` | 1311 |
| unresolved_call | `_windows_api_path` | `value.startswith` | 1313 |
| external_call | `_open_windows_readonly_file_handle` | `wintypes.HANDLE` | 443 |
| external_call | `_open_windows_readonly_file_handle` | `ctypes.WinError` | 445 |
| step_limit | `open_windows_readonly_file` | `first 12 steps` | 0 |

## Behavior

This flow starts at `open_windows_readonly_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
