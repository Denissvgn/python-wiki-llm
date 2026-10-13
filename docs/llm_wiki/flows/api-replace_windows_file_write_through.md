# replace_windows_file_write_through

**Entry point:** `replace_windows_file_write_through` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as replace_windows_file_write_through
    participant p1 as move_windows_path_write_through
    participant p2 as WindowsDurabilityError
    participant p3 as ctypes.WinDLL
    participant p4 as move_file
    participant p5 as _windows_api_path
    participant p6 as Path
    participant p7 as ctypes.get_last_error
    participant p8 as FileExistsError
    participant p9 as os.strerror
    participant p10 as ctypes.WinError
    participant p11 as os.path.abspath
    participant p12 as os.fspath
    participant p13 as value.startswith
    p0->>p1: move_windows_path_write_through
    p1->>p2: WindowsDurabilityError
    p1-->>p3: ctypes.WinDLL('kernel32', use_last_error=True)
    p1-->>p4: move_file(_windows_api_path(...), _windows_api_path(...), flags)
    p1->>p5: _windows_api_path
    p1-->>p6: Path(source)
    p1->>p5: _windows_api_path
    p1-->>p6: Path(target)
    p1-->>p7: ctypes.get_last_error
    p1-->>p8: FileExistsError(error_number, os.strerror(...), target)
    p1-->>p9: os.strerror(error_number)
    p1-->>p10: ctypes.WinError(error_number)
    p1->>p2: WindowsDurabilityError
    p5-->>p11: os.path.abspath(os.fspath(...))
    p5-->>p12: os.fspath(path)
    p5-->>p13: value.startswith('\\\\?\\')
    p5-->>p13: value.startswith('\\\\')
```

> Call sequence diagram shows 17 of 17 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 9 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. replace_windows_file_write_through"]
    s2["2. move_windows_path_write_through"]
    s3["3. WindowsDurabilityError"]
    s4["4. ctypes.WinDLL"]
    s5["5. move_file"]
    s6["6. _windows_api_path"]
    s7["7. os.path.abspath"]
    s8["8. os.fspath"]
    s9["9. value.startswith"]
    s10["10. value.startswith"]
    s11["11. Path"]
    s12["12. _windows_api_path"]
    s1 -->|"move_windows_path_write_through(source, target, replace_existing=True)"| s2
    s2 -->|"WindowsDurabilityError('Write-through Windows moves are unavailable on this platform.')"| s3
    s2 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s4
    s2 -. "move_file(_windows_api_path(...), _windows_api_path(...), flags)" .-> s5
    s2 -->|"_windows_api_path(Path(...))"| s6
    s6 -. "os.path.abspath(os.fspath(...))" .-> s7
    s6 -. "os.fspath(path)" .-> s8
    s6 -. "value.startswith('\\\\?\\')" .-> s9
    s6 -. "value.startswith('\\\\')" .-> s10
    s2 -. "Path(source)" .-> s11
    s2 -->|"_windows_api_path(Path(...))"| s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s3 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s12 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `replace_windows_file_write_through` | `source: Path`, `target: Path` | - | - | - |
| `move_windows_path_write_through` | `source: Path`, `target: Path`, `replace_existing: bool` | `os` | `move_file.argtypes`, `move_file.restype` | - |
| `WindowsDurabilityError` | - | - | - | - |
| `ctypes.WinDLL` | - | - | - | - |
| `move_file` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |
| `os.path.abspath` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `value.startswith` | - | - | - | - |
| `value.startswith` | - | - | - | - |
| `Path` | - | - | - | - |
| `_windows_api_path` | `path: Path` | - | - | `value`, `...`, `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| replace_windows_file_write_through | move_windows_path_write_through | 685 | `move_windows_path_write_through(source, target, replace_existing=True)` |
| move_windows_path_write_through | WindowsDurabilityError | 701 | `WindowsDurabilityError('Write-through Windows moves are unavailable on this platform.')` |
| move_windows_path_write_through | ctypes.WinDLL | 706 | `ctypes.WinDLL('kernel32', use_last_error=True)` |
| move_windows_path_write_through | move_file | 713 | `move_file(_windows_api_path(...), _windows_api_path(...), flags)` |
| move_windows_path_write_through | _windows_api_path | 714 | `_windows_api_path(Path(...))` |
| _windows_api_path | os.path.abspath | 1310 | `os.path.abspath(os.fspath(...))` |
| _windows_api_path | os.fspath | 1310 | `os.fspath(path)` |
| _windows_api_path | value.startswith | 1311 | `value.startswith('\\\\?\\')` |
| _windows_api_path | value.startswith | 1313 | `value.startswith('\\\\')` |
| move_windows_path_write_through | Path | 714 | `Path(source)` |
| move_windows_path_write_through | _windows_api_path | 715 | `_windows_api_path(Path(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `move_windows_path_write_through` | `ctypes.WinDLL` | 706 |
| unresolved_call | `move_windows_path_write_through` | `move_file` | 713 |
| external_call | `_windows_api_path` | `os.path.abspath` | 1310 |
| external_call | `_windows_api_path` | `os.fspath` | 1310 |
| unresolved_call | `_windows_api_path` | `value.startswith` | 1311 |
| unresolved_call | `_windows_api_path` | `value.startswith` | 1313 |
| step_limit | `replace_windows_file_write_through` | `first 12 steps` | 0 |

## Behavior

This flow starts at `replace_windows_file_write_through` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
