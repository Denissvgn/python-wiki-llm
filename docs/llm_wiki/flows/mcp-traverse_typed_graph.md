# traverse_typed_graph

**Entry point:** `traverse_typed_graph` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as traverse_typed_graph
    p0-->>p0: traverse_typed_graph
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. traverse_typed_graph"]
    s2["2. traverse_typed_graph"]
    s1 -. "service.traverse_typed_graph(locator_or_exact_route, direction=direction, kinds=kinds, origins=origins, resolutions=resolutions, include_evidence=include_evide…" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `traverse_typed_graph` | `locator_or_exact_route: str`, `direction: str`, `kinds: list[str] \| None`, `origins: list[str] \| None`, `resolutions: list[str] \| None`, `include_evidence: bool`, `limit: int` | - | - | `service.traverse_typed_graph(...)` |
| `traverse_typed_graph` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| traverse_typed_graph | traverse_typed_graph | 1002 | `service.traverse_typed_graph(locator_or_exact_route, direction=direction, kinds=kinds, origins=origins, resolutions=resolutions, include_evidence=include_evidence, limit=limit)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `traverse_typed_graph` | `service.traverse_typed_graph` | 1002 |

## Behavior

This flow starts at `traverse_typed_graph` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
