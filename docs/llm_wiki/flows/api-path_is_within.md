# path_is_within

**Entry point:** `path_is_within` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as path_is_within
    participant p1 as relative_to
    p0-->>p1: relative_to
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. path_is_within"]
    s2["2. relative_to"]
    s1 -. "path.relative_to(root)" .-> s2
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `path_is_within` | `path: Path`, `root: Path` | - | - | `False`, `True` |
| `relative_to` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| path_is_within | relative_to | 432 | `path.relative_to(root)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `path_is_within` | `path.relative_to` | 432 |

## Behavior

This flow starts at `path_is_within` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
