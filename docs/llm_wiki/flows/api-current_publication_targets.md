# current_publication_targets

**Entry point:** `current_publication_targets` (`api`)
**Source:** [publication_targets](../modules/publication_targets.md)
**Modules touched:** [publication_targets](../modules/publication_targets.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as current_publication_targets
    participant p1 as _ACTIVE_TARGETS.get
    p0-->>p1: _ACTIVE_TARGETS.get
```

> Call sequence diagram shows 1 of 1 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 2, emitted: 2, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. current_publication_targets"]
    s2["2. _ACTIVE_TARGETS.get"]
    s1 -. "_ACTIVE_TARGETS.get(data not statically known)" .-> s2
    click s1 "../modules/publication_targets.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `current_publication_targets` | - | `DEFAULT_PUBLICATION_TARGETS` | - | `...` |
| `_ACTIVE_TARGETS.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| current_publication_targets | _ACTIVE_TARGETS.get | 178 | `_ACTIVE_TARGETS.get(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `current_publication_targets` | `_ACTIVE_TARGETS.get` | 178 |

## Behavior

This flow starts at `current_publication_targets` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
