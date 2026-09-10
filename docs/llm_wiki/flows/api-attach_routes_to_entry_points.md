# attach_routes_to_entry_points

**Entry point:** `attach_routes_to_entry_points` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as attach_routes_to_entry_points
    participant p1 as defaultdict
    participant p2 as contracts.get
    participant p3 as operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)
    participant p4 as isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)
    participant p5 as str
    participant p6 as handler.get
    participant p7 as _resolved_flow_route
    participant p8 as operation.get (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    participant p9 as isinstance (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    participant p10 as method.strip
    participant p11 as method.upper
    participant p12 as path.strip
    participant p13 as any
    participant p14 as unknown.get
    participant p15 as operation_id.strip
    participant p16 as handler_routes.append
    participant p17 as leaf_qualnames[…].add
    participant p18 as symbol.rsplit
    participant p19 as dict
    p0-->>p1: defaultdict
    p0-->>p1: defaultdict
    p0-->>p2: contracts.get
    p0-->>p3: operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points)
    p0-->>p4: isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points)
    p0-->>p5: str
    p0-->>p6: handler.get
    p0-->>p5: str
    p0-->>p6: handler.get
    p0-->>p5: str
    p0-->>p6: handler.get
    p0->>p7: _resolved_flow_route
    p7-->>p8: operation.get (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p8: operation.get (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p9: isinstance (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p10: method.strip
    p7-->>p11: method.upper
    p7-->>p9: isinstance (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p12: path.strip
    p7-->>p13: any
    p7-->>p9: isinstance (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p14: unknown.get
    p7-->>p8: operation.get (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p8: operation.get (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p9: isinstance (src/llm_wiki_cli/services…ts.py:_resolved_flow_route)
    p7-->>p15: operation_id.strip
    p0-->>p16: handler_routes.append
    p0-->>p17: leaf_qualnames[…].add
    p0-->>p18: symbol.rsplit
    p0-->>p19: dict
```

> Call sequence diagram shows 30 of 46 interactions; 16 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
| attach_routes_to_entry_points | defaultdict | 1888 | `defaultdict(list)` |
| attach_routes_to_entry_points | defaultdict | 1889 | `defaultdict(set)` |
| attach_routes_to_entry_points | contracts.get | 1890 | `contracts.get('operations', [...])` |
| attach_routes_to_entry_points | operation.get (src/llm_wiki_cli/services…ach_routes_to_entry_points) | 1891 | `operation.get('handler')` |
| attach_routes_to_entry_points | isinstance (src/llm_wiki_cli/services…ach_routes_to_entry_points) | 1892 | `isinstance(handler, Mapping)` |
| attach_routes_to_entry_points | str | 1894 | `str(...)` |
| attach_routes_to_entry_points | handler.get | 1894 | `handler.get('file')` |
| attach_routes_to_entry_points | str | 1895 | `str(...)` |
| attach_routes_to_entry_points | handler.get | 1895 | `handler.get('symbol')` |
| attach_routes_to_entry_points | str | 1896 | `str(...)` |
| attach_routes_to_entry_points | handler.get | 1896 | `handler.get('qualname')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `handler_routes.append` | `attach_routes_to_entry_points` | 1902 |
| mutation | `item.pop` | `attach_routes_to_entry_points` | 1915 |
| mutation | `result.append` | `attach_routes_to_entry_points` | 1920 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `attach_routes_to_entry_points` | `defaultdict` | 1888 |
| external_call | `attach_routes_to_entry_points` | `defaultdict` | 1889 |
| unresolved_call | `attach_routes_to_entry_points` | `contracts.get` | 1890 |
| unresolved_call | `attach_routes_to_entry_points` | `operation.get` | 1891 |
| external_call | `attach_routes_to_entry_points` | `isinstance` | 1892 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1894 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1895 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1896 |
| step_limit | `attach_routes_to_entry_points` | `first 12 steps` | 0 |

## Behavior

This flow starts at `attach_routes_to_entry_points` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
