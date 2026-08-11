# hash_file

**Entry point:** `hash_file` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_file
    participant p1 as _hash_file
    participant p2 as Path
    participant p3 as abspath
    participant p4 as fspath
    participant p5 as guard_windows_directory_chain
    participant p6 as WindowsDirectoryGuardError
    participant p7 as append
    participant p8 as _open_windows_directory_guard
    participant p9 as WinDLL
    participant p10 as create_file
    participant p11 as _windows_api_path
    participant p12 as startswith
    participant p13 as HANDLE
    participant p14 as get_last_error
    participant p15 as WinError
    participant p16 as _WindowsDirectoryGuardUnavailableError
    participant p17 as _ByHandleFileInformation
    participant p18 as get_information
    participant p19 as byref
    p0->>p1: _hash_file
    p1-->>p2: Path
    p1-->>p3: abspath
    p1-->>p4: fspath
    p1->>p5: guard_windows_directory_chain
    p5->>p6: WindowsDirectoryGuardError
    p5-->>p2: Path
    p5-->>p3: abspath
    p5-->>p4: fspath
    p5->>p6: WindowsDirectoryGuardError
    p5-->>p2: Path
    p5-->>p7: append
    p5->>p8: _open_windows_directory_guard
    p8-->>p9: WinDLL
    p8-->>p10: create_file
    p8->>p11: _windows_api_path
    p11-->>p3: abspath
    p11-->>p4: fspath
    p11-->>p12: startswith
    p11-->>p12: startswith
    p8-->>p13: HANDLE
    p8-->>p14: get_last_error
    p8-->>p15: WinError
    p8->>p16: _WindowsDirectoryGuardUnavailableError
    p8->>p6: WindowsDirectoryGuardError
    p8-->>p17: _ByHandleFileInformation
    p8-->>p18: get_information
    p8-->>p19: byref
    p8-->>p15: WinError
    p8-->>p14: get_last_error
```

> Call sequence diagram shows 30 of 356 interactions; 326 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_file"]
    s2["2. _hash_file"]
    s3["3. Path"]
    s4["4. abspath"]
    s5["5. fspath"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path"]
    s9["9. abspath"]
    s10["10. fspath"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path"]
    s1 -->|"_hash_file(Path(...))"| s2
    s2 -. "Path(os.path.abspath(...))" .-> s3
    s2 -. "os.path.abspath(os.fspath(...))" .-> s4
    s2 -. "os.fspath(path)" .-> s5
    s2 -->|"guard_windows_directory_chain(absolute_path.parent, (...))"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath(os.fspath(...))" .-> s9
    s6 -. "os.fspath(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path(root_path.anchor)" .-> s12
    b0["mutation digest.update"]
    s2 -. "mutation digest.update" .-> b0
    b1["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b2
    b3["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b3
    click s1 "../modules/documentation_policy.md"
    click s2 "../modules/documentation_policy.md"
    click s6 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_file` | `path: str \| Path` | - | - | `_hash_file(...)` |
| `_hash_file` | `path: Path`, `inspected: os.stat_result \| None`, `max_bytes: int \| None` | `os`, `WindowsDirectoryGuardError`, `os`, `os`, `os`, `os` | - | `_hash_windows_file(...)`, `...` |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_file | _hash_file | 524 | `_hash_file(Path(...))` |
| _hash_file | Path | 626 | `Path(os.path.abspath(...))` |
| _hash_file | abspath | 626 | `os.path.abspath(os.fspath(...))` |
| _hash_file | fspath | 626 | `os.fspath(path)` |
| _hash_file | guard_windows_directory_chain | 628 | `guard_windows_directory_chain(absolute_path.parent, (...))` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | abspath | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | fspath | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path | 179 | `Path(root_path.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `digest.update` | `_hash_file` | 677 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_hash_file` | `os.path.abspath` | 626 |
| external_call | `_hash_file` | `os.fspath` | 626 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `hash_file` | `first 12 steps` | 0 |
| truncated_flow | `hash_file` | `depth limit` | 0 |

## Behavior

This flow starts at `hash_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
