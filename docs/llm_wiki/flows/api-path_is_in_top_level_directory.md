# path_is_in_top_level_directory

**Entry point:** `path_is_in_top_level_directory` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as path_is_in_top_level_directory
    participant p1 as path.relative_to
    participant p2 as path.resolve().relative_to
    participant p3 as path.resolve
    participant p4 as root.resolve
    p0-->>p1: path.relative_to(root)
    p0-->>p2: path.resolve().relative_to(root.resolve(...))
    p0-->>p3: path.resolve
    p0-->>p4: root.resolve
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 4 of 4 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 5, emitted: 5, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. path_is_in_top_level_directory"]
    s2["2. path.relative_to"]
    s3["3. path.resolve().relative_to"]
    s4["4. path.resolve"]
    s5["5. root.resolve"]
    s1 -. "path.relative_to(root)" .-> s2
    s1 -. "path.resolve().relative_to(root.resolve(...))" .-> s3
    s1 -. "path.resolve(data not statically known)" .-> s4
    s1 -. "path.resolve(data not statically known)" .-> s5
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `path_is_in_top_level_directory` | `path: Path`, `root: Path`, `directory: str` | - | - | `False`, `...` |
| `path.relative_to` | - | - | - | - |
| `path.resolve().relative_to` | - | - | - | - |
| `path.resolve` | - | - | - | - |
| `root.resolve` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| path_is_in_top_level_directory | path.relative_to | 510 | `path.relative_to(root)` |
| path_is_in_top_level_directory | path.resolve().relative_to | 513 | `path.resolve().relative_to(root.resolve(...))` |
| path_is_in_top_level_directory | path.resolve | 513 | `path.resolve(data not statically known)` |
| path_is_in_top_level_directory | root.resolve | 513 | `path.resolve(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `path_is_in_top_level_directory` | `path.relative_to` | 510 |
| unresolved_call | `path_is_in_top_level_directory` | `path.resolve().relative_to` | 513 |
| unresolved_call | `path_is_in_top_level_directory` | `path.resolve` | 513 |
| unresolved_call | `path_is_in_top_level_directory` | `root.resolve` | 513 |

## Behavior

This flow starts at `path_is_in_top_level_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
