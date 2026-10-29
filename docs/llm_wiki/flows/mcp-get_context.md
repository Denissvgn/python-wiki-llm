# get_context

**Entry point:** `get_context` (`mcp`)
**Source:** [mcp_server](../modules/mcp_server.md)
**Modules touched:** [mcp_server](../modules/mcp_server.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_context
    participant p1 as service.get_context
    p0-->>p1: service.get_context(**=options)
```

> Call sequence diagram shows 1 of 1 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 8, emitted: 8, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. get_context"]
    s2["2. service.get_context"]
    s1 -. "service.get_context(**=options)" .-> s2
    click s1 "../modules/mcp_server.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_context` | `budget_tokens: int`, `focus: list[str] \| None`, `format: str`, `filters: dict \| None`, `prefer_fresh: bool`, `knowledge_mode: KnowledgeMode \| None` | - | `options[...]` | `service.get_context(...)` |
| `service.get_context` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_context | service.get_context | 1516 | `service.get_context(**=options)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_context` | `service.get_context` | 1516 |

## Behavior

Builds and validates the versioned context request from budget, focus, format,
filters, and freshness preference, using `changed` and `neighbors` when focus is
omitted. It revalidates the pinned source selection through the service options
and returns the protocol success envelope with payload and warnings. Invalid
requests become `McpWikiError` without mutating source or wiki files.
