# get_context_packet

**Entry point:** `get_context_packet` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_context_packet
    p0-->>p0: get_context_packet
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_context_packet"]
    s2["2. get_context_packet"]
    s1 -. "service.get_context_packet(**=options)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_context_packet` | `budget_tokens: int`, `focus: list[str] \| None`, `format: str`, `filters: dict \| None`, `prefer_fresh: bool`, `if_packet_id: str \| None`, `knowledge_mode: KnowledgeMode \| None` | - | `options[...]` | `service.get_context_packet(...)` |
| `get_context_packet` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_context_packet | get_context_packet | 1285 | `service.get_context_packet(**=options)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_context_packet` | `service.get_context_packet` | 1285 |

## Behavior

This flow starts at `get_context_packet` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
