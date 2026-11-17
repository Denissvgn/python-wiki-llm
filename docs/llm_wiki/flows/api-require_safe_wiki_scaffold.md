# require_safe_wiki_scaffold

**Entry point:** `require_safe_wiki_scaffold` (`api`)
**Source:** [wiki_lifecycle](../modules/wiki_lifecycle.md)
**Modules touched:** [host](../modules/host.md), [io](../modules/io.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_safe_wiki_scaffold
    participant p1 as first_unsafe_path_component
    participant p2 as iter_directory_kinds
    participant p3 as WikiScaffoldPathError
    participant p4 as current_host
    participant p5 as Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    participant p6 as directory.exists
    participant p7 as tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)
    participant p8 as directory.is_dir
    participant p9 as path.exists
    participant p10 as path.is_file
    participant p11 as tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds)
    participant p12 as Path (src/llm_wiki_cli/services…irst_unsafe_path_component)
    participant p13 as os.fspath
    participant p14 as os.path.abspath
    participant p15 as lexical.is_absolute
    participant p16 as current_host().cwd
    participant p17 as list
    participant p18 as pending_parts.pop
    participant p19 as current.lstat
    participant p20 as getattr
    participant p21 as stat.S_ISLNK
    participant p22 as bool
    participant p23 as trusted_symlink_owner
    participant p24 as callable
    p0->>p1: first_unsafe_path_component
    p0->>p2: iter_directory_kinds
    p0->>p3: WikiScaffoldPathError
    p1->>p4: current_host
    p0-->>p5: Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)(wiki_dir)
    p0-->>p6: directory.exists
    p0-->>p7: tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)(...)
    p0-->>p7: tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)(...)
    p0-->>p8: directory.is_dir
    p0-->>p9: path.exists
    p0-->>p10: path.is_file
    p2-->>p11: tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds)(...)
    p1-->>p12: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.fspath(...))
    p1-->>p13: os.fspath(path)
    p1-->>p12: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(os.path.abspath(...))
    p1-->>p14: os.path.abspath(lexical)
    p1-->>p15: lexical.is_absolute
    p1-->>p16: current_host().cwd
    p1-->>p12: Path (src/llm_wiki_cli/services…irst_unsafe_path_component)(absolute.anchor)
    p1-->>p17: list(...)
    p1-->>p18: pending_parts.pop(0)
    p1-->>p19: current.lstat
    p1-->>p20: getattr(metadata, 'st_file_attributes', 0)
    p1-->>p20: getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    p1-->>p21: stat.S_ISLNK(metadata.st_mode)
    p1-->>p22: bool(reparse_flag)
    p1-->>p22: bool(...)
    p1-->>p20: getattr(metadata, 'st_uid', None)
    p1-->>p23: trusted_symlink_owner(current)
    p1-->>p24: callable(getattr(...))
```

> Call sequence diagram shows 30 of 40 interactions; 10 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 17 of 23 (6 omitted); unresolved 9 of 11 (2 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/host.py:current_host` | 14 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | - | external | 6 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:require_safe_wiki_scaffold` | 1 | [src/llm_wiki_cli/services/wiki_lifecycle.py](../modules/wiki_lifecycle.md) | internal | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 7; effect analysis evaluated: 4, partial: 0, unavailable: 3. Counts include steps omitted from the displayed trace.

Collector observations for 4 source steps with known totals: observed: 19, emitted: 19, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `require_safe_wiki_scaffold` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `iter_directory_kinds` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `first_unsafe_path_component` | `available` | `evaluated` | `available` | `14` | `14` | `0` |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.fspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_cli/services…irst_unsafe_path_component)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.path.abspath` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `lexical.is_absolute` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. require_safe_wiki_scaffold"]
    s2["2. Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold)"]
    s3["3. tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold)"]
    s4["4. iter_directory_kinds"]
    s5["5. tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds)"]
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
    s4 -. "tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds)(...)" .-> s5
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
| `tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds)` | - | - | - | - |
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
| require_safe_wiki_scaffold | Path (src/llm_wiki_cli/services…require_safe_wiki_scaffold) | 44 | `Path(wiki_dir)` |
| require_safe_wiki_scaffold | tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold) | 45 | `tuple(...)` |
| require_safe_wiki_scaffold | iter_directory_kinds | 47 | `iter_directory_kinds(data not statically known)` |
| iter_directory_kinds | tuple (src/llm_wiki_engine/wiki_…ce.py:iter_directory_kinds) | 224 | `tuple(...)` |
| require_safe_wiki_scaffold | tuple (src/llm_wiki_cli/services…require_safe_wiki_scaffold) | 50 | `tuple(...)` |
| require_safe_wiki_scaffold | first_unsafe_path_component | 55 | `first_unsafe_path_component(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 52 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath | 52 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…irst_unsafe_path_component) | 60 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath | 60 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 61 | `lexical.is_absolute(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 72 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 52 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 60 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 61 |
| step_limit | `require_safe_wiki_scaffold` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_safe_wiki_scaffold` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
