# require_positive_int

**Entry point:** `require_positive_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_positive_int
    participant p1 as require_nonnegative_int
    participant p2 as require_int
    participant p3 as isinstance
    p0->>p1: require_nonnegative_int
    p1->>p2: require_int
    p2-->>p3: isinstance(value, bool)
    p2-->>p3: isinstance(value, int)
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 3, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 10, emitted: 10, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_positive_int"]
    s2["2. require_nonnegative_int"]
    s3["3. require_int"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s1 -->|"require_nonnegative_int(value, error=invalid_error)"| s2
    s2 -->|"require_int(value, error=error)"| s3
    s3 -. "isinstance(value, bool)" .-> s4
    s3 -. "isinstance(value, int)" .-> s5
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s3 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_positive_int` | `value: object`, `invalid_error: Exception`, `zero_error: Exception \| None` | - | - | `parsed` |
| `require_nonnegative_int` | `value: object`, `error: Exception` | - | - | `parsed` |
| `require_int` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_positive_int | require_nonnegative_int | 856 | `require_nonnegative_int(value, error=invalid_error)` |
| require_nonnegative_int | require_int | 834 | `require_int(value, error=error)` |
| require_int | isinstance | 826 | `isinstance(value, bool)` |
| require_int | isinstance | 826 | `isinstance(value, int)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_int` | `isinstance` | 826 |

## Behavior

This flow starts at `require_positive_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
