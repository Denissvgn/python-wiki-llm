# coerce_positive_int

**Entry point:** `coerce_positive_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as coerce_positive_int
    participant p1 as coerce_nonnegative_int
    participant p2 as int
    participant p3 as isinstance
    p0->>p1: coerce_nonnegative_int
    p1-->>p2: int(value)
    p1-->>p3: isinstance(value, bool)
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 6, emitted: 6, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. coerce_positive_int"]
    s2["2. coerce_nonnegative_int"]
    s3["3. int"]
    s4["4. isinstance"]
    s1 -->|"coerce_nonnegative_int(value, error=error)"| s2
    s2 -. "int(value)" .-> s3
    s2 -. "isinstance(value, bool)" .-> s4
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `coerce_positive_int` | `value: object`, `error: Exception` | - | - | `parsed` |
| `coerce_nonnegative_int` | `value: object`, `error: Exception` | - | - | `parsed` |
| `int` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| coerce_positive_int | coerce_nonnegative_int | 936 | `coerce_nonnegative_int(value, error=error)` |
| coerce_nonnegative_int | int | 925 | `int(value)` |
| coerce_nonnegative_int | isinstance | 928 | `isinstance(value, bool)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `coerce_nonnegative_int` | `isinstance` | 928 |

## Behavior

This flow starts at `coerce_positive_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
