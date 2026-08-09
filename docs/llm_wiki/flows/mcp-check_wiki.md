# check_wiki

**Entry point:** `check_wiki` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as check_wiki
    p0-->>p0: check_wiki
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. check_wiki"]
    s2["2. check_wiki"]
    s1 -. "service.check_wiki(strict=strict, format=format, knowledge_drift_report=knowledge_drift_report)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `check_wiki` | `strict: bool`, `format: str`, `knowledge_drift_report: bool` | - | - | `service.check_wiki(...)` |
| `check_wiki` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| check_wiki | check_wiki | 1070 | `service.check_wiki(strict=strict, format=format, knowledge_drift_report=knowledge_drift_report)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `check_wiki` | `service.check_wiki` | 1070 |

## Behavior

This flow starts at `check_wiki` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
