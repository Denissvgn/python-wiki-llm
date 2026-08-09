# get_concept

**Entry point:** `get_concept` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_concept
    p0-->>p0: get_concept
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_concept"]
    s2["2. get_concept"]
    s1 -. "service.get_concept(locator_or_exact_route, limit=limit)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_concept` | `locator_or_exact_route: str`, `limit: int` | - | - | `service.get_concept(...)` |
| `get_concept` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_concept | get_concept | 961 | `service.get_concept(locator_or_exact_route, limit=limit)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_concept` | `service.get_concept` | 961 |

## Behavior

This flow starts at `get_concept` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
