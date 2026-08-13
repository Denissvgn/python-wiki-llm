# get_module

**Entry point:** `get_module` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_module
    p0-->>p0: get_module
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. get_module"]
    s2["2. get_module"]
    s1 -. "service.get_module(module_id_or_source_path)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_module` | `module_id_or_source_path: str` | - | - | `service.get_module(...)` |
| `get_module` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_module | get_module | 1147 | `service.get_module(module_id_or_source_path)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_module` | `service.get_module` | 1147 |

## Behavior

This flow starts at `get_module` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
