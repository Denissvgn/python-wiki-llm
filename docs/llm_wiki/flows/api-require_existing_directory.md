# require_existing_directory

**Entry point:** `require_existing_directory` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_existing_directory
    participant p1 as path.exists
    participant p2 as path.is_dir
    p0-->>p1: path.exists
    p0-->>p2: path.is_dir
```

> Call sequence diagram shows 2 of 2 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 2, emitted: 2, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_existing_directory"]
    s2["2. path.exists"]
    s3["3. path.is_dir"]
    s1 -. "path.exists(data not statically known)" .-> s2
    s1 -. "path.is_dir(data not statically known)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_existing_directory` | `path: Path`, `error: Exception` | - | - | - |
| `path.exists` | - | - | - | - |
| `path.is_dir` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_existing_directory | path.exists | 582 | `path.exists(data not statically known)` |
| require_existing_directory | path.is_dir | 582 | `path.is_dir(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_existing_directory` | `path.exists` | 582 |
| unresolved_call | `require_existing_directory` | `path.is_dir` | 582 |

## Behavior

This flow starts at `require_existing_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
