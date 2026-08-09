# require_bounded_int

**Entry point:** `require_bounded_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_bounded_int
    participant p1 as require_int
    participant p2 as isinstance
    p0->>p1: require_int
    p1-->>p2: isinstance
    p1-->>p2: isinstance
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_bounded_int"]
    s2["2. require_int"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s1 -->|"require_int(value, error=invalid_error)"| s2
    s2 -. "isinstance(value, bool)" .-> s3
    s2 -. "isinstance(value, int)" .-> s4
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_bounded_int` | `value: object`, `minimum: int`, `maximum: int`, `invalid_error: Exception`, `bounds_error: Exception \| None` | - | - | `parsed` |
| `require_int` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_bounded_int | require_int | 840 | `require_int(value, error=invalid_error)` |
| require_int | isinstance | 780 | `isinstance(value, bool)` |
| require_int | isinstance | 780 | `isinstance(value, int)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_int` | `isinstance` | 780 |

## Behavior

This flow starts at `require_bounded_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
