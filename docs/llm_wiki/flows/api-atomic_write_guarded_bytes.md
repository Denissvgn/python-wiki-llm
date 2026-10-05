# atomic_write_guarded_bytes

**Entry point:** `atomic_write_guarded_bytes` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md), [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as atomic_write_guarded_bytes
    participant p1 as Path (src/llm_wiki_cli/services…tomic_write_guarded_bytes)
    participant p2 as target.is_absolute
    participant p3 as OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)
    participant p4 as isinstance (src/llm_wiki_cli/services…tomic_write_guarded_bytes)
    participant p5 as TypeError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)
    participant p6 as before_wiki_write
    participant p7 as _atomic_write_guarded_bytes_windows
    participant p8 as _atomic_write_private_bytes_posix
    participant p9 as after_wiki_write
    participant p10 as ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)
    participant p11 as uuid.uuid4 (src/llm_wiki_cli/services…ite_guarded_bytes_windows)
    participant p12 as getattr (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p13 as ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…basis.py:after_wiki_write)
    participant p14 as basis.before_write
    participant p15 as basis.after_write
    participant p16 as Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)
    participant p17 as guard_windows_directory_chain
    participant p18 as OSError (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p19 as Path (src/llm_wiki_cli/services…basis.py:after_wiki_write)
    participant p20 as Path (src/llm_wiki_cli/services…ite_guarded_bytes_windows)
    participant p21 as os.path.lexists (src/llm_wiki_cli/services…ite_guarded_bytes_windows)
    participant p22 as os.open (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p23 as target.lstat
    participant p24 as uuid.uuid4 (src/llm_wiki_cli/services…write_private_bytes_posix)
    participant p25 as getattr (src/llm_wiki_cli/services…ite_guarded_bytes_windows)
    p0-->>p1: Path (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(path)
    p0-->>p2: target.is_absolute
    p0-->>p3: OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(...)
    p0-->>p3: OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(...)
    p0-->>p4: isinstance (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(data, bytes)
    p0-->>p5: TypeError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)('Guarded output data must be bytes.')
    p0->>p6: before_wiki_write
    p0->>p7: _atomic_write_guarded_bytes_windows
    p0->>p8: _atomic_write_private_bytes_posix
    p0->>p9: after_wiki_write
    p6-->>p10: ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)
    p7-->>p11: uuid.uuid4 (src/llm_wiki_cli/services…ite_guarded_bytes_windows)
    p8-->>p12: getattr (src/llm_wiki_cli/services…write_private_bytes_posix)(os, 'O_NOFOLLOW', None)
    p9-->>p13: ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…basis.py:after_wiki_write)
    p6-->>p14: basis.before_write(Path(...), content)
    p7-->>p11: uuid.uuid4 (src/llm_wiki_cli/services…ite_guarded_bytes_windows)
    p8-->>p12: getattr (src/llm_wiki_cli/services…write_private_bytes_posix)(os, 'O_DIRECTORY', None)
    p9-->>p15: basis.after_write(Path(...), content)
    p6-->>p16: Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)(path)
    p7->>p17: guard_windows_directory_chain
    p8-->>p18: OSError (src/llm_wiki_cli/services…write_private_bytes_posix)('This POSIX platform cannot provide no-follow directory writes.')
    p9-->>p19: Path (src/llm_wiki_cli/services…basis.py:after_wiki_write)(path)
    p7-->>p20: Path (src/llm_wiki_cli/services…ite_guarded_bytes_windows)(parent.anchor)
    p8-->>p12: getattr (src/llm_wiki_cli/services…write_private_bytes_posix)(os, 'O_CLOEXEC', 0)
    p7-->>p21: os.path.lexists (src/llm_wiki_cli/services…ite_guarded_bytes_windows)(target)
    p8-->>p22: os.open (src/llm_wiki_cli/services…write_private_bytes_posix)(target.anchor, directory_flags)
    p7-->>p23: target.lstat
    p8-->>p24: uuid.uuid4 (src/llm_wiki_cli/services…write_private_bytes_posix)
    p7-->>p25: getattr (src/llm_wiki_cli/services…ite_guarded_bytes_windows)(existing, 'st_file_attributes', 0)
    p8-->>p24: uuid.uuid4 (src/llm_wiki_cli/services…write_private_bytes_posix)
```

> Call sequence diagram shows 30 of 380 interactions; 350 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 238 (219 omitted); unresolved 6 of 47 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 15 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 15 | - | external | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 15 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 23 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 23 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 23 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 26 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 26 | - | unresolved | 2 |
> Omission summary shows 8 of 46 groups; 38 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. atomic_write_guarded_bytes"]
    s2["2. Path (src/llm_wiki_cli/services…tomic_write_guarded_bytes)"]
    s3["3. target.is_absolute"]
    s4["4. OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)"]
    s5["5. OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)"]
    s6["6. isinstance (src/llm_wiki_cli/services…tomic_write_guarded_bytes)"]
    s7["7. TypeError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)"]
    s8["8. before_wiki_write"]
    s9["9. ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)"]
    s10["10. basis.before_write"]
    s11["11. Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)"]
    s12["12. _atomic_write_guarded_bytes_windows"]
    s1 -. "Path (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(path)" .-> s2
    s1 -. "target.is_absolute(data not statically known)" .-> s3
    s1 -. "OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(...)" .-> s4
    s1 -. "OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(...)" .-> s5
    s1 -. "isinstance (src/llm_wiki_cli/services…tomic_write_guarded_bytes)(data, bytes)" .-> s6
    s1 -. "TypeError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)('Guarded output data must be bytes.')" .-> s7
    s1 -->|"before_wiki_write(target, data)"| s8
    s8 -. "ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)(data not statically known)" .-> s9
    s8 -. "basis.before_write(Path(...), content)" .-> s10
    s8 -. "Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)(path)" .-> s11
    s1 -->|"_atomic_write_guarded_bytes_windows(target, data, expected_existing=expected_existing, require_single_link=require_single_link)"| s12
    b0["filesystem_write quarantine.unlink"]
    s12 -. "filesystem_write quarantine.unlink" .-> b0
    b1["filesystem_write temporary.unlink"]
    s12 -. "filesystem_write temporary.unlink" .-> b1
    click s1 "../modules/filesystem_guard.md"
    click s8 "../modules/wiki_write_basis.md"
    click s12 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `atomic_write_guarded_bytes` | `path: Path`, `data: bytes`, `mode: int`, `require_single_link: bool`, `expected_existing: bytes \| None \| object` | `os` | - | `target` |
| `Path (src/llm_wiki_cli/services…tomic_write_guarded_bytes)` | - | - | - | - |
| `target.is_absolute` | - | - | - | - |
| `OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)` | - | - | - | - |
| `OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…tomic_write_guarded_bytes)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…tomic_write_guarded_bytes)` | - | - | - | - |
| `before_wiki_write` | `path: str \| Path`, `content: bytes \| None` | - | - | - |
| `ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)` | - | - | - | - |
| `basis.before_write` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)` | - | - | - | - |
| `_atomic_write_guarded_bytes_windows` | `target: Path`, `data: bytes`, `expected_existing: bytes \| None \| object`, `require_single_link: bool` | `os`, `os`, `os`, `os`, `os`, `_EXPECTED_EXISTING_UNSET` | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| atomic_write_guarded_bytes | Path (src/llm_wiki_cli/services…tomic_write_guarded_bytes) | 1615 | `Path(path)` |
| atomic_write_guarded_bytes | target.is_absolute | 1616 | `target.is_absolute(data not statically known)` |
| atomic_write_guarded_bytes | OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes) | 1617 | `OSError(...)` |
| atomic_write_guarded_bytes | OSError (src/llm_wiki_cli/services…tomic_write_guarded_bytes) | 1619 | `OSError(...)` |
| atomic_write_guarded_bytes | isinstance (src/llm_wiki_cli/services…tomic_write_guarded_bytes) | 1620 | `isinstance(data, bytes)` |
| atomic_write_guarded_bytes | TypeError (src/llm_wiki_cli/services…tomic_write_guarded_bytes) | 1621 | `TypeError('Guarded output data must be bytes.')` |
| atomic_write_guarded_bytes | before_wiki_write | 1624 | `before_wiki_write(target, data)` |
| before_wiki_write | ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write) | 24 | `ACTIVE_WRITE_BASIS.get(data not statically known)` |
| before_wiki_write | basis.before_write | 26 | `basis.before_write(Path(...), content)` |
| before_wiki_write | Path (src/llm_wiki_cli/services…asis.py:before_wiki_write) | 26 | `Path(path)` |
| atomic_write_guarded_bytes | _atomic_write_guarded_bytes_windows | 1626 | `_atomic_write_guarded_bytes_windows(target, data, expected_existing=expected_existing, require_single_link=require_single_link)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `quarantine.unlink` | `_atomic_write_guarded_bytes_windows` | 2679 |
| filesystem_write | `temporary.unlink` | `_atomic_write_guarded_bytes_windows` | 2684 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `atomic_write_guarded_bytes` | `target.is_absolute` | 1616 |
| external_call | `atomic_write_guarded_bytes` | `OSError` | 1617 |
| external_call | `atomic_write_guarded_bytes` | `OSError` | 1619 |
| external_call | `atomic_write_guarded_bytes` | `isinstance` | 1620 |
| external_call | `atomic_write_guarded_bytes` | `TypeError` | 1621 |
| unresolved_call | `before_wiki_write` | `ACTIVE_WRITE_BASIS.get` | 24 |
| unresolved_call | `before_wiki_write` | `basis.before_write` | 26 |
| step_limit | `atomic_write_guarded_bytes` | `first 12 steps` | 0 |
| truncated_flow | `atomic_write_guarded_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `atomic_write_guarded_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
