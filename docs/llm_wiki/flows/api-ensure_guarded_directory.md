# ensure_guarded_directory

**Entry point:** `ensure_guarded_directory` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as ensure_guarded_directory
    participant p1 as guard_windows_directory_chain
    participant p2 as _open_windows_directory_guard
    participant p3 as create_private_windows_directory
    participant p4 as _private_windows_security_attributes
    participant p5 as move_windows_path_write_through
    participant p6 as _verify_windows_handle_restrictive_dacl
    participant p7 as _current_windows_user_sid
    participant p8 as _windows_sid_string
    participant p9 as WindowsDirectoryGuardError
    participant p10 as _close_windows_handle
    participant p11 as _windows_api_path
    participant p12 as _WindowsDirectoryGuardUnavailableError
    participant p13 as WindowsDurabilityError
    participant p14 as WindowsSecurityGuardError
    participant p15 as Path (src/llm_wiki_cli/services…:ensure_guarded_directory)
    participant p16 as target.is_absolute
    participant p17 as OSError
    participant p18 as getattr
    participant p19 as os.open
    participant p20 as os.mkdir
    participant p21 as os.close
    p0->>p1: guard_windows_directory_chain
    p1->>p2: _open_windows_directory_guard
    p1->>p3: create_private_windows_directory
    p3->>p4: _private_windows_security_attributes
    p3->>p5: move_windows_path_write_through
    p2->>p6: _verify_windows_handle_restrictive_dacl
    p6->>p7: _current_windows_user_sid
    p7->>p8: _windows_sid_string
    p1->>p9: WindowsDirectoryGuardError
    p1->>p10: _close_windows_handle
    p2->>p11: _windows_api_path
    p2->>p12: _WindowsDirectoryGuardUnavailableError
    p5->>p13: WindowsDurabilityError
    p4->>p14: WindowsSecurityGuardError
    p0-->>p15: Path (src/llm_wiki_cli/services…:ensure_guarded_directory)(path)
    p0-->>p16: target.is_absolute
    p0-->>p17: OSError(...)
    p0-->>p15: Path (src/llm_wiki_cli/services…:ensure_guarded_directory)(target.anchor)
    p0-->>p15: Path (src/llm_wiki_cli/services…:ensure_guarded_directory)(target.anchor)
    p0-->>p18: getattr(os, 'O_NOFOLLOW', None)
    p0-->>p18: getattr(os, 'O_DIRECTORY', None)
    p0-->>p17: OSError('This POSIX platform cannot create guarded directories.')
    p0-->>p18: getattr(os, 'O_CLOEXEC', 0)
    p0-->>p19: os.open(target.anchor, flags)
    p0-->>p15: Path (src/llm_wiki_cli/services…:ensure_guarded_directory)(component)
    p0-->>p17: OSError(...)
    p0-->>p19: os.open(component, flags, dir_fd=descriptor)
    p0-->>p20: os.mkdir(component, mode, dir_fd=descriptor)
    p0-->>p19: os.open(component, flags, dir_fd=descriptor)
    p0-->>p21: os.close(descriptor)
```

> Call sequence diagram shows 30 of 230 interactions; 200 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 144 (129 omitted); unresolved 1 of 28 (27 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | - | external | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 5 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 6 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 17 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 17 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 14 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 6 |
> Omission summary shows 8 of 29 groups; 21 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. ensure_guarded_directory"]
    s2["2. Path (src/llm_wiki_cli/services…:ensure_guarded_directory)"]
    s3["3. target.is_absolute"]
    s4["4. OSError"]
    s5["5. Path (src/llm_wiki_cli/services…:ensure_guarded_directory)"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s9["9. os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s10["10. os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s1 -. "Path (src/llm_wiki_cli/services…:ensure_guarded_directory)(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError(...)" .-> s4
    s1 -. "Path (src/llm_wiki_cli/services…:ensure_guarded_directory)(target.anchor)" .-> s5
    s1 -->|"guard_windows_directory_chain(Path(...), ..., create_missing=True)"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))" .-> s9
    s6 -. "os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)" .-> s12
    b0["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b0
    b1["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b2
    click s1 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `ensure_guarded_directory` | `path: Path`, `mode: int` | `os`, `os`, `os`, `os` | - | `target`, `target`, `target` |
| `Path (src/llm_wiki_cli/services…:ensure_guarded_directory)` | - | - | - | - |
| `target.is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…:ensure_guarded_directory)` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| ensure_guarded_directory | Path (src/llm_wiki_cli/services…:ensure_guarded_directory) | 1647 | `Path(path)` |
| ensure_guarded_directory | target.is_absolute | 1648 | `target.is_absolute(data not statically known)` |
| ensure_guarded_directory | OSError | 1649 | `OSError(...)` |
| ensure_guarded_directory | Path (src/llm_wiki_cli/services…:ensure_guarded_directory) | 1650 | `Path(target.anchor)` |
| ensure_guarded_directory | guard_windows_directory_chain | 1653 | `guard_windows_directory_chain(Path(...), ..., create_missing=True)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 179 | `Path(root_path.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `ensure_guarded_directory` | `target.is_absolute` | 1648 |
| external_call | `ensure_guarded_directory` | `OSError` | 1649 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `ensure_guarded_directory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `ensure_guarded_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
