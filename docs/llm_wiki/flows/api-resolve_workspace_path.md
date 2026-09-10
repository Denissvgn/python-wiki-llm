# resolve_workspace_path

**Entry point:** `resolve_workspace_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolve_workspace_path
    participant p1 as workspace_root.resolve
    participant p2 as (…).resolve
    participant p3 as target.relative_to
    p0-->>p1: workspace_root.resolve
    p0-->>p2: (…).resolve
    p0-->>p3: target.relative_to
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. resolve_workspace_path"]
    s2["2. workspace_root.resolve"]
    s3["3. (…).resolve"]
    s4["4. target.relative_to"]
    s1 -. "workspace_root.resolve(data not statically known)" .-> s2
    s1 -. "(…).resolve(data not statically known)" .-> s3
    s1 -. "target.relative_to(resolved_root)" .-> s4
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `resolve_workspace_path` | `workspace_root: Path`, `relative: str`, `escape_error: Exception` | - | - | `target` |
| `workspace_root.resolve` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `target.relative_to` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| resolve_workspace_path | workspace_root.resolve | 484 | `workspace_root.resolve(data not statically known)` |
| resolve_workspace_path | (…).resolve | 485 | `(resolved_root / relative).resolve(data not statically known)` |
| resolve_workspace_path | target.relative_to | 487 | `target.relative_to(resolved_root)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `resolve_workspace_path` | `workspace_root.resolve` | 484 |
| unresolved_call | `resolve_workspace_path` | `(resolved_root / relative).resolve` | 485 |
| unresolved_call | `resolve_workspace_path` | `target.relative_to` | 487 |

## Behavior

This flow starts at `resolve_workspace_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
