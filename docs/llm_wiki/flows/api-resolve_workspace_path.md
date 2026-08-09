# resolve_workspace_path

**Entry point:** `resolve_workspace_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolve_workspace_path
    participant p1 as resolve
    participant p2 as relative_to
    p0-->>p1: resolve
    p0-->>p1: resolve
    p0-->>p2: relative_to
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. resolve_workspace_path"]
    s2["2. resolve"]
    s3["3. resolve"]
    s4["4. relative_to"]
    s1 -. "workspace_root.resolve(data not statically known)" .-> s2
    s1 -. "(resolved_root / relative).resolve(data not statically known)" .-> s3
    s1 -. "target.relative_to(resolved_root)" .-> s4
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `resolve_workspace_path` | `workspace_root: Path`, `relative: str`, `escape_error: Exception` | - | - | `target` |
| `resolve` | - | - | - | - |
| `resolve` | - | - | - | - |
| `relative_to` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| resolve_workspace_path | resolve | 484 | `workspace_root.resolve(data not statically known)` |
| resolve_workspace_path | resolve | 485 | `(resolved_root / relative).resolve(data not statically known)` |
| resolve_workspace_path | relative_to | 487 | `target.relative_to(resolved_root)` |

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
