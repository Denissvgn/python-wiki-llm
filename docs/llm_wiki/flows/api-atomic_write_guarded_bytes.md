# atomic_write_guarded_bytes

**Entry point:** `atomic_write_guarded_bytes` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as atomic_write_guarded_bytes
    participant p1 as Path
    participant p2 as is_absolute
    participant p3 as OSError
    participant p4 as isinstance
    participant p5 as TypeError
    participant p6 as _atomic_write_guarded_bytes_windows
    participant p7 as uuid4
    participant p8 as guard_windows_directory_chain
    participant p9 as WindowsDirectoryGuardError
    participant p10 as abspath
    participant p11 as fspath
    participant p12 as append
    participant p13 as _open_windows_directory_guard
    participant p14 as WinDLL
    participant p15 as create_file
    participant p16 as _windows_api_path
    participant p17 as startswith
    participant p18 as HANDLE
    participant p19 as get_last_error
    participant p20 as WinError
    participant p21 as _WindowsDirectoryGuardUnavailableError
    p0-->>p1: Path
    p0-->>p2: is_absolute
    p0-->>p3: OSError
    p0-->>p3: OSError
    p0-->>p4: isinstance
    p0-->>p5: TypeError
    p0->>p6: _atomic_write_guarded_bytes_windows
    p6-->>p7: uuid4
    p6-->>p7: uuid4
    p6->>p8: guard_windows_directory_chain
    p8->>p9: WindowsDirectoryGuardError
    p8-->>p1: Path
    p8-->>p10: abspath
    p8-->>p11: fspath
    p8->>p9: WindowsDirectoryGuardError
    p8-->>p1: Path
    p8-->>p12: append
    p8->>p13: _open_windows_directory_guard
    p13-->>p14: WinDLL
    p13-->>p15: create_file
    p13->>p16: _windows_api_path
    p16-->>p10: abspath
    p16-->>p11: fspath
    p16-->>p17: startswith
    p16-->>p17: startswith
    p13-->>p18: HANDLE
    p13-->>p19: get_last_error
    p13-->>p20: WinError
    p13->>p21: _WindowsDirectoryGuardUnavailableError
    p13->>p9: WindowsDirectoryGuardError
```

> Call sequence diagram shows 30 of 372 interactions; 342 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. atomic_write_guarded_bytes"]
    s2["2. Path"]
    s3["3. is_absolute"]
    s4["4. OSError"]
    s5["5. OSError"]
    s6["6. isinstance"]
    s7["7. TypeError"]
    s8["8. _atomic_write_guarded_bytes_windows"]
    s9["9. uuid4"]
    s10["10. uuid4"]
    s11["11. guard_windows_directory_chain"]
    s12["12. WindowsDirectoryGuardError"]
    s1 -. "Path(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError(...)" .-> s4
    s1 -. "OSError(...)" .-> s5
    s1 -. "isinstance(data, bytes)" .-> s6
    s1 -. "TypeError('Guarded output data must be bytes.')" .-> s7
    s1 -->|"_atomic_write_guarded_bytes_windows(target, data, expected_existing=expected_existing, require_single_link=require_single_link)"| s8
    s8 -. "uuid.uuid4(data not statically known)" .-> s9
    s8 -. "uuid.uuid4(data not statically known)" .-> s10
    s8 -->|"guard_windows_directory_chain(Path(...), relative_components)"| s11
    s11 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s12
    b0["filesystem_write quarantine.unlink"]
    s8 -. "filesystem_write quarantine.unlink" .-> b0
    b1["filesystem_write temporary.unlink"]
    s8 -. "filesystem_write temporary.unlink" .-> b1
    b2["mutation handles.append"]
    s11 -. "mutation handles.append" .-> b2
    b3["mutation handles.append"]
    s11 -. "mutation handles.append" .-> b3
    b4["mutation handles.append"]
    s11 -. "mutation handles.append" .-> b4
    click s1 "../modules/filesystem_guard.md"
    click s8 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
    click s12 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `atomic_write_guarded_bytes` | `path: Path`, `data: bytes`, `mode: int`, `require_single_link: bool`, `expected_existing: bytes \| None \| object` | `os` | - | `target` |
| `Path` | - | - | - | - |
| `is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `OSError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_atomic_write_guarded_bytes_windows` | `target: Path`, `data: bytes`, `expected_existing: bytes \| None \| object`, `require_single_link: bool` | `os`, `os`, `os`, `os`, `os`, `_EXPECTED_EXISTING_UNSET` | - | - |
| `uuid4` | - | - | - | - |
| `uuid4` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| atomic_write_guarded_bytes | Path | 1603 | `Path(path)` |
| atomic_write_guarded_bytes | is_absolute | 1604 | `target.is_absolute(data not statically known)` |
| atomic_write_guarded_bytes | OSError | 1605 | `OSError(...)` |
| atomic_write_guarded_bytes | OSError | 1607 | `OSError(...)` |
| atomic_write_guarded_bytes | isinstance | 1608 | `isinstance(data, bytes)` |
| atomic_write_guarded_bytes | TypeError | 1609 | `TypeError('Guarded output data must be bytes.')` |
| atomic_write_guarded_bytes | _atomic_write_guarded_bytes_windows | 1611 | `_atomic_write_guarded_bytes_windows(target, data, expected_existing=expected_existing, require_single_link=require_single_link)` |
| _atomic_write_guarded_bytes_windows | uuid4 | 2566 | `uuid.uuid4(data not statically known)` |
| _atomic_write_guarded_bytes_windows | uuid4 | 2567 | `uuid.uuid4(data not statically known)` |
| _atomic_write_guarded_bytes_windows | guard_windows_directory_chain | 2571 | `guard_windows_directory_chain(Path(...), relative_components)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `quarantine.unlink` | `_atomic_write_guarded_bytes_windows` | 2655 |
| filesystem_write | `temporary.unlink` | `_atomic_write_guarded_bytes_windows` | 2660 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `atomic_write_guarded_bytes` | `target.is_absolute` | 1604 |
| unresolved_call | `atomic_write_guarded_bytes` | `OSError` | 1605 |
| unresolved_call | `atomic_write_guarded_bytes` | `OSError` | 1607 |
| unresolved_call | `atomic_write_guarded_bytes` | `isinstance` | 1608 |
| unresolved_call | `atomic_write_guarded_bytes` | `TypeError` | 1609 |
| external_call | `_atomic_write_guarded_bytes_windows` | `uuid.uuid4` | 2566 |
| external_call | `_atomic_write_guarded_bytes_windows` | `uuid.uuid4` | 2567 |
| step_limit | `atomic_write_guarded_bytes` | `first 12 steps` | 0 |
| truncated_flow | `atomic_write_guarded_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `atomic_write_guarded_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
