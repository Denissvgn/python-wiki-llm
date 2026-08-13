# related_concepts

**Entry point:** `related_concepts` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as related_concepts
    p0-->>p0: related_concepts
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. related_concepts"]
    s2["2. related_concepts"]
    s1 -. "service.related_concepts(locator_or_exact_route, direction=direction, kinds=kinds, limit=limit)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `related_concepts` | `locator_or_exact_route: str`, `direction: str`, `kinds: list[str] \| None`, `limit: int` | - | - | `service.related_concepts(...)` |
| `related_concepts` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| related_concepts | related_concepts | 1185 | `service.related_concepts(locator_or_exact_route, direction=direction, kinds=kinds, limit=limit)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `related_concepts` | `service.related_concepts` | 1185 |

## Behavior

This flow starts at `related_concepts` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
