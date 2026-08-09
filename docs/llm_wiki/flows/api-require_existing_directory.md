# require_existing_directory

**Entry point:** `require_existing_directory` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_existing_directory
    participant p1 as exists
    participant p2 as is_dir
    p0-->>p1: exists
    p0-->>p2: is_dir
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_existing_directory"]
    s2["2. exists"]
    s3["3. is_dir"]
    s1 -. "path.exists(data not statically known)" .-> s2
    s1 -. "path.is_dir(data not statically known)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_existing_directory` | `path: Path`, `error: Exception` | - | - | - |
| `exists` | - | - | - | - |
| `is_dir` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_existing_directory | exists | 533 | `path.exists(data not statically known)` |
| require_existing_directory | is_dir | 533 | `path.is_dir(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_existing_directory` | `path.exists` | 533 |
| unresolved_call | `require_existing_directory` | `path.is_dir` | 533 |

## Behavior

This flow starts at `require_existing_directory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
