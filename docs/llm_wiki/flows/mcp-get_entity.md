# get_entity

**Entry point:** `get_entity` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_entity
    p0-->>p0: get_entity
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_entity"]
    s2["2. get_entity"]
    s1 -. "service.get_entity(entity_id)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_entity` | `entity_id: str` | - | - | `service.get_entity(...)` |
| `get_entity` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_entity | get_entity | 1142 | `service.get_entity(entity_id)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_entity` | `service.get_entity` | 1142 |

## Behavior

This flow starts at `get_entity` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
