# require_int

**Entry point:** `require_int` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_int
    participant p1 as isinstance
    p0-->>p1: isinstance
    p0-->>p1: isinstance
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_int"]
    s2["2. isinstance"]
    s3["3. isinstance"]
    s1 -. "isinstance(value, bool)" .-> s2
    s1 -. "isinstance(value, int)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_int` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_int | isinstance | 780 | `isinstance(value, bool)` |
| require_int | isinstance | 780 | `isinstance(value, int)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_int` | `isinstance` | 780 |

## Behavior

This flow starts at `require_int` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
