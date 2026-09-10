# atomic_write_private_bytes

**Entry point:** `atomic_write_private_bytes` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as atomic_write_private_bytes
    participant p1 as Path (src/llm_wiki_cli/services…tomic_write_private_bytes)
    participant p2 as target.is_absolute
    participant p3 as OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)
    participant p4 as isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes)
    participant p5 as TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes)
    participant p6 as _atomic_write_private_bytes_windows
    participant p7 as uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p8 as guard_windows_directory_chain
    participant p9 as WindowsDirectoryGuardError
    participant p10 as Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p11 as os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p12 as os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    participant p13 as handles.append
    participant p14 as _open_windows_directory_guard
    participant p15 as ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p16 as create_file (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p17 as _windows_api_path
    participant p18 as os.path.abspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    participant p19 as os.fspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    participant p20 as value.startswith
    participant p21 as wintypes.HANDLE (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p22 as ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p23 as ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    participant p24 as _WindowsDirectoryGuardUnavailableError
    p0-->>p1: Path (src/llm_wiki_cli/services…tomic_write_private_bytes)
    p0-->>p2: target.is_absolute
    p0-->>p3: OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)
    p0-->>p3: OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)
    p0-->>p4: isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes)
    p0-->>p5: TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes)
    p0->>p6: _atomic_write_private_bytes_windows
    p6-->>p7: uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)
    p6-->>p7: uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)
    p6->>p8: guard_windows_directory_chain
    p8->>p9: WindowsDirectoryGuardError
    p8-->>p10: Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    p8-->>p11: os.path.abspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    p8-->>p12: os.fspath (src/llm_wiki_cli/services…d_windows_directory_chain)
    p8->>p9: WindowsDirectoryGuardError
    p8-->>p10: Path (src/llm_wiki_cli/services…d_windows_directory_chain)
    p8-->>p13: handles.append
    p8->>p14: _open_windows_directory_guard
    p14-->>p15: ctypes.WinDLL (src/llm_wiki_cli/services…n_windows_directory_guard)
    p14-->>p16: create_file (src/llm_wiki_cli/services…n_windows_directory_guard)
    p14->>p17: _windows_api_path
    p17-->>p18: os.path.abspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    p17-->>p19: os.fspath (src/llm_wiki_cli/services…uard.py:_windows_api_path)
    p17-->>p20: value.startswith
    p17-->>p20: value.startswith
    p14-->>p21: wintypes.HANDLE (src/llm_wiki_cli/services…n_windows_directory_guard)
    p14-->>p22: ctypes.get_last_error (src/llm_wiki_cli/services…n_windows_directory_guard)
    p14-->>p23: ctypes.WinError (src/llm_wiki_cli/services…n_windows_directory_guard)
    p14->>p24: _WindowsDirectoryGuardUnavailableError
    p14->>p9: WindowsDirectoryGuardError
```

> Call sequence diagram shows 30 of 432 interactions; 402 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. atomic_write_private_bytes"]
    s2["2. Path (src/llm_wiki_cli/services…tomic_write_private_bytes)"]
    s3["3. target.is_absolute"]
    s4["4. OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)"]
    s5["5. OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)"]
    s6["6. isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes)"]
    s7["7. TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes)"]
    s8["8. _atomic_write_private_bytes_windows"]
    s9["9. uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)"]
    s10["10. uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)"]
    s11["11. guard_windows_directory_chain"]
    s12["12. WindowsDirectoryGuardError"]
    s1 -. "Path (src/llm_wiki_cli/services…tomic_write_private_bytes)(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)(...)" .-> s4
    s1 -. "OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)(...)" .-> s5
    s1 -. "isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes)(data, bytes)" .-> s6
    s1 -. "TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes)('Private atomic output data must be bytes.')" .-> s7
    s1 -->|"_atomic_write_private_bytes_windows(target, data, expected_existing=expected_existing)"| s8
    s8 -. "uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)(data not statically known)" .-> s9
    s8 -. "uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)(data not statically known)" .-> s10
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
| `atomic_write_private_bytes` | `path: Path`, `data: bytes`, `expected_existing: bytes \| None \| object` | `os` | - | `target` |
| `Path (src/llm_wiki_cli/services…tomic_write_private_bytes)` | - | - | - | - |
| `target.is_absolute` | - | - | - | - |
| `OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)` | - | - | - | - |
| `OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes)` | - | - | - | - |
| `_atomic_write_private_bytes_windows` | `target: Path`, `data: bytes`, `expected_existing: bytes \| None \| object`, `require_single_link: bool` | `_EXPECTED_EXISTING_UNSET` | - | - |
| `uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)` | - | - | - | - |
| `uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)` | - | - | - | - |
| `guard_windows_directory_chain` | `root: Path`, `relative_components: Sequence[str]`, `create_missing: bool`, `require_restrictive_dacl: bool` | `os`, `WindowsDurabilityError` | - | - |
| `WindowsDirectoryGuardError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| atomic_write_private_bytes | Path (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1548 | `Path(path)` |
| atomic_write_private_bytes | target.is_absolute | 1549 | `target.is_absolute(data not statically known)` |
| atomic_write_private_bytes | OSError (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1550 | `OSError(...)` |
| atomic_write_private_bytes | OSError (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1552 | `OSError(...)` |
| atomic_write_private_bytes | isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1553 | `isinstance(data, bytes)` |
| atomic_write_private_bytes | TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1554 | `TypeError('Private atomic output data must be bytes.')` |
| atomic_write_private_bytes | _atomic_write_private_bytes_windows | 1556 | `_atomic_write_private_bytes_windows(target, data, expected_existing=expected_existing)` |
| _atomic_write_private_bytes_windows | uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows) | 2450 | `uuid.uuid4(data not statically known)` |
| _atomic_write_private_bytes_windows | uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows) | 2451 | `uuid.uuid4(data not statically known)` |
| _atomic_write_private_bytes_windows | guard_windows_directory_chain | 2455 | `guard_windows_directory_chain(Path(...), relative_components)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `quarantine.unlink` | `_atomic_write_private_bytes_windows` | 2529 |
| filesystem_write | `temporary.unlink` | `_atomic_write_private_bytes_windows` | 2534 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `atomic_write_private_bytes` | `target.is_absolute` | 1549 |
| external_call | `atomic_write_private_bytes` | `OSError` | 1550 |
| external_call | `atomic_write_private_bytes` | `OSError` | 1552 |
| external_call | `atomic_write_private_bytes` | `isinstance` | 1553 |
| external_call | `atomic_write_private_bytes` | `TypeError` | 1554 |
| external_call | `_atomic_write_private_bytes_windows` | `uuid.uuid4` | 2450 |
| external_call | `_atomic_write_private_bytes_windows` | `uuid.uuid4` | 2451 |
| step_limit | `atomic_write_private_bytes` | `first 12 steps` | 0 |
| truncated_flow | `atomic_write_private_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `atomic_write_private_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
