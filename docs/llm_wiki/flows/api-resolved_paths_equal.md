# resolved_paths_equal

**Entry point:** `resolved_paths_equal` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolved_paths_equal
    participant p1 as resolve
    participant p2 as Path
    p0-->>p1: resolve
    p0-->>p2: Path
    p0-->>p1: resolve
    p0-->>p2: Path
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. resolved_paths_equal"]
    s2["2. resolve"]
    s3["3. Path"]
    s4["4. resolve"]
    s5["5. Path"]
    s1 -. "Path(left).resolve(data not statically known)" .-> s2
    s1 -. "Path(left)" .-> s3
    s1 -. "Path(left).resolve(data not statically known)" .-> s4
    s1 -. "Path(right)" .-> s5
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `resolved_paths_equal` | `left: str \| Path`, `right: str \| Path` | - | - | `...` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| resolved_paths_equal | resolve | 450 | `Path(left).resolve(data not statically known)` |
| resolved_paths_equal | Path | 450 | `Path(left)` |
| resolved_paths_equal | resolve | 450 | `Path(left).resolve(data not statically known)` |
| resolved_paths_equal | Path | 450 | `Path(right)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `resolved_paths_equal` | `Path(left).resolve` | 450 |
| unresolved_call | `resolved_paths_equal` | `Path(right).resolve` | 450 |

## Behavior

This flow starts at `resolved_paths_equal` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
