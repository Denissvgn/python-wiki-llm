# publication_target

**Entry point:** `publication_target` (`api`)
**Source:** [publication_targets](../modules/publication_targets.md)
**Modules touched:** [publication_targets](../modules/publication_targets.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as publication_target
    participant p1 as current_publication_targets().get
    participant p2 as current_publication_targets
    participant p3 as _ACTIVE_TARGETS.get
    p0-->>p1: current_publication_targets().get(kind)
    p0->>p2: current_publication_targets
    p2-->>p3: _ACTIVE_TARGETS.get
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 4, emitted: 4, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. publication_target"]
    s2["2. current_publication_targets().get"]
    s3["3. current_publication_targets"]
    s4["4. _ACTIVE_TARGETS.get"]
    s1 -. "current_publication_targets().get(kind)" .-> s2
    s1 -->|"current_publication_targets(data not statically known)"| s3
    s3 -. "_ACTIVE_TARGETS.get(data not statically known)" .-> s4
    click s1 "../modules/publication_targets.md"
    click s3 "../modules/publication_targets.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `publication_target` | `kind: str` | - | - | `...` |
| `current_publication_targets().get` | - | - | - | - |
| `current_publication_targets` | - | `DEFAULT_PUBLICATION_TARGETS` | - | `...` |
| `_ACTIVE_TARGETS.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| publication_target | current_publication_targets().get | 183 | `current_publication_targets().get(kind)` |
| publication_target | current_publication_targets | 183 | `current_publication_targets(data not statically known)` |
| current_publication_targets | _ACTIVE_TARGETS.get | 178 | `_ACTIVE_TARGETS.get(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `publication_target` | `current_publication_targets().get` | 183 |
| unresolved_call | `current_publication_targets` | `_ACTIVE_TARGETS.get` | 178 |

## Behavior

This flow starts at `publication_target` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
