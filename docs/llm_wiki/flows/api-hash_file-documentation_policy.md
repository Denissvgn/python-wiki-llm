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
    participant p2 as Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    participant p3 as os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    participant p4 as os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    participant p5 as guard_windows_directory_chain
    participant p6 as WindowsDirectoryGuardError
    participant p7 as Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p8 as os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p9 as os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p10 as handles.append
    participant p11 as _open_windows_directory_guard
    participant p12 as ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p13 as create_file (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p14 as _windows_api_path
    participant p15 as os.path.abspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    participant p16 as os.fspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    participant p17 as value.startswith
    participant p18 as wintypes.HANDLE (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p19 as ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p20 as ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p21 as _WindowsDirectoryGuardUnavailableError
    participant p22 as _ByHandleFileInformation (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p23 as get_information (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p24 as ctypes.byref (src/llm_wiki_cli/services…n_windows_directory_guard)
    p0->>p1: _hash_file
    p1-->>p2: Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    p1-->>p3: os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    p1-->>p4: os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)
    p1->>p5: guard_windows_directory_chain
    p5->>p6: WindowsDirectoryGuardError
    p5-->>p7: Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    p5-->>p8: os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    p5-->>p9: os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    p5->>p6: WindowsDirectoryGuardError
    p5-->>p7: Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    p5-->>p10: handles.append
    p5->>p11: _open_windows_directory_guard
    p11-->>p12: ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p13: create_file (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11->>p14: _windows_api_path
    p14-->>p15: os.path.abspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    p14-->>p16: os.fspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    p14-->>p17: value.startswith
    p14-->>p17: value.startswith
    p11-->>p18: wintypes.HANDLE (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p19: ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p20: ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11->>p21: _WindowsDirectoryGuardUnavailableError
    p11->>p6: WindowsDirectoryGuardError
    p11-->>p22: _ByHandleFileInformation (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p23: get_information (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p24: ctypes.byref (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p20: ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    p11-->>p19: ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
```

> Call sequence diagram shows 30 of 356 interactions; 326 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_file"]
    s2["2. _hash_file"]
    s3["3. Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)"]
    s4["4. os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)"]
    s5["5. os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)"]
    s6["6. guard_windows_directory_chain"]
    s7["7. WindowsDirectoryGuardError"]
    s8["8. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s9["9. os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s10["10. os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s11["11. WindowsDirectoryGuardError"]
    s12["12. Path (src/llm_wiki_cli/services…d_windows_directory_chain)"]
    s1 -->|"_hash_file(Path(...))"| s2
    s2 -. "Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(os.path.abspath(...))" .-> s3
    s2 -. "os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(os.fspath(...))" .-> s4
    s2 -. "os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)(path)" .-> s5
    s2 -->|"guard_windows_directory_chain(absolute_path.parent, (...))"| s6
    s6 -->|"WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')"| s7
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(os.path.abspath(...))" .-> s8
    s6 -. "os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)(os.fspath(...))" .-> s9
    s6 -. "os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)(root)" .-> s10
    s6 -->|"WindowsDirectoryGuardError(...)"| s11
    s6 -. "Path (src/llm_wiki_cli/services…d_windows_directory_chain)(root_path.anchor)" .-> s12
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
| `Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file)` | - | - | - | - |
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
| hash_file | _hash_file | 524 | `_hash_file(Path(...))` |
| _hash_file | Path (src/llm_wiki_cli/services…tion_policy.py:_hash_file) | 626 | `Path(os.path.abspath(...))` |
| _hash_file | os.path.abspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file) | 626 | `os.path.abspath(os.fspath(...))` |
| _hash_file | os.fspath (src/llm_wiki_cli/services…tion_policy.py:_hash_file) | 626 | `os.fspath(path)` |
| _hash_file | guard_windows_directory_chain | 628 | `guard_windows_directory_chain(absolute_path.parent, (...))` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `Path(os.path.abspath(...))` |
| guard_windows_directory_chain | os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.path.abspath(os.fspath(...))` |
| guard_windows_directory_chain | os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain) | 174 | `os.fspath(root)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 176 | `WindowsDirectoryGuardError(...)` |
| guard_windows_directory_chain | Path (src/llm_wiki_cli/services…d_windows_directory_chain) | 179 | `Path(root_path.anchor)` |

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
