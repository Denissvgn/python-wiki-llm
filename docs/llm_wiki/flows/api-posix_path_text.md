# posix_path_text

**Entry point:** `posix_path_text` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as posix_path_text
    participant p1 as replace
    participant p2 as str
    p0-->>p1: replace
    p0-->>p2: str
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. posix_path_text"]
    s2["2. replace"]
    s3["3. str"]
    s1 -. "str(value).replace('\\', '/')" .-> s2
    s1 -. "str(value)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `posix_path_text` | `value: object` | - | - | `...` |
| `replace` | - | - | - | - |
| `str` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| posix_path_text | replace | 473 | `str(value).replace('\\', '/')` |
| posix_path_text | str | 473 | `str(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `posix_path_text` | `str(value).replace` | 473 |

## Behavior

This flow starts at `posix_path_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
