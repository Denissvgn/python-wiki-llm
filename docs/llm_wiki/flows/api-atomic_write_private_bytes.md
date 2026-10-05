# atomic_write_private_bytes

**Entry point:** `atomic_write_private_bytes` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

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
    participant p7 as _atomic_write_private_bytes_posix
    participant p8 as uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p9 as getattr (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p10 as guard_windows_directory_chain
    participant p11 as OSError (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p12 as Path (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p13 as os.path.lexists (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p14 as os.open
    participant p15 as target.lstat
    participant p16 as uuid.uuid4 (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p17 as getattr (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p18 as stat.S_ISREG (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p19 as Path (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p20 as WindowsFileGuardError
    participant p21 as open_windows_private_write_file
    participant p22 as os.fdopen (src/llm_wiki_cli/services…ite_private_bytes_windows)
    participant p23 as os.close (src/llm_wiki_cli/services…write_private_bytes_posix)
    p0-->>p1: Path (src/llm_wiki_cli/services…tomic_write_private_bytes)(path)
    p0-->>p2: target.is_absolute
    p0-->>p3: OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)(...)
    p0-->>p3: OSError (src/llm_wiki_cli/services…tomic_write_private_bytes)(...)
    p0-->>p4: isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes)(data, bytes)
    p0-->>p5: TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes)('Private atomic output data must be bytes.')
    p0->>p6: _atomic_write_private_bytes_windows
    p0->>p7: _atomic_write_private_bytes_posix
    p6-->>p8: uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)
    p7-->>p9: getattr (src/llm_wiki_cli/services…write_private_bytes_posix)(os, 'O_NOFOLLOW', None)
    p6-->>p8: uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows)
    p7-->>p9: getattr (src/llm_wiki_cli/services…write_private_bytes_posix)(os, 'O_DIRECTORY', None)
    p6->>p10: guard_windows_directory_chain
    p7-->>p11: OSError (src/llm_wiki_cli/services…write_private_bytes_posix)('This POSIX platform cannot provide no-follow directory writes.')
    p6-->>p12: Path (src/llm_wiki_cli/services…ite_private_bytes_windows)(parent.anchor)
    p7-->>p9: getattr (src/llm_wiki_cli/services…write_private_bytes_posix)(os, 'O_CLOEXEC', 0)
    p6-->>p13: os.path.lexists (src/llm_wiki_cli/services…ite_private_bytes_windows)(target)
    p7-->>p14: os.open(target.anchor, directory_flags)
    p6-->>p15: target.lstat
    p7-->>p16: uuid.uuid4 (src/llm_wiki_cli/services…write_private_bytes_posix)
    p6-->>p17: getattr (src/llm_wiki_cli/services…ite_private_bytes_windows)(existing, 'st_file_attributes', 0)
    p7-->>p16: uuid.uuid4 (src/llm_wiki_cli/services…write_private_bytes_posix)
    p6-->>p18: stat.S_ISREG (src/llm_wiki_cli/services…ite_private_bytes_windows)(existing.st_mode)
    p7-->>p19: Path (src/llm_wiki_cli/services…write_private_bytes_posix)(component)
    p6->>p20: WindowsFileGuardError
    p7-->>p11: OSError (src/llm_wiki_cli/services…write_private_bytes_posix)(...)
    p6->>p21: open_windows_private_write_file
    p7-->>p14: os.open(component, directory_flags, dir_fd=parent_fd)
    p6-->>p22: os.fdopen (src/llm_wiki_cli/services…ite_private_bytes_windows)(descriptor, 'wb', closefd=True)
    p7-->>p23: os.close (src/llm_wiki_cli/services…write_private_bytes_posix)(parent_fd)
```

> Call sequence diagram shows 30 of 432 interactions; 402 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 23 of 264 (241 omitted); unresolved 2 of 49 (47 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 11 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 11 | - | external | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 11 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 19 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 19 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 19 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 22 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 22 | - | unresolved | 2 |
> Omission summary shows 8 of 61 groups; 53 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| atomic_write_private_bytes | Path (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1560 | `Path(path)` |
| atomic_write_private_bytes | target.is_absolute | 1561 | `target.is_absolute(data not statically known)` |
| atomic_write_private_bytes | OSError (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1562 | `OSError(...)` |
| atomic_write_private_bytes | OSError (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1564 | `OSError(...)` |
| atomic_write_private_bytes | isinstance (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1565 | `isinstance(data, bytes)` |
| atomic_write_private_bytes | TypeError (src/llm_wiki_cli/services…tomic_write_private_bytes) | 1566 | `TypeError('Private atomic output data must be bytes.')` |
| atomic_write_private_bytes | _atomic_write_private_bytes_windows | 1568 | `_atomic_write_private_bytes_windows(target, data, expected_existing=expected_existing)` |
| _atomic_write_private_bytes_windows | uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows) | 2474 | `uuid.uuid4(data not statically known)` |
| _atomic_write_private_bytes_windows | uuid.uuid4 (src/llm_wiki_cli/services…ite_private_bytes_windows) | 2475 | `uuid.uuid4(data not statically known)` |
| _atomic_write_private_bytes_windows | guard_windows_directory_chain | 2479 | `guard_windows_directory_chain(Path(...), relative_components)` |
| guard_windows_directory_chain | WindowsDirectoryGuardError | 170 | `WindowsDirectoryGuardError('Windows directory guards are unavailable on this platform.')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `quarantine.unlink` | `_atomic_write_private_bytes_windows` | 2553 |
| filesystem_write | `temporary.unlink` | `_atomic_write_private_bytes_windows` | 2558 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 182 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 189 |
| mutation | `handles.append` | `guard_windows_directory_chain` | 216 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `atomic_write_private_bytes` | `target.is_absolute` | 1561 |
| external_call | `atomic_write_private_bytes` | `OSError` | 1562 |
| external_call | `atomic_write_private_bytes` | `OSError` | 1564 |
| external_call | `atomic_write_private_bytes` | `isinstance` | 1565 |
| external_call | `atomic_write_private_bytes` | `TypeError` | 1566 |
| external_call | `_atomic_write_private_bytes_windows` | `uuid.uuid4` | 2474 |
| external_call | `_atomic_write_private_bytes_windows` | `uuid.uuid4` | 2475 |
| step_limit | `atomic_write_private_bytes` | `first 12 steps` | 0 |
| truncated_flow | `atomic_write_private_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `atomic_write_private_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
