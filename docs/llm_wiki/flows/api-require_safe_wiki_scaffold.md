# require_safe_wiki_scaffold

**Entry point:** `require_safe_wiki_scaffold` (`api`)
**Source:** [wiki_lifecycle](../modules/wiki_lifecycle.md)
**Modules touched:** [io](../modules/io.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_safe_wiki_scaffold
    participant p1 as Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    participant p2 as tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    participant p3 as iter_directory_kinds
    participant p4 as tuple (src/llm_wiki_cli/services…ce.py:iter_directory_kinds)
    participant p5 as first_unsafe_path_component
    participant p6 as Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    participant p7 as os.fspath
    participant p8 as os.path.abspath
    participant p9 as lexical.is_absolute
    participant p10 as Path.cwd
    participant p11 as list
    participant p12 as pending_parts.pop
    participant p13 as current.lstat
    participant p14 as getattr
    participant p15 as stat.S_ISLNK
    participant p16 as bool
    participant p17 as trusted_symlink_owner
    participant p18 as callable
    participant p19 as os.readlink
    participant p20 as link_target.is_absolute
    p0-->>p1: Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    p0-->>p2: tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    p0->>p3: iter_directory_kinds
    p3-->>p4: tuple (src/llm_wiki_cli/services…ce.py:iter_directory_kinds)
    p0-->>p2: tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    p0->>p5: first_unsafe_path_component
    p5-->>p6: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p5-->>p7: os.fspath
    p5-->>p6: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p5-->>p8: os.path.abspath
    p5-->>p9: lexical.is_absolute
    p5-->>p10: Path.cwd
    p5-->>p6: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p5-->>p11: list
    p5-->>p12: pending_parts.pop
    p5-->>p13: current.lstat
    p5-->>p14: getattr
    p5-->>p14: getattr
    p5-->>p15: stat.S_ISLNK
    p5-->>p16: bool
    p5-->>p16: bool
    p5-->>p14: getattr
    p5-->>p17: trusted_symlink_owner
    p5-->>p18: callable
    p5-->>p14: getattr
    p5-->>p6: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p5-->>p6: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    p5-->>p19: os.readlink
    p5-->>p20: link_target.is_absolute
    p5-->>p6: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
```

> Call sequence diagram shows 30 of 38 interactions; 8 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_safe_wiki_scaffold"]
    s2["2. Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)"]
    s3["3. tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)"]
    s4["4. iter_directory_kinds"]
    s5["5. tuple (src/llm_wiki_cli/services…ce.py:iter_directory_kinds)"]
    s6["6. tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)"]
    s7["7. first_unsafe_path_component"]
    s8["8. Path (src/llm_wiki_cli/services…irst_unsafe_path_component)"]
    s9["9. os.fspath"]
    s10["10. Path (src/llm_wiki_cli/services…irst_unsafe_path_component)"]
    s11["11. os.path.abspath"]
    s12["12. lexical.is_absolute"]
    s1 -. "Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)(wiki_dir)" .-> s2
    s1 -. "tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)(...)" .-> s3
    s1 -->|"iter_directory_kinds(data not statically known)"| s4
    s4 -. "tuple (src/llm_wiki_cli/services…ce.py:iter_directory_kinds)(...)" .-> s5
    s1 -. "tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)(...)" .-> s6
    s1 -->|"first_unsafe_path_component(path)"| s7
    s7 -. "Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.fspath(...))" .-> s8
    s7 -. "os.fspath(path)" .-> s9
    s7 -. "Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.path.abspath(...))" .-> s10
    s7 -. "os.path.abspath(lexical)" .-> s11
    s7 -. "lexical.is_absolute(data not statically known)" .-> s12
    b0["mutation pending_parts.pop"]
    s7 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/wiki_lifecycle.md"
    click s4 "../modules/wiki_surface.md"
    click s7 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_safe_wiki_scaffold` | `wiki_dir: Union[str, Path]` | - | - | - |
| `Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)` | - | - | - | - |
| `iter_directory_kinds` | - | `_PAGE_KINDS` | - | `tuple(...)` |
| `tuple (src/llm_wiki_cli/services…ce.py:iter_directory_kinds)` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_safe_wiki_scaffold | Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold) | 43 | `Path(wiki_dir)` |
| require_safe_wiki_scaffold | tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold) | 44 | `tuple(...)` |
| require_safe_wiki_scaffold | iter_directory_kinds | 46 | `iter_directory_kinds(data not statically known)` |
| iter_directory_kinds | tuple (src/llm_wiki_cli/services…ce.py:iter_directory_kinds) | 224 | `tuple(...)` |
| require_safe_wiki_scaffold | tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold) | 49 | `tuple(...)` |
| require_safe_wiki_scaffold | first_unsafe_path_component | 54 | `first_unsafe_path_component(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 50 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 50 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 58 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 58 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 59 | `lexical.is_absolute(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 70 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 50 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 58 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 59 |
| step_limit | `require_safe_wiki_scaffold` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_safe_wiki_scaffold` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
