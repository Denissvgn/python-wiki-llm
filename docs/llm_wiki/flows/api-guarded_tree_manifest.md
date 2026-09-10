# guarded_tree_manifest

**Entry point:** `guarded_tree_manifest` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as guarded_tree_manifest
    participant p1 as Path (src/llm_wiki_cli/services….py:guarded_tree_manifest)
    participant p2 as target.is_absolute
    participant p3 as OSError (src/llm_wiki_cli/services….py:guarded_tree_manifest)
    participant p4 as guard_windows_directory_chain
    participant p5 as WindowsDirectoryGuardError
    participant p6 as Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p7 as os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p8 as os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p9 as handles.append
    participant p10 as _open_windows_directory_guard
    participant p11 as ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p12 as create_file (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p13 as _windows_api_path
    participant p14 as os.path.abspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    participant p15 as os.fspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    participant p16 as value.startswith
    participant p17 as wintypes.HANDLE (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p18 as ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p19 as ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p20 as _WindowsDirectoryGuardUnavailableError
    participant p21 as _ByHandleFileInformation (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p22 as get_information (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p23 as ctypes.byref (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p24 as _close_windows_handle
    p0-->>p1: Path (src/llm_wiki_cli/services….py:guarded_tree_manifest)
    p0-->>p2: target.is_absolute
    p0-->>p3: OSError (src/llm_wiki_cli/services….py:guarded_tree_manifest)
    p0->>p4: guard_windows_directory_chain
    p4->>p5: WindowsDirectoryGuardError
    p4-->>p6: Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    p4-->>p7: os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    p4-->>p8: os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    p4->>p5: WindowsDirectoryGuardError
    p4-->>p6: Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    p4-->>p9: handles.append
    p4->>p10: _open_windows_directory_guard
    p10-->>p11: ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p12: create_file (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10->>p13: _windows_api_path
    p13-->>p14: os.path.abspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    p13-->>p15: os.fspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    p13-->>p16: value.startswith
    p13-->>p16: value.startswith
    p10-->>p17: wintypes.HANDLE (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p18: ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p19: ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10->>p20: _WindowsDirectoryGuardUnavailableError
    p10->>p5: WindowsDirectoryGuardError
    p10-->>p21: _ByHandleFileInformation (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p22: get_information (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p23: ctypes.byref (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p19: ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10-->>p18: ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    p10->>p24: _close_windows_handle
```

> Call sequence diagram shows 30 of 335 interactions; 305 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. guarded_tree_manifest"]
    s2["2. Path (src/llm_wiki_cli/services….py:guarded_tree_manifest)"]
    s3["3. target.is_absolute"]
    s4["4. OSError (src/llm_wiki_cli/services….py:guarded_tree_manifest)"]
    s5["5. guard_windows_directory_chain"]
    s6["6. WindowsDirectoryGuardError"]
    s7["7. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s8["8. os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s9["9. os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s10["10. WindowsDirectoryGuardError"]
    s11["11. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s12["12. handles.append"]
    s1 -. "Path (src/llm_wiki_cli/services….py:guarded_tree_manifest)(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError (src/llm_wiki_cli/services….py:guarded_tree_manifest)(...)" .-> s4
    s1 -->|"guard_windows_directory_chain(Path(...), ...)"| s5
    s5 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s6
    s5 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))" .-> s7
    s5 -. "os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))" .-> s8
    s5 -. "os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)" .-> s9
    s5 -->|"WindowsDirectoryGuardError(...)"| s10
    s5 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)" .-> s11
    s5 -. "handles.append(_open_windows_directory_guard(...))" .-> s12
    b0["mutation handles.append"]
    s5 -. "mutation handles.append" .-> b0
    b1["mutation handles.append"]
    s5 -. "mutation handles.append" .-> b1
    b2["mutation handles.append"]
    s5 -. "mutation handles.append" .-> b2
    click s1 "../modules/filesystem_guard.md"
    click s5 "../modules/filesystem_guard.md"
    click s6 "../modules/filesystem_guard.md"
    click s10 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `guarded_tree_manifest` | `path: Path` | `os`, `os`, `os`, `os` | - | `_guarded_tree_manifest_windows_path(...)`, `_guarded_tree_manifest_posix_fd(...)` |
| `Path (src/llm_wiki_cli/services….py:guarded_tree_manifest)` | - | - | - | - |
| `target.is_absolute` | - | - | - | - |
| `OSError (src/llm_wiki_cli/services….py:guarded_tree_manifest)` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…d_windows_directory_chain)` | - | - | - | - |
| `handles.append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| guarded_tree_manifest | Path (src/llm_wiki_cli/services….py:guarded_tree_manifest) | 1509 | `Path(path)` |
| guarded_tree_manifest | target.is_absolute | 1510 | `target.is_absolute(data not statically known)` |
| guarded_tree_manifest | OSError (src/llm_wiki_cli/services….py:guarded_tree_manifest) | 1511 | `OSError(...)` |
| guarded_tree_manifest | guard_windows_directory_chain | 1513 | `guard_windows_directory_chain(Path(...), ...)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 179 | `Path(root_path.anchor)` |
| guard_windows_directory_chain | handles.append | 182 | `handles.append(_open_windows_directory_guard(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `guarded_tree_manifest` | `target.is_absolute` | 1510 |
| external_call | `guarded_tree_manifest` | `OSError` | 1511 |
| external_call | `guard_windows_directory_chain` | `os.path.abspath` | 174 |
| external_call | `guard_windows_directory_chain` | `os.fspath` | 174 |
| step_limit | `guarded_tree_manifest` | `first 12 steps` | 0 |

## Behavior

This flow starts at `guarded_tree_manifest` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
