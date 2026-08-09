# require_int_at_least

**Entry point:** `require_int_at_least` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_int_at_least
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
    s1["1. require_int_at_least"]
    s2["2. require_int"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s1 -->|"require_int(value, error=error)"| s2
    s2 -. "isinstance(value, bool)" .-> s3
    s2 -. "isinstance(value, int)" .-> s4
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_int_at_least` | `value: object`, `minimum: int`, `error: Exception` | - | - | `parsed` |
| `require_int` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_int_at_least | require_int | 824 | `require_int(value, error=error)` |
| require_int | isinstance | 780 | `isinstance(value, bool)` |
| require_int | isinstance | 780 | `isinstance(value, int)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_int` | `isinstance` | 780 |

## Behavior

This flow starts at `require_int_at_least` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
