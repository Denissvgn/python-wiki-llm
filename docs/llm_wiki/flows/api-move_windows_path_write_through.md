# move_windows_path_write_through

**Entry point:** `move_windows_path_write_through` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as move_windows_path_write_through
    participant p1 as WindowsDurabilityError
    participant p2 as ctypes.WinDLL
    participant p3 as move_file
    participant p4 as _windows_api_path
    participant p5 as os.path.abspath
    participant p6 as os.fspath
    participant p7 as value.startswith
    participant p8 as Path
    participant p9 as ctypes.get_last_error
    participant p10 as FileExistsError
    participant p11 as os.strerror
    participant p12 as ctypes.WinError
    p0->>p1: WindowsDurabilityError
    p0-->>p2: ctypes.WinDLL
    p0-->>p3: move_file
    p0->>p4: _windows_api_path
    p4-->>p5: os.path.abspath
    p4-->>p6: os.fspath
    p4-->>p7: value.startswith
    p4-->>p7: value.startswith
    p0-->>p8: Path
    p0->>p4: _windows_api_path
    p0-->>p8: Path
    p0-->>p9: ctypes.get_last_error
    p0-->>p10: FileExistsError
    p0-->>p11: os.strerror
    p0-->>p12: ctypes.WinError
    p0->>p1: WindowsDurabilityError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. move_windows_path_write_through"]
    s2["2. WindowsDurabilityError"]
    s3["3. ctypes.WinDLL"]
    s4["4. move_file"]
    s5["5. _windows_api_path"]
    s6["6. os.path.abspath"]
    s7["7. os.fspath"]
    s8["8. value.startswith"]
    s9["9. value.startswith"]
    s10["10. Path"]
    s11["11. _windows_api_path"]
    s12["12. Path"]
    s1 -->|"WindowsDurabilityError('Write-through Windows moves are unavailable on this platform.')"| s2
    s1 -. "ctypes.WinDLL('kernel32', use_last_error=True)" .-> s3
    s1 -. "move_file(_windows_api_path(...), _windows_api_path(...), flags)" .-> s4
    s1 -->|"_windows_api_path(Path(...))"| s5
    s5 -. "os.path.abspath(os.fspath(...))" .-> s6
    s5 -. "os.fspath(path)" .-> s7
    s5 -. "value.startswith('\\\\?\\')" .-> s8
    s5 -. "value.startswith('\\\\')" .-> s9
    s1 -. "Path(source)" .-> s10
    s1 -->|"_windows_api_path(Path(...))"| s11
    s1 -. "Path(target)" .-> s12
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/filesystem_guard.md"
    click s5 "../modules/filesystem_guard.md"
    click s11 "../modules/filesystem_guard.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| move_windows_path_write_through | Path | 715 | `Path(target)` |

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
| step_limit | `move_windows_path_write_through` | `first 12 steps` | 0 |

## Behavior

This flow starts at `move_windows_path_write_through` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
