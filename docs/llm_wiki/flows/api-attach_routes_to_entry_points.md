# attach_routes_to_entry_points

**Entry point:** `attach_routes_to_entry_points` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as attach_routes_to_entry_points
    participant p1 as _resolved_flow_route
    participant p2 as defaultdict
    participant p3 as contracts.get
    participant p4 as operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)
    participant p5 as isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)
    participant p6 as str
    participant p7 as handler.get
    participant p8 as handler_routes.append
    participant p9 as leaf_qualnames[…].add
    participant p10 as symbol.rsplit
    participant p11 as dict
    participant p12 as item.get
    participant p13 as routes.get
    participant p14 as leaf_qualnames.get
    participant p15 as set
    participant p16 as len
    participant p17 as next
    participant p18 as iter
    participant p19 as item.pop
    p0->>p1: _resolved_flow_route
    p0-->>p2: defaultdict(list)
    p0-->>p3: contracts.get('operations', [...])
    p0-->>p2: defaultdict(set)
    p0-->>p4: operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)('handler')
    p0-->>p5: isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)(handler, Mapping)
    p0-->>p6: str(...)
    p0-->>p7: handler.get('file')
    p0-->>p6: str(...)
    p0-->>p7: handler.get('symbol')
    p0-->>p6: str(...)
    p0-->>p7: handler.get('qualname')
    p0-->>p8: handler_routes.append(route)
    p0-->>p9: leaf_qualnames[…].add(qualname)
    p0-->>p10: symbol.rsplit('.', 1)
    p0-->>p11: dict(entry)
    p0-->>p6: str(...)
    p0-->>p12: item.get('file')
    p0-->>p6: str(...)
    p0-->>p12: item.get('symbol')
    p0-->>p13: routes.get((...))
    p0-->>p14: leaf_qualnames.get((...), set(...))
    p0-->>p10: symbol.rsplit('.', 1)
    p0-->>p15: set
    p0-->>p16: len(qualnames)
    p0-->>p13: routes.get((...))
    p0-->>p17: next(iter(...))
    p0-->>p18: iter(qualnames)
    p0-->>p12: item.get('category')
    p0-->>p19: item.pop('routes', None)
```

> Call sequence diagram shows 30 of 46 interactions; 16 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 13 of 19 (6 omitted); unresolved 16 of 26 (10 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/api_contracts.py:_resolved_flow_route` | 13 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/api_contracts.py:_resolved_flow_route` | 13 | - | external | 5 |
| `src/llm_wiki_cli/services/api_contracts.py:attach_routes_to_entry_points` | 1 | - | external | 1 |
| `src/llm_wiki_cli/services/api_contracts.py:attach_routes_to_entry_points` | 1 | - | unresolved | 1 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 14, emitted: 14, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. attach_routes_to_entry_points"]
    s2["2. defaultdict"]
    s3["3. defaultdict"]
    s4["4. contracts.get"]
    s5["5. operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)"]
    s6["6. isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)"]
    s7["7. str"]
    s8["8. handler.get"]
    s9["9. str"]
    s10["10. handler.get"]
    s11["11. str"]
    s12["12. handler.get"]
    s1 -. "defaultdict(list)" .-> s2
    s1 -. "defaultdict(set)" .-> s3
    s1 -. "contracts.get('operations', [...])" .-> s4
    s1 -. "operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)('handler')" .-> s5
    s1 -. "isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)(handler, Mapping)" .-> s6
    s1 -. "str(...)" .-> s7
    s1 -. "handler.get('file')" .-> s8
    s1 -. "str(...)" .-> s9
    s1 -. "handler.get('symbol')" .-> s10
    s1 -. "str(...)" .-> s11
    s1 -. "handler.get('qualname')" .-> s12
    b0["mutation handler_routes.append"]
    s1 -. "mutation handler_routes.append" .-> b0
    b1["mutation item.pop"]
    s1 -. "mutation item.pop" .-> b1
    b2["mutation result.append"]
    s1 -. "mutation result.append" .-> b2
    click s1 "../modules/api_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `attach_routes_to_entry_points` | `entry_points: Sequence[Mapping[str, Any]]`, `contracts: Mapping[str, Any]` | `Mapping` | `item[...]` | `result` |
| `defaultdict` | - | - | - | - |
| `defaultdict` | - | - | - | - |
| `contracts.get` | - | - | - | - |
| `operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)` | - | - | - | - |
| `str` | - | - | - | - |
| `handler.get` | - | - | - | - |
| `str` | - | - | - | - |
| `handler.get` | - | - | - | - |
| `str` | - | - | - | - |
| `handler.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| attach_routes_to_entry_points | defaultdict | 1923 | `defaultdict(list)` |
| attach_routes_to_entry_points | defaultdict | 1924 | `defaultdict(set)` |
| attach_routes_to_entry_points | contracts.get | 1925 | `contracts.get('operations', [...])` |
| attach_routes_to_entry_points | operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points) | 1926 | `operation.get('handler')` |
| attach_routes_to_entry_points | isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points) | 1927 | `isinstance(handler, Mapping)` |
| attach_routes_to_entry_points | str | 1929 | `str(...)` |
| attach_routes_to_entry_points | handler.get | 1929 | `handler.get('file')` |
| attach_routes_to_entry_points | str | 1930 | `str(...)` |
| attach_routes_to_entry_points | handler.get | 1930 | `handler.get('symbol')` |
| attach_routes_to_entry_points | str | 1931 | `str(...)` |
| attach_routes_to_entry_points | handler.get | 1931 | `handler.get('qualname')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handler_routes.append` | `attach_routes_to_entry_points` | 1937 |
| mutation | `item.pop` | `attach_routes_to_entry_points` | 1950 |
| mutation | `result.append` | `attach_routes_to_entry_points` | 1955 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `attach_routes_to_entry_points` | `defaultdict` | 1923 |
| external_call | `attach_routes_to_entry_points` | `defaultdict` | 1924 |
| unresolved_call | `attach_routes_to_entry_points` | `contracts.get` | 1925 |
| unresolved_call | `attach_routes_to_entry_points` | `operation.get` | 1926 |
| external_call | `attach_routes_to_entry_points` | `isinstance` | 1927 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1929 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1930 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1931 |
| step_limit | `attach_routes_to_entry_points` | `first 12 steps` | 0 |

## Behavior

This flow starts at `attach_routes_to_entry_points` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
