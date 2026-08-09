# nonnegative_int_or_none

**Entry point:** `nonnegative_int_or_none` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as nonnegative_int_or_none
    participant p1 as isinstance
    p0-->>p1: isinstance
    p0-->>p1: isinstance
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. nonnegative_int_or_none"]
    s2["2. isinstance"]
    s3["3. isinstance"]
    s1 -. "isinstance(value, bool)" .-> s2
    s1 -. "isinstance(value, int)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `nonnegative_int_or_none` | `value: object` | - | - | `None`, `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| nonnegative_int_or_none | isinstance | 797 | `isinstance(value, bool)` |
| nonnegative_int_or_none | isinstance | 797 | `isinstance(value, int)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `nonnegative_int_or_none` | `isinstance` | 797 |

## Behavior

This flow starts at `nonnegative_int_or_none` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
