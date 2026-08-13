# query_graph

**Entry point:** `query_graph` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as query_graph
    p0-->>p0: query_graph
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. query_graph"]
    s2["2. query_graph"]
    s1 -. "service.query_graph(query)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `query_graph` | `query: dict` | - | - | `service.query_graph(...)` |
| `query_graph` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| query_graph | query_graph | 1162 | `service.query_graph(query)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `query_graph` | `service.query_graph` | 1162 |

## Behavior

This flow starts at `query_graph` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
