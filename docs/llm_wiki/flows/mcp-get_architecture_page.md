# get_architecture_page

**Entry point:** `get_architecture_page` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_architecture_page
    p0-->>p0: get_architecture_page
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_architecture_page"]
    s2["2. get_architecture_page"]
    s1 -. "service.get_architecture_page(page)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_architecture_page` | `page: str` | - | - | `service.get_architecture_page(...)` |
| `get_architecture_page` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_architecture_page | get_architecture_page | 948 | `service.get_architecture_page(page)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_architecture_page` | `service.get_architecture_page` | 948 |

## Behavior

This flow starts at `get_architecture_page` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
