# require_existing_file

**Entry point:** `require_existing_file` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_existing_file
    participant p1 as is_file
    p0-->>p1: is_file
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_existing_file"]
    s2["2. is_file"]
    s1 -. "path.is_file(data not statically known)" .-> s2
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_existing_file` | `path: Path`, `error: Exception` | - | - | `path` |
| `is_file` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_existing_file | is_file | 540 | `path.is_file(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_existing_file` | `path.is_file` | 540 |

## Behavior

This flow starts at `require_existing_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
