# governance_lock

**Entry point:** `governance_lock` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [io](../modules/io.md), [knowledge_governance](../modules/knowledge_governance.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as governance_lock
    participant p1 as GovernanceError
    participant p2 as Path (src/llm_wiki_cli/services…ernance.py:governance_lock)
    participant p3 as first_unsafe_path_component
    participant p4 as _governance_lock_root
    participant p5 as lock_root.mkdir
    participant p6 as getattr (src/llm_wiki_cli/services…ernance.py:governance_lock)
    participant p7 as os.open
    participant p8 as os.fstat
    participant p9 as stat.S_ISREG
    participant p10 as os.write
    participant p11 as os.fsync
    participant p12 as os.fdopen
    participant p13 as os.close
    participant p14 as descriptor.seek
    participant p15 as msvcrt.locking
    participant p16 as descriptor.fileno
    participant p17 as fcntl.flock
    participant p18 as GovernanceConflictError
    participant p19 as descriptor.close
    participant p20 as Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p0->>p1: GovernanceError
    p0-->>p2: Path (src/llm_wiki_cli/services…ernance.py:governance_lock)(wiki_dir)
    p0->>p3: first_unsafe_path_component
    p0->>p1: GovernanceError
    p0->>p4: _governance_lock_root
    p0-->>p5: lock_root.mkdir(parents=True, exist_ok=True)
    p0->>p3: first_unsafe_path_component
    p0->>p1: GovernanceError
    p0-->>p6: getattr (src/llm_wiki_cli/services…ernance.py:governance_lock)(os, 'O_CLOEXEC', 0)
    p0-->>p6: getattr (src/llm_wiki_cli/services…ernance.py:governance_lock)(os, 'O_NOFOLLOW', 0)
    p0-->>p7: os.open(lock_path, flags, 384)
    p0->>p1: GovernanceError
    p0-->>p8: os.fstat(file_descriptor)
    p0-->>p9: stat.S_ISREG(metadata.st_mode)
    p0->>p1: GovernanceError
    p0-->>p10: os.write(file_descriptor, b'\x00')
    p0-->>p11: os.fsync(file_descriptor)
    p0-->>p12: os.fdopen(file_descriptor, 'r+', encoding='utf-8')
    p0-->>p13: os.close(file_descriptor)
    p0-->>p14: descriptor.seek(0)
    p0-->>p15: msvcrt.locking(descriptor.fileno(...), msvcrt.LK_NBLCK, 1)
    p0-->>p16: descriptor.fileno
    p0-->>p17: fcntl.flock(descriptor, ...)
    p0->>p18: GovernanceConflictError
    p0-->>p14: descriptor.seek(0)
    p0-->>p15: msvcrt.locking(descriptor.fileno(...), msvcrt.LK_UNLCK, 1)
    p0-->>p16: descriptor.fileno
    p0-->>p17: fcntl.flock(descriptor, fcntl.LOCK_UN)
    p0-->>p19: descriptor.close
    p3-->>p20: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.fspath(...))
```

> Call sequence diagram shows 30 of 61 interactions; 31 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 39 (24 omitted); unresolved 6 of 13 (7 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 4 | - | external | 19 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 4 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_governance_lock_root` | 31 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_governance_lock_root` | 31 | - | external | 5 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. governance_lock"]
    s2["2. GovernanceError"]
    s3["3. Path (src/llm_wiki_cli/services…ernance.py:governance_lock)"]
    s4["4. first_unsafe_path_component"]
    s5["5. Path (src/llm_wiki_cli/services…irst_unsafe_path_component)"]
    s6["6. os.fspath"]
    s7["7. Path (src/llm_wiki_cli/services…irst_unsafe_path_component)"]
    s8["8. os.path.abspath"]
    s9["9. lexical.is_absolute"]
    s10["10. Path.cwd"]
    s11["11. Path (src/llm_wiki_cli/services…irst_unsafe_path_component)"]
    s12["12. list"]
    s1 -->|"GovernanceError('lock', 'unknown mutation lock')"| s2
    s1 -. "Path (src/llm_wiki_cli/services…ernance.py:governance_lock)(wiki_dir)" .-> s3
    s1 -->|"first_unsafe_path_component(root)"| s4
    s4 -. "Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.fspath(...))" .-> s5
    s4 -. "os.fspath(path)" .-> s6
    s4 -. "Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.path.abspath(...))" .-> s7
    s4 -. "os.path.abspath(lexical)" .-> s8
    s4 -. "lexical.is_absolute(data not statically known)" .-> s9
    s4 -. "Path.cwd(data not statically known)" .-> s10
    s4 -. "Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(absolute.anchor)" .-> s11
    s4 -. "list(...)" .-> s12
    b0["mutation pending_parts.pop"]
    s4 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s4 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `governance_lock` | `wiki_dir: str \| Path`, `_lock_filename: str` | `GOVERNANCE_LOCK_FILENAME`, `os`, `os`, `os`, `sys`, `sys`, `GOVERNANCE_FILENAME`, `sys` | - | - |
| `GovernanceError` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…ernance.py:governance_lock)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |
| `Path.cwd` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | - | - | - | - |
| `list` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| governance_lock | GovernanceError | 862 | `GovernanceError('lock', 'unknown mutation lock')` |
| governance_lock | Path (src/llm_wiki_cli/services…ernance.py:governance_lock) | 863 | `Path(wiki_dir)` |
| governance_lock | first_unsafe_path_component | 864 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd | 66 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 67 | `Path(absolute.anchor)` |
| first_unsafe_path_component | list | 68 | `list(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 59 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 60 |
| external_call | `first_unsafe_path_component` | `Path.cwd` | 66 |
| step_limit | `governance_lock` | `first 12 steps` | 0 |

## Behavior

This flow starts at `governance_lock` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
