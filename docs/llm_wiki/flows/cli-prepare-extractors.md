# prepare-extractors

**Entry point:** `run` (`cli`)
**Source:** [prepare_extractors_cmd](../modules/prepare_extractors_cmd.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [filesystem_guard](../modules/filesystem_guard.md), and 5 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [prepare_extractors_cmd](../modules/prepare_extractors_cmd.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as _dedupe_languages
    participant p3 as set
    participant p4 as append
    participant p5 as add
    participant p6 as bool
    participant p7 as validate_source_root
    participant p8 as validate_path
    participant p9 as PathValidationError
    participant p10 as resolve
    participant p11 as cwd
    participant p12 as relative_to
    participant p13 as expanduser
    participant p14 as Path
    participant p15 as is_absolute
    participant p16 as is_dir
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0->>p2: _dedupe_languages
    p2-->>p3: set
    p2-->>p4: append
    p2-->>p5: add
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p6: bool
    p0-->>p1: getattr
    p0-->>p6: bool
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0->>p7: validate_source_root
    p7->>p8: validate_path
    p8->>p9: PathValidationError
    p8-->>p10: resolve
    p8-->>p11: cwd
    p8-->>p10: resolve
    p8-->>p11: cwd
    p8-->>p12: relative_to
    p8->>p9: PathValidationError
    p7-->>p13: expanduser
    p7-->>p14: Path
    p7-->>p15: is_absolute
    p7-->>p11: cwd
    p7-->>p10: resolve
    p7->>p9: PathValidationError
    p7-->>p16: is_dir
    p7->>p9: PathValidationError
```

> Call sequence diagram shows 30 of 870 interactions; 840 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. _dedupe_languages"]
    s5["5. set"]
    s6["6. append"]
    s7["7. add"]
    s8["8. getattr"]
    s9["9. getattr"]
    s10["10. bool"]
    s11["11. getattr"]
    s12["12. bool"]
    s1 -. "getattr(args, 'src_dir', '.')" .-> s2
    s1 -. "getattr(args, 'cache_dir', None)" .-> s3
    s1 -->|"_dedupe_languages(getattr(...))"| s4
    s4 -. "set(data not statically known)" .-> s5
    s4 -. "result.append(value)" .-> s6
    s4 -. "seen.add(value)" .-> s7
    s1 -. "getattr(args, 'language', None)" .-> s8
    s1 -. "getattr(args, 'source_selection', None)" .-> s9
    s1 -. "bool(getattr(...))" .-> s10
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s11
    s1 -. "bool(getattr(...))" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    b6["mutation result.append"]
    s4 -. "mutation result.append" .-> b6
    b7["mutation seen.add"]
    s4 -. "mutation seen.add" .-> b7
    click s1 "../modules/prepare_extractors_cmd.md"
    click s4 "../modules/prepare_extractors_cmd.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `sys`, `sys`, `sys` | - | `none`, `none` |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `_dedupe_languages` | `values: list[str] \| None` | - | - | `[...]`, `result` |
| `set` | - | - | - | - |
| `append` | - | - | - | - |
| `add` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 75 | `getattr(args, 'src_dir', '.')` |
| run | getattr | 76 | `getattr(args, 'cache_dir', None)` |
| run | _dedupe_languages | 77 | `_dedupe_languages(getattr(...))` |
| _dedupe_languages | set | 24 | `set(data not statically known)` |
| _dedupe_languages | append | 28 | `result.append(value)` |
| _dedupe_languages | add | 29 | `seen.add(value)` |
| run | getattr | 77 | `getattr(args, 'language', None)` |
| run | getattr | 78 | `getattr(args, 'source_selection', None)` |
| run | bool | 79 | `bool(getattr(...))` |
| run | getattr | 79 | `getattr(args, 'allow_external_src', False)` |
| run | bool | 80 | `bool(getattr(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 89 |
| output | `print` | `run` | 102 |
| output | `print` | `run` | 117 |
| output | `print` | `run` | 128 |
| output | `print` | `run` | 134 |
| output | `print` | `run` | 137 |
| mutation | `result.append` | `_dedupe_languages` | 28 |
| mutation | `seen.add` | `_dedupe_languages` | 29 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 75 |
| unresolved_call | `run` | `getattr` | 76 |
| unresolved_call | `run` | `getattr` | 77 |
| unresolved_call | `run` | `getattr` | 78 |
| unresolved_call | `run` | `getattr` | 79 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
