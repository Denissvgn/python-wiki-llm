# require_positive_int

**Entry point:** `require_positive_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_positive_int
    participant p1 as require_nonnegative_int
    participant p2 as require_int
    participant p3 as isinstance
    p0->>p1: require_nonnegative_int
    p1->>p2: require_int
    p2-->>p3: isinstance
    p2-->>p3: isinstance
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
| require_positive_int | require_nonnegative_int | 810 | `require_nonnegative_int(value, error=invalid_error)` |
| require_nonnegative_int | require_int | 788 | `require_int(value, error=error)` |
| require_int | isinstance | 780 | `isinstance(value, bool)` |
| require_int | isinstance | 780 | `isinstance(value, int)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_int` | `isinstance` | 780 |

## Behavior

This flow starts at `require_positive_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
