# unlink_guarded_bytes

**Entry point:** `unlink_guarded_bytes` (`api`)
**Source:** [filesystem_guard](../modules/filesystem_guard.md)
**Modules touched:** [filesystem_guard](../modules/filesystem_guard.md), [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as unlink_guarded_bytes
    participant p1 as before_wiki_write
    participant p2 as _unlink_guarded_bytes
    participant p3 as after_wiki_write
    participant p4 as ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)
    participant p5 as Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)
    participant p6 as ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…basis.py:after_wiki_write)
    participant p7 as basis.before_write
    participant p8 as target.is_absolute
    participant p9 as basis.after_write
    participant p10 as Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)
    participant p11 as OSError
    participant p12 as Path (src/llm_wiki_cli/services…basis.py:after_wiki_write)
    participant p13 as isinstance
    participant p14 as TypeError
    participant p15 as uuid.uuid4 (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)
    participant p16 as guard_windows_directory_chain
    participant p17 as move_windows_path_write_through
    participant p18 as quarantine.lstat
    participant p19 as getattr (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)
    participant p20 as WindowsFileGuardError
    participant p21 as open_windows_readonly_file
    participant p22 as stat.S_ISREG
    participant p23 as stream.read
    participant p24 as quarantine.unlink
    p0->>p1: before_wiki_write
    p0->>p2: _unlink_guarded_bytes
    p0->>p3: after_wiki_write
    p1-->>p4: ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)
    p2-->>p5: Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(path)
    p3-->>p6: ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…basis.py:after_wiki_write)
    p1-->>p7: basis.before_write(Path(...), content)
    p2-->>p8: target.is_absolute
    p3-->>p9: basis.after_write(Path(...), content)
    p1-->>p10: Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)(path)
    p2-->>p11: OSError(...)
    p3-->>p12: Path (src/llm_wiki_cli/services…basis.py:after_wiki_write)(path)
    p2-->>p13: isinstance(expected, bytes)
    p2-->>p14: TypeError('Guarded unlink expected content must be bytes.')
    p2-->>p15: uuid.uuid4 (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)
    p2->>p16: guard_windows_directory_chain
    p2-->>p5: Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(target.parent.anchor)
    p2->>p17: move_windows_path_write_through
    p2-->>p18: quarantine.lstat
    p2-->>p19: getattr (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(metadata, 'st_file_attributes', 0)
    p2->>p20: WindowsFileGuardError
    p2->>p21: open_windows_readonly_file
    p2-->>p22: stat.S_ISREG(opened.st_mode)
    p2-->>p23: stream.read
    p2->>p20: WindowsFileGuardError
    p2-->>p24: quarantine.unlink
    p2->>p17: move_windows_path_write_through
    p2-->>p19: getattr (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(os, 'O_NOFOLLOW', None)
    p2-->>p19: getattr (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(os, 'O_DIRECTORY', None)
    p2-->>p11: OSError('This POSIX platform cannot provide guarded unlink.')
```

> Call sequence diagram shows 30 of 311 interactions; 281 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 13 of 185 (172 omitted); unresolved 8 of 41 (33 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 13 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 13 | - | external | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:guard_windows_directory_chain` | 13 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 21 | - | external | 14 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 21 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_open_windows_directory_guard` | 21 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 9 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 24 | - | external | 2 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_windows_api_path` | 24 | - | unresolved | 2 |
> Omission summary shows 8 of 40 groups; 32 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. unlink_guarded_bytes"]
    s2["2. before_wiki_write"]
    s3["3. ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)"]
    s4["4. basis.before_write"]
    s5["5. Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)"]
    s6["6. _unlink_guarded_bytes"]
    s7["7. Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)"]
    s8["8. target.is_absolute"]
    s9["9. OSError"]
    s10["10. isinstance"]
    s11["11. TypeError"]
    s12["12. uuid.uuid4 (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)"]
    s1 -->|"before_wiki_write(path, None)"| s2
    s2 -. "ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)(data not statically known)" .-> s3
    s2 -. "basis.before_write(Path(...), content)" .-> s4
    s2 -. "Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)(path)" .-> s5
    s1 -->|"_unlink_guarded_bytes(path, expected=expected)"| s6
    s6 -. "Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(path)" .-> s7
    s6 -. "target.is_absolute(data not statically known)" .-> s8
    s6 -. "OSError(...)" .-> s9
    s6 -. "isinstance(expected, bytes)" .-> s10
    s6 -. "TypeError('Guarded unlink expected content must be bytes.')" .-> s11
    s6 -. "uuid.uuid4 (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)(data not statically known)" .-> s12
    b0["filesystem_write quarantine.unlink"]
    s6 -. "filesystem_write quarantine.unlink" .-> b0
    b1["mutation chunks.append"]
    s6 -. "mutation chunks.append" .-> b1
    b2["filesystem_write os.unlink"]
    s6 -. "filesystem_write os.unlink" .-> b2
    click s1 "../modules/filesystem_guard.md"
    click s2 "../modules/wiki_write_basis.md"
    click s6 "../modules/filesystem_guard.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `unlink_guarded_bytes` | `path: Path`, `expected: bytes` | - | - | - |
| `before_wiki_write` | `path: str \| Path`, `content: bytes \| None` | - | - | - |
| `ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write)` | - | - | - | - |
| `basis.before_write` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…asis.py:before_wiki_write)` | - | - | - | - |
| `_unlink_guarded_bytes` | `path: Path`, `expected: bytes` | `os`, `os`, `os`, `os`, `os` | - | `none` |
| `Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)` | - | - | - | - |
| `target.is_absolute` | - | - | - | - |
| `OSError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `uuid.uuid4 (src/llm_wiki_cli/services….py:_unlink_guarded_bytes)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| unlink_guarded_bytes | before_wiki_write | 1685 | `before_wiki_write(path, None)` |
| before_wiki_write | ACTIVE_WRITE_BASIS.get (src/llm_wiki_cli/services…asis.py:before_wiki_write) | 24 | `ACTIVE_WRITE_BASIS.get(data not statically known)` |
| before_wiki_write | basis.before_write | 26 | `basis.before_write(Path(...), content)` |
| before_wiki_write | Path (src/llm_wiki_cli/services…asis.py:before_wiki_write) | 26 | `Path(path)` |
| unlink_guarded_bytes | _unlink_guarded_bytes | 1686 | `_unlink_guarded_bytes(path, expected=expected)` |
| _unlink_guarded_bytes | Path (src/llm_wiki_cli/services….py:_unlink_guarded_bytes) | 1693 | `Path(path)` |
| _unlink_guarded_bytes | target.is_absolute | 1694 | `target.is_absolute(data not statically known)` |
| _unlink_guarded_bytes | OSError | 1695 | `OSError(...)` |
| _unlink_guarded_bytes | isinstance | 1696 | `isinstance(expected, bytes)` |
| _unlink_guarded_bytes | TypeError | 1697 | `TypeError('Guarded unlink expected content must be bytes.')` |
| _unlink_guarded_bytes | uuid.uuid4 (src/llm_wiki_cli/services….py:_unlink_guarded_bytes) | 1699 | `uuid.uuid4(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `quarantine.unlink` | `_unlink_guarded_bytes` | 1728 |
| mutation | `chunks.append` | `_unlink_guarded_bytes` | 1773 |
| filesystem_write | `os.unlink` | `_unlink_guarded_bytes` | 1780 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `before_wiki_write` | `ACTIVE_WRITE_BASIS.get` | 24 |
| unresolved_call | `before_wiki_write` | `basis.before_write` | 26 |
| unresolved_call | `_unlink_guarded_bytes` | `target.is_absolute` | 1694 |
| external_call | `_unlink_guarded_bytes` | `OSError` | 1695 |
| external_call | `_unlink_guarded_bytes` | `isinstance` | 1696 |
| external_call | `_unlink_guarded_bytes` | `TypeError` | 1697 |
| external_call | `_unlink_guarded_bytes` | `uuid.uuid4` | 1699 |
| step_limit | `unlink_guarded_bytes` | `first 12 steps` | 0 |
| truncated_flow | `unlink_guarded_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `unlink_guarded_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
