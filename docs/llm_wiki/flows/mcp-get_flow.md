# get_flow

**Entry point:** `get_flow` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_flow
    p0-->>p0: get_flow
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_flow"]
    s2["2. get_flow"]
    s1 -. "service.get_flow(flow_id)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_flow` | `flow_id: str` | - | - | `service.get_flow(...)` |
| `get_flow` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_flow | get_flow | 943 | `service.get_flow(flow_id)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_flow` | `service.get_flow` | 943 |

## Behavior

This flow starts at `get_flow` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
