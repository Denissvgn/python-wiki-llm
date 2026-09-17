# governance_lock

**Entry point:** `governance_lock` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [io](../modules/io.md), [knowledge_governance](../modules/knowledge_governance.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as governance_lock
    participant p1 as GovernanceError
    participant p2 as Path (src/llm_wiki_cli/services…ernance.py:governance_lock)
    participant p3 as first_unsafe_path_component
    participant p4 as Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    participant p5 as os.fspath
    participant p6 as os.path.abspath
    participant p7 as lexical.is_absolute
    participant p8 as Path.cwd
    participant p9 as list
    participant p10 as pending_parts.pop
    participant p11 as current.lstat
    participant p12 as getattr (src/llm_wiki_cli/services…irst_unsafe_path_component)
    participant p13 as stat.S_ISLNK
    participant p14 as bool (src/llm_wiki_cli/services…irst_unsafe_path_component)
    participant p15 as trusted_symlink_owner
    participant p16 as callable
    participant p17 as os.readlink
    participant p18 as link_target.is_absolute
    participant p19 as _governance_lock_root
    p0->>p1: GovernanceError
    p0-->>p2: Path (src/llm_wiki_cli/services…ernance.py:governance_lock)
    p0->>p3: first_unsafe_path_component
    p3-->>p4: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p5: os.fspath
    p3-->>p4: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p6: os.path.abspath
    p3-->>p7: lexical.is_absolute
    p3-->>p8: Path.cwd
    p3-->>p4: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p9: list
    p3-->>p10: pending_parts.pop
    p3-->>p11: current.lstat
    p3-->>p12: getattr (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p12: getattr (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p13: stat.S_ISLNK
    p3-->>p14: bool (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p14: bool (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p12: getattr (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p15: trusted_symlink_owner
    p3-->>p16: callable
    p3-->>p12: getattr (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p4: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p4: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p17: os.readlink
    p3-->>p18: link_target.is_absolute
    p3-->>p4: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p3-->>p9: list
    p0->>p1: GovernanceError
    p0->>p19: _governance_lock_root
```

> Call sequence diagram shows 30 of 61 interactions; 31 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
| governance_lock | GovernanceError | 860 | `GovernanceError('lock', 'unknown mutation lock')` |
| governance_lock | Path (src/llm_wiki_cli/services…ernance.py:governance_lock) | 861 | `Path(wiki_dir)` |
| governance_lock | first_unsafe_path_component | 862 | `first_unsafe_path_component(root)` |
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
