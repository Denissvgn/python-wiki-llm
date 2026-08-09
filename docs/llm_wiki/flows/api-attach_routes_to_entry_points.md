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
    participant p2 as get
    participant p3 as isinstance
    participant p4 as str
    participant p5 as append
    participant p6 as add
    participant p7 as dict
    participant p8 as rsplit
    participant p9 as set
    participant p10 as len
    participant p11 as next
    participant p12 as iter
    p0-->>p1: defaultdict
    p0-->>p1: defaultdict
    p0-->>p2: get
    p0-->>p2: get
    p0-->>p3: isinstance
    p0-->>p4: str
    p0-->>p2: get
    p0-->>p4: str
    p0-->>p2: get
    p0-->>p4: str
    p0-->>p2: get
    p0-->>p5: append
    p0-->>p2: get
    p0-->>p2: get
    p0-->>p2: get
    p0-->>p6: add
    p0-->>p7: dict
    p0-->>p4: str
    p0-->>p2: get
    p0-->>p4: str
    p0-->>p2: get
    p0-->>p2: get
    p0-->>p2: get
    p0-->>p8: rsplit
    p0-->>p9: set
    p0-->>p10: len
    p0-->>p2: get
    p0-->>p11: next
    p0-->>p12: iter
    p0-->>p2: get
```

> Call sequence diagram shows 30 of 34 interactions; 4 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. attach_routes_to_entry_points"]
    s2["2. defaultdict"]
    s3["3. defaultdict"]
    s4["4. get"]
    s5["5. get"]
    s6["6. isinstance"]
    s7["7. str"]
    s8["8. get"]
    s9["9. str"]
    s10["10. get"]
    s11["11. str"]
    s12["12. get"]
    s1 -. "defaultdict(list)" .-> s2
    s1 -. "defaultdict(set)" .-> s3
    s1 -. "contracts.get('operations', [...])" .-> s4
    s1 -. "operation.get('handler')" .-> s5
    s1 -. "isinstance(handler, Mapping)" .-> s6
    s1 -. "str(...)" .-> s7
    s1 -. "handler.get('file')" .-> s8
    s1 -. "str(...)" .-> s9
    s1 -. "handler.get('symbol')" .-> s10
    s1 -. "str(...)" .-> s11
    s1 -. "handler.get('qualname')" .-> s12
    b0["mutation result.append"]
    s1 -. "mutation result.append" .-> b0
    click s1 "../modules/api_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `attach_routes_to_entry_points` | `entry_points: Sequence[Mapping[str, Any]]`, `contracts: Mapping[str, Any]` | `Mapping` | `item[...]` | `result` |
| `defaultdict` | - | - | - | - |
| `defaultdict` | - | - | - | - |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| attach_routes_to_entry_points | defaultdict | 1836 | `defaultdict(list)` |
| attach_routes_to_entry_points | defaultdict | 1837 | `defaultdict(set)` |
| attach_routes_to_entry_points | get | 1838 | `contracts.get('operations', [...])` |
| attach_routes_to_entry_points | get | 1839 | `operation.get('handler')` |
| attach_routes_to_entry_points | isinstance | 1840 | `isinstance(handler, Mapping)` |
| attach_routes_to_entry_points | str | 1842 | `str(...)` |
| attach_routes_to_entry_points | get | 1842 | `handler.get('file')` |
| attach_routes_to_entry_points | str | 1843 | `str(...)` |
| attach_routes_to_entry_points | get | 1843 | `handler.get('symbol')` |
| attach_routes_to_entry_points | str | 1844 | `str(...)` |
| attach_routes_to_entry_points | get | 1844 | `handler.get('qualname')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `result.append` | `attach_routes_to_entry_points` | 1867 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `attach_routes_to_entry_points` | `defaultdict` | 1836 |
| external_call | `attach_routes_to_entry_points` | `defaultdict` | 1837 |
| unresolved_call | `attach_routes_to_entry_points` | `contracts.get` | 1838 |
| unresolved_call | `attach_routes_to_entry_points` | `operation.get` | 1839 |
| unresolved_call | `attach_routes_to_entry_points` | `isinstance` | 1840 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1842 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1843 |
| unresolved_call | `attach_routes_to_entry_points` | `handler.get` | 1844 |
| step_limit | `attach_routes_to_entry_points` | `first 12 steps` | 0 |

## Behavior

This flow starts at `attach_routes_to_entry_points` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
