# require_safe_wiki_scaffold

**Entry point:** `require_safe_wiki_scaffold` (`api`)
**Source:** [wiki_lifecycle](../modules/wiki_lifecycle.md)
**Modules touched:** [io](../modules/io.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_safe_wiki_scaffold
    participant p1 as Path
    participant p2 as tuple
    participant p3 as iter_directory_kinds
    participant p4 as first_unsafe_path_component
    participant p5 as fspath
    participant p6 as abspath
    participant p7 as is_absolute
    participant p8 as cwd
    participant p9 as list
    participant p10 as pop
    participant p11 as lstat
    participant p12 as getattr
    participant p13 as S_ISLNK
    participant p14 as bool
    participant p15 as trusted_symlink_owner
    participant p16 as callable
    participant p17 as readlink
    p0-->>p1: Path
    p0-->>p2: tuple
    p0->>p3: iter_directory_kinds
    p3-->>p2: tuple
    p0-->>p2: tuple
    p0->>p4: first_unsafe_path_component
    p4-->>p1: Path
    p4-->>p5: fspath
    p4-->>p1: Path
    p4-->>p6: abspath
    p4-->>p7: is_absolute
    p4-->>p8: cwd
    p4-->>p1: Path
    p4-->>p9: list
    p4-->>p10: pop
    p4-->>p11: lstat
    p4-->>p12: getattr
    p4-->>p12: getattr
    p4-->>p13: S_ISLNK
    p4-->>p14: bool
    p4-->>p14: bool
    p4-->>p12: getattr
    p4-->>p15: trusted_symlink_owner
    p4-->>p16: callable
    p4-->>p12: getattr
    p4-->>p1: Path
    p4-->>p1: Path
    p4-->>p17: readlink
    p4-->>p7: is_absolute
    p4-->>p1: Path
```

> Call sequence diagram shows 30 of 38 interactions; 8 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_safe_wiki_scaffold"]
    s2["2. Path"]
    s3["3. tuple"]
    s4["4. iter_directory_kinds"]
    s5["5. tuple"]
    s6["6. tuple"]
    s7["7. first_unsafe_path_component"]
    s8["8. Path"]
    s9["9. fspath"]
    s10["10. Path"]
    s11["11. abspath"]
    s12["12. is_absolute"]
    s1 -. "Path(wiki_dir)" .-> s2
    s1 -. "tuple(...)" .-> s3
    s1 -->|"iter_directory_kinds(data not statically known)"| s4
    s4 -. "tuple(...)" .-> s5
    s1 -. "tuple(...)" .-> s6
    s1 -->|"first_unsafe_path_component(path)"| s7
    s7 -. "Path(os.fspath(...))" .-> s8
    s7 -. "os.fspath(path)" .-> s9
    s7 -. "Path(os.path.abspath(...))" .-> s10
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
| `Path` | - | - | - | - |
| `tuple` | - | - | - | - |
| `iter_directory_kinds` | - | `_PAGE_KINDS` | - | `tuple(...)` |
| `tuple` | - | - | - | - |
| `tuple` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path` | - | - | - | - |
| `fspath` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `is_absolute` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_safe_wiki_scaffold | Path | 43 | `Path(wiki_dir)` |
| require_safe_wiki_scaffold | tuple | 44 | `tuple(...)` |
| require_safe_wiki_scaffold | iter_directory_kinds | 46 | `iter_directory_kinds(data not statically known)` |
| iter_directory_kinds | tuple | 224 | `tuple(...)` |
| require_safe_wiki_scaffold | tuple | 49 | `tuple(...)` |
| require_safe_wiki_scaffold | first_unsafe_path_component | 54 | `first_unsafe_path_component(path)` |
| first_unsafe_path_component | Path | 50 | `Path(os.fspath(...))` |
| first_unsafe_path_component | fspath | 50 | `os.fspath(path)` |
| first_unsafe_path_component | Path | 58 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | abspath | 58 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | is_absolute | 59 | `lexical.is_absolute(data not statically known)` |

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
