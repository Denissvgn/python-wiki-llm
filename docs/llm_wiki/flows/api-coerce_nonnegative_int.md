# coerce_nonnegative_int

**Entry point:** `coerce_nonnegative_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as coerce_nonnegative_int
    participant p1 as int
    participant p2 as isinstance
    p0-->>p1: int
    p0-->>p2: isinstance
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. coerce_nonnegative_int"]
    s2["2. int"]
    s3["3. isinstance"]
    s1 -. "int(value)" .-> s2
    s1 -. "isinstance(value, bool)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `coerce_nonnegative_int` | `value: object`, `error: Exception` | - | - | `parsed` |
| `int` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| coerce_nonnegative_int | int | 887 | `int(value)` |
| coerce_nonnegative_int | isinstance | 890 | `isinstance(value, bool)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `coerce_nonnegative_int` | `isinstance` | 890 |

## Behavior

This flow starts at `coerce_nonnegative_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
