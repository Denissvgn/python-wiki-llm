# get_status

**Entry point:** `get_status` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_status
    p0-->>p0: get_status
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_status"]
    s2["2. get_status"]
    s1 -. "service.get_status(data not statically known)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_status` | - | - | - | `service.get_status(...)` |
| `get_status` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_status | get_status | 1303 | `service.get_status(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_status` | `service.get_status` | 1303 |

## Behavior

This flow starts at `get_status` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
