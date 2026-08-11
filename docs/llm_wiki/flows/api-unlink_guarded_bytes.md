# unlink_guarded_bytes

**Entry point:** `unlink_guarded_bytes` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as unlink_guarded_bytes
    participant p1 as Path
    participant p2 as is_absolute
    participant p3 as OSError
    participant p4 as isinstance
    participant p5 as TypeError
    participant p6 as uuid4
    participant p7 as guard_windows_directory_chain
    participant p8 as WindowsDirectoryGuardError
    participant p9 as abspath
    participant p10 as fspath
    participant p11 as append
    participant p12 as _open_windows_directory_guard
    participant p13 as WinDLL
    participant p14 as create_file
    participant p15 as _windows_api_path
    participant p16 as startswith
    participant p17 as HANDLE
    participant p18 as get_last_error
    participant p19 as WinError
    participant p20 as _WindowsDirectoryGuardUnavailableError
    participant p21 as _ByHandleFileInformation
    participant p22 as get_information
    participant p23 as byref
    p0-->>p1: Path
    p0-->>p2: is_absolute
    p0-->>p3: OSError
    p0-->>p4: isinstance
    p0-->>p5: TypeError
    p0-->>p6: uuid4
    p0->>p7: guard_windows_directory_chain
    p7->>p8: WindowsDirectoryGuardError
    p7-->>p1: Path
    p7-->>p9: abspath
    p7-->>p10: fspath
    p7->>p8: WindowsDirectoryGuardError
    p7-->>p1: Path
    p7-->>p11: append
    p7->>p12: _open_windows_directory_guard
    p12-->>p13: WinDLL
    p12-->>p14: create_file
    p12->>p15: _windows_api_path
    p15-->>p9: abspath
    p15-->>p10: fspath
    p15-->>p16: startswith
    p15-->>p16: startswith
    p12-->>p17: HANDLE
    p12-->>p18: get_last_error
    p12-->>p19: WinError
    p12->>p20: _WindowsDirectoryGuardUnavailableError
    p12->>p8: WindowsDirectoryGuardError
    p12-->>p21: _ByHandleFileInformation
    p12-->>p22: get_information
    p12-->>p23: byref
```

> Call sequence diagram shows 30 of 314 interactions; 284 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. unlink_guarded_bytes"]
    s2["2. Path"]
    s3["3. is_absolute"]
    s4["4. OSError"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. uuid4"]
    s8["8. guard_windows_directory_chain"]
    s9["9. WindowsDirectoryGuardError"]
    s10["10. Path"]
    s11["11. abspath"]
    s12["12. fspath"]
    s1 -. "Path(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError(...)" .-> s4
    s1 -. "isinstance(expected, bytes)" .-> s5
    s1 -. "TypeError('Guarded unlink expected content must be bytes.')" .-> s6
    s1 -. "uuid.uuid4(data not statically known)" .-> s7
    s1 -->|"guard_windows_directory_chain(Path(...), ...)"| s8
    s8 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s9
    s8 -. "Path(os.path.abspath(...))" .-> s10
    s8 -. "os.path.abspath(os.fspath(...))" .-> s11
    s8 -. "os.fspath(root)" .-> s12
    b0["filesystem_write quarantine.unlink"]
    s1 -. "filesystem_write quarantine.unlink" .-> b0
    b1["mutation chunks.append"]
    s1 -. "mutation chunks.append" .-> b1
    b2["filesystem_write os.unlink"]
    s1 -. "filesystem_write os.unlink" .-> b2
    b3["mutation handles.append"]
    s8 -. "mutation handles.append" .-> b3
    b4["mutation handles.append"]
    s8 -. "mutation handles.append" .-> b4
    b5["mutation handles.append"]
    s8 -. "mutation handles.append" .-> b5
    click s1 "../modules/filesystem_guard.md"
    click s8 "../modules/filesystem_guard.md"
    click s9 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `unlink_guarded_bytes` | `path: Path`, `expected: bytes` | `os`, `os`, `os`, `os`, `os` | - | `none` |
| `Path` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `uuid4` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| unlink_guarded_bytes | Path | 1669 | `Path(path)` |
| unlink_guarded_bytes | is_absolute | 1670 | `target.is_absolute(data not statically known)` |
| unlink_guarded_bytes | OSError | 1671 | `OSError(...)` |
| unlink_guarded_bytes | isinstance | 1672 | `isinstance(expected, bytes)` |
| unlink_guarded_bytes | TypeError | 1673 | `TypeError('Guarded unlink expected content must be bytes.')` |
| unlink_guarded_bytes | uuid4 | 1675 | `uuid.uuid4(data not statically known)` |
| unlink_guarded_bytes | guard_windows_directory_chain | 1677 | `guard_windows_directory_chain(Path(...), ...)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | abspath | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | fspath | 174 | `os.fspath(root)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `quarantine.unlink` | `unlink_guarded_bytes` | 1701 |
| mutation | `chunks.append` | `unlink_guarded_bytes` | 1746 |
| filesystem_write | `os.unlink` | `unlink_guarded_bytes` | 1753 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `unlink_guarded_bytes` | `target.is_absolute` | 1670 |
| unresolved_call | `unlink_guarded_bytes` | `OSError` | 1671 |
| unresolved_call | `unlink_guarded_bytes` | `isinstance` | 1672 |
| unresolved_call | `unlink_guarded_bytes` | `TypeError` | 1673 |
| external_call | `unlink_guarded_bytes` | `uuid.uuid4` | 1675 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `unlink_guarded_bytes` | `first 12 steps` | 0 |

## Behavior

This flow starts at `unlink_guarded_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
