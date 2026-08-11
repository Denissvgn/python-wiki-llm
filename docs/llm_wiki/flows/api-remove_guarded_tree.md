# remove_guarded_tree

**Entry point:** `remove_guarded_tree` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as remove_guarded_tree
    participant p1 as Path
    participant p2 as is_absolute
    participant p3 as OSError
    participant p4 as uuid4
    participant p5 as guard_windows_directory_chain
    participant p6 as WindowsDirectoryGuardError
    participant p7 as abspath
    participant p8 as fspath
    participant p9 as append
    participant p10 as _open_windows_directory_guard
    participant p11 as WinDLL
    participant p12 as create_file
    participant p13 as _windows_api_path
    participant p14 as startswith
    participant p15 as HANDLE
    participant p16 as get_last_error
    participant p17 as WinError
    participant p18 as _WindowsDirectoryGuardUnavailableError
    participant p19 as _ByHandleFileInformation
    participant p20 as get_information
    participant p21 as byref
    p0-->>p1: Path
    p0-->>p2: is_absolute
    p0-->>p3: OSError
    p0-->>p4: uuid4
    p0->>p5: guard_windows_directory_chain
    p5->>p6: WindowsDirectoryGuardError
    p5-->>p1: Path
    p5-->>p7: abspath
    p5-->>p8: fspath
    p5->>p6: WindowsDirectoryGuardError
    p5-->>p1: Path
    p5-->>p9: append
    p5->>p10: _open_windows_directory_guard
    p10-->>p11: WinDLL
    p10-->>p12: create_file
    p10->>p13: _windows_api_path
    p13-->>p7: abspath
    p13-->>p8: fspath
    p13-->>p14: startswith
    p13-->>p14: startswith
    p10-->>p15: HANDLE
    p10-->>p16: get_last_error
    p10-->>p17: WinError
    p10->>p18: _WindowsDirectoryGuardUnavailableError
    p10->>p6: WindowsDirectoryGuardError
    p10-->>p19: _ByHandleFileInformation
    p10-->>p20: get_information
    p10-->>p21: byref
    p10-->>p17: WinError
    p10-->>p16: get_last_error
```

> Call sequence diagram shows 30 of 385 interactions; 355 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. remove_guarded_tree"]
    s2["2. Path"]
    s3["3. is_absolute"]
    s4["4. OSError"]
    s5["5. uuid4"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path"]
    s9["9. abspath"]
    s10["10. fspath"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path"]
    s1 -. "Path(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError(...)" .-> s4
    s1 -. "uuid.uuid4(data not statically known)" .-> s5
    s1 -->|"guard_windows_directory_chain(Path(...), ...)"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath(os.fspath(...))" .-> s9
    s6 -. "os.fspath(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path(root_path.anchor)" .-> s12
    b0["filesystem_write claimed.rmdir"]
    s1 -. "filesystem_write claimed.rmdir" .-> b0
    b1["filesystem_write quarantine.rmdir"]
    s1 -. "filesystem_write quarantine.rmdir" .-> b1
    b2["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b2
    b3["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b3
    b4["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b4
    b5["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b5
    b6["filesystem_write os.rmdir"]
    s1 -. "filesystem_write os.rmdir" .-> b6
    b7["mutation handles.append"]
    s6 -. "mutation handles.append" .-> b7
    click s1 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s7 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `remove_guarded_tree` | `path: Path`, `expected_identity: tuple[int, int] \| None`, `expected_manifest: GuardedTreeManifest \| None` | `os`, `os`, `os`, `os` | - | `none` |
| `Path` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `uuid4` | - | - | - | - |
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
| remove_guarded_tree | Path | 1777 | `Path(path)` |
| remove_guarded_tree | is_absolute | 1778 | `target.is_absolute(data not statically known)` |
| remove_guarded_tree | OSError | 1779 | `OSError(...)` |
| remove_guarded_tree | uuid4 | 1781 | `uuid.uuid4(data not statically known)` |
| remove_guarded_tree | guard_windows_directory_chain | 1898 | `guard_windows_directory_chain(Path(...), ...)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | abspath | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | fspath | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path | 179 | `Path(root_path.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `claimed.rmdir` | `remove_guarded_tree` | 1950 |
| filesystem_write | `quarantine.rmdir` | `remove_guarded_tree` | 1963 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2167 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2173 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2192 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2202 |
| filesystem_write | `os.rmdir` | `remove_guarded_tree` | 2214 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `remove_guarded_tree` | `target.is_absolute` | 1778 |
| unresolved_call | `remove_guarded_tree` | `OSError` | 1779 |
| external_call | `remove_guarded_tree` | `uuid.uuid4` | 1781 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `remove_guarded_tree` | `first 12 steps` | 0 |

## Behavior

This flow starts at `remove_guarded_tree` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
