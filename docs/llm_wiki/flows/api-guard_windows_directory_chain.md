# guard_windows_directory_chain

**Entry point:** `guard_windows_directory_chain` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as guard_windows_directory_chain
    participant p1 as _open_windows_directory_guard
    participant p2 as create_private_windows_directory
    participant p3 as WindowsDirectoryGuardError
    participant p4 as _close_windows_handle
    participant p5 as _private_windows_security_attributes
    participant p6 as move_windows_path_write_through
    participant p7 as _verify_windows_handle_restrictive_dacl
    participant p8 as _current_windows_user_sid
    participant p9 as _windows_sid_string
    participant p10 as _windows_api_path
    participant p11 as _WindowsDirectoryGuardUnavailableError
    participant p12 as WindowsDurabilityError
    participant p13 as WindowsSecurityGuardError
    participant p14 as Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p15 as handles.append
    participant p16 as os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p17 as os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p18 as enumerate
    participant p19 as len
    participant p20 as os.path.lexists
    participant p21 as current.mkdir
    participant p22 as reversed
    participant p23 as ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p24 as create_file
    participant p25 as ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)
    participant p26 as Path (src/llm_wiki_cli/services…private_windows_directory)
    p0->>p1: _open_windows_directory_guard
    p0->>p2: create_private_windows_directory
    p0->>p3: WindowsDirectoryGuardError
    p0->>p4: _close_windows_handle
    p2->>p5: _private_windows_security_attributes
    p2->>p6: move_windows_path_write_through
    p1->>p7: _verify_windows_handle_restrictive_dacl
    p7->>p8: _current_windows_user_sid
    p8->>p9: _windows_sid_string
    p1->>p10: _windows_api_path
    p1->>p11: _WindowsDirectoryGuardUnavailableError
    p6->>p12: WindowsDurabilityError
    p5->>p13: WindowsSecurityGuardError
    p0-->>p14: Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))
    p0-->>p15: handles.append(_open_windows_directory_guard(...))
    p0-->>p16: os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))
    p0-->>p17: os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)
    p0-->>p14: Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)
    p0-->>p18: enumerate(root_components)
    p0-->>p15: handles.append(_open_windows_directory_guard(...))
    p0-->>p19: len(root_components)
    p0-->>p14: Path (src/llm_wiki_cli/services…d_windows_directory_chain)(component)
    p0-->>p20: os.path.lexists(current)
    p0-->>p21: current.mkdir(exist_ok=True)
    p0-->>p15: handles.append(_open_windows_directory_guard(...))
    p0-->>p22: reversed(handles)
    p1-->>p23: ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)('kernel32', use_last_error=True)
    p1-->>p24: create_file(_windows_api_path(...), desired_access, ..., None, _OPEN_EXISTING, ..., None)
    p2-->>p25: ctypes.WinDLL (src/llm_wiki_cli/services…private_windows_directory)('kernel32', use_last_error=True)
    p2-->>p26: Path (src/llm_wiki_cli/services…private_windows_directory)(path)
```

> Call sequence diagram shows 30 of 212 interactions; 182 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 128 (116 omitted); unresolved 5 of 27 (22 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 1 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 5 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 12 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 12 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 9 | - | external | 13 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 9 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 6 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 9 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_close_windows_handle` | 27 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_close_windows_handle` | 27 | - | unresolved | 1 |
> Omission summary shows 8 of 26 groups; 18 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 58; effect analysis evaluated: 21, partial: 6, unavailable: 31. Counts include steps omitted from the displayed trace.

Collector observations for 27 source steps with known totals: observed: 208, emitted: 201, omitted: 7. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `guard_windows_directory_chain` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `WindowsDirectoryGuardError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `WindowsDirectoryGuardError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `handles.append` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_open_windows_directory_guard` | `available` | `partial` | `available` | `16` | `15` | `1` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `create_file` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_windows_api_path` | `available` | `evaluated` | `available` | `4` | `4` | `0` |

```mermaid
flowchart LR
    s1["1. guard_windows_directory_chain"]
    s2["2. WindowsDirectoryGuardError"]
    s3["3. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s4["4. os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s5["5. os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s6["6. WindowsDirectoryGuardError"]
    s7["7. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s8["8. handles.append"]
    s9["9. _open_windows_directory_guard"]
    s10["10. ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)"]
    s11["11. create_file"]
    s12["12. _windows_api_path"]
    s1 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s2
    s1 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))" .-> s3
    s1 -. "os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))" .-> s4
    s1 -. "os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)" .-> s5
    s1 -->|"WindowsDirectoryGuardError(...)"| s6
    s1 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)" .-> s7
    s1 -. "handles.append(_open_windows_directory_guard(...))" .-> s8
    s1 -->|"_open_windows_directory_guard(current)"| s9
    s9 -. "ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)('kernel32', use_last_error=True)" .-> s10
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
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `handles.append` | - | - | - | - |
| `_open_windows_directory_guard` | `path: Path`, `require_restrictive_dacl: bool` | `_FILE_LIST_DIRECTORY`, `_FILE_READ_ATTRIBUTES`, `_READ_CONTROL`, `_FILE_SHARE_READ`, `_FILE_SHARE_WRITE`, `_OPEN_EXISTING`, `_FILE_FLAG_BACKUP_SEMANTICS`, `_FILE_FLAG_OPEN_REPARSE_POINT` | `create_file.argtypes`, `create_file.restype`, `get_information.argtypes`, `get_information.restype` | `int(...)` |
| `ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)` | - | - | - | - |
| `create_file` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 179 | `Path(root_path.anchor)` |
| guard_windows_directory_chain | handles.append | 182 | `handles.append(_open_windows_directory_guard(...))` |
| guard_windows_directory_chain | _open_windows_directory_guard | 182 | `_open_windows_directory_guard(current)` |
| _open_windows_directory_guard | ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard) | 235 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
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
