# check_wiki

**Entry point:** `check_wiki` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as check_wiki
    participant p1 as service.check_wiki
    p0-->>p1: service.check_wiki(strict=strict, format=format, knowledge_drift_report=knowledge_drift_report)
```

> Call sequence diagram shows 1 of 1 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. check_wiki"]
    s2["2. service.check_wiki"]
    s1 -. "service.check_wiki(strict=strict, format=format, knowledge_drift_report=knowledge_drift_report)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `check_wiki` | `strict: bool`, `format: str`, `knowledge_drift_report: bool` | - | - | `service.check_wiki(...)` |
| `service.check_wiki` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| check_wiki | service.check_wiki | 1543 | `service.check_wiki(strict=strict, format=format, knowledge_drift_report=knowledge_drift_report)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `check_wiki` | `service.check_wiki` | 1543 |

## Behavior

This flow starts at `check_wiki` and is classified as `mcp`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
