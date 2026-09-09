# link_entry_point_flows

**Entry point:** `link_entry_point_flows` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as link_entry_point_flows
    participant p1 as deepcopy
    participant p2 as dict
    participant p3 as get
    participant p4 as rsplit
    participant p5 as str
    participant p6 as isinstance
    p0-->>p1: deepcopy
    p0-->>p2: dict
    p0-->>p3: get
    p0-->>p3: get
    p0-->>p4: rsplit
    p0-->>p5: str
    p0-->>p3: get
    p0-->>p5: str
    p0-->>p3: get
    p0-->>p5: str
    p0-->>p3: get
    p0-->>p6: isinstance
    p0-->>p6: isinstance
    p0-->>p3: get
    p0-->>p6: isinstance
    p0-->>p4: rsplit
    p0-->>p5: str
    p0-->>p3: get
    p0-->>p3: get
    p0-->>p5: str
    p0-->>p3: get
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. link_entry_point_flows"]
    s2["2. deepcopy"]
    s3["3. dict"]
    s4["4. get"]
    s5["5. get"]
    s6["6. rsplit"]
    s7["7. str"]
    s8["8. get"]
    s9["9. str"]
    s10["10. get"]
    s11["11. str"]
    s12["12. get"]
    s1 -. "deepcopy(dict(...))" .-> s2
    s1 -. "dict(contracts)" .-> s3
    s1 -. "entry.get('category')" .-> s4
    s1 -. "entry.get('id')" .-> s5
    s1 -. "str(entry.get('symbol') or '').rsplit('.', 1)" .-> s6
    s1 -. "str(...)" .-> s7
    s1 -. "entry.get('symbol')" .-> s8
    s1 -. "str(...)" .-> s9
    s1 -. "entry.get('file')" .-> s10
    s1 -. "str(entry[...])" .-> s11
    s1 -. "linked.get('operations')" .-> s12
    click s1 "../modules/api_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `link_entry_point_flows` | `contracts: Mapping[str, object]`, `entry_points: Iterable[Mapping[str, object]]` | `Mapping` | `operation[...]` | `linked` |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `rsplit` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| link_entry_point_flows | deepcopy | 1837 | `deepcopy(dict(...))` |
| link_entry_point_flows | dict | 1837 | `dict(contracts)` |
| link_entry_point_flows | get | 1840 | `entry.get('category')` |
| link_entry_point_flows | get | 1840 | `entry.get('id')` |
| link_entry_point_flows | rsplit | 1842 | `str(entry.get('symbol') or '').rsplit('.', 1)` |
| link_entry_point_flows | str | 1842 | `str(...)` |
| link_entry_point_flows | get | 1842 | `entry.get('symbol')` |
| link_entry_point_flows | str | 1843 | `str(...)` |
| link_entry_point_flows | get | 1843 | `entry.get('file')` |
| link_entry_point_flows | str | 1843 | `str(entry[...])` |
| link_entry_point_flows | get | 1844 | `linked.get('operations')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `link_entry_point_flows` | `deepcopy` | 1837 |
| unresolved_call | `link_entry_point_flows` | `entry.get` | 1840 |
| unresolved_call | `link_entry_point_flows` | `str(entry.get('symbol') or '').rsplit` | 1842 |
| unresolved_call | `link_entry_point_flows` | `entry.get` | 1842 |
| unresolved_call | `link_entry_point_flows` | `entry.get` | 1843 |
| unresolved_call | `link_entry_point_flows` | `linked.get` | 1844 |
| step_limit | `link_entry_point_flows` | `first 12 steps` | 0 |

## Behavior

This flow starts at `link_entry_point_flows` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
