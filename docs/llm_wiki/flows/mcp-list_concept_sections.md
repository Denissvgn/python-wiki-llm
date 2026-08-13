# list_concept_sections

**Entry point:** `list_concept_sections` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as list_concept_sections
    p0-->>p0: list_concept_sections
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. list_concept_sections"]
    s2["2. list_concept_sections"]
    s1 -. "service.list_concept_sections(locator_or_exact_route, ownership=ownership, limit=limit)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `list_concept_sections` | `locator_or_exact_route: str`, `ownership: str \| None`, `limit: int` | - | - | `service.list_concept_sections(...)` |
| `list_concept_sections` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| list_concept_sections | list_concept_sections | 1199 | `service.list_concept_sections(locator_or_exact_route, ownership=ownership, limit=limit)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `list_concept_sections` | `service.list_concept_sections` | 1199 |

## Behavior

This flow starts at `list_concept_sections` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
