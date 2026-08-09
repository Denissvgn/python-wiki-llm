# coerce_positive_int

**Entry point:** `coerce_positive_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as coerce_positive_int
    participant p1 as coerce_nonnegative_int
    participant p2 as int
    participant p3 as isinstance
    p0->>p1: coerce_nonnegative_int
    p1-->>p2: int
    p1-->>p3: isinstance
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
| coerce_positive_int | coerce_nonnegative_int | 898 | `coerce_nonnegative_int(value, error=error)` |
| coerce_nonnegative_int | int | 887 | `int(value)` |
| coerce_nonnegative_int | isinstance | 890 | `isinstance(value, bool)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `coerce_nonnegative_int` | `isinstance` | 890 |

## Behavior

This flow starts at `coerce_positive_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
