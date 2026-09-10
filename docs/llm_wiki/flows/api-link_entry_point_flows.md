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
    participant p3 as entry.get
    participant p4 as str(…).rsplit (src/llm_wiki_cli/services….py:link_entry_point_flows)
    participant p5 as str (src/llm_wiki_cli/services….py:link_entry_point_flows)
    participant p6 as str (src/llm_wiki_cli/services…:link_entry_point_flows, 1)
    participant p7 as linked.get
    participant p8 as isinstance
    participant p9 as operation.get
    participant p10 as str(…).rsplit (src/llm_wiki_cli/services…:link_entry_point_flows, 1)
    participant p11 as handler.get
    participant p12 as flow_ids.get
    p0-->>p1: deepcopy
    p0-->>p2: dict
    p0-->>p3: entry.get
    p0-->>p3: entry.get
    p0-->>p4: str(…).rsplit (src/llm_wiki_cli/services….py:link_entry_point_flows)
    p0-->>p5: str (src/llm_wiki_cli/services….py:link_entry_point_flows)
    p0-->>p3: entry.get
    p0-->>p6: str (src/llm_wiki_cli/services…:link_entry_point_flows, 1)
    p0-->>p3: entry.get
    p0-->>p5: str (src/llm_wiki_cli/services….py:link_entry_point_flows)
    p0-->>p7: linked.get
    p0-->>p8: isinstance
    p0-->>p8: isinstance
    p0-->>p9: operation.get
    p0-->>p8: isinstance
    p0-->>p10: str(…).rsplit (src/llm_wiki_cli/services…:link_entry_point_flows, 1)
    p0-->>p5: str (src/llm_wiki_cli/services….py:link_entry_point_flows)
    p0-->>p11: handler.get
    p0-->>p12: flow_ids.get
    p0-->>p5: str (src/llm_wiki_cli/services….py:link_entry_point_flows)
    p0-->>p11: handler.get
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. link_entry_point_flows"]
    s2["2. deepcopy"]
    s3["3. dict"]
    s4["4. entry.get"]
    s5["5. entry.get"]
    s6["6. str(…).rsplit (src/llm_wiki_cli/services….py:link_entry_point_flows)"]
    s7["7. str (src/llm_wiki_cli/services….py:link_entry_point_flows)"]
    s8["8. entry.get"]
    s9["9. str (src/llm_wiki_cli/services…:link_entry_point_flows, 1)"]
    s10["10. entry.get"]
    s11["11. str (src/llm_wiki_cli/services….py:link_entry_point_flows)"]
    s12["12. linked.get"]
    s1 -. "deepcopy(dict(...))" .-> s2
    s1 -. "dict(contracts)" .-> s3
    s1 -. "entry.get('category')" .-> s4
    s1 -. "entry.get('id')" .-> s5
    s1 -. "str(…).rsplit (src/llm_wiki_cli/services….py:link_entry_point_flows)('.', 1)" .-> s6
    s1 -. "str (src/llm_wiki_cli/services….py:link_entry_point_flows)(...)" .-> s7
    s1 -. "entry.get('symbol')" .-> s8
    s1 -. "str (src/llm_wiki_cli/services…:link_entry_point_flows, 1)(...)" .-> s9
    s1 -. "entry.get('file')" .-> s10
    s1 -. "str (src/llm_wiki_cli/services….py:link_entry_point_flows)(entry[...])" .-> s11
    s1 -. "linked.get('operations')" .-> s12
    click s1 "../modules/api_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `link_entry_point_flows` | `contracts: Mapping[str, object]`, `entry_points: Iterable[Mapping[str, object]]` | `Mapping` | `operation[...]` | `linked` |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `entry.get` | - | - | - | - |
| `entry.get` | - | - | - | - |
| `str(…).rsplit (src/llm_wiki_cli/services….py:link_entry_point_flows)` | - | - | - | - |
| `str (src/llm_wiki_cli/services….py:link_entry_point_flows)` | - | - | - | - |
| `entry.get` | - | - | - | - |
| `str (src/llm_wiki_cli/services…:link_entry_point_flows, 1)` | - | - | - | - |
| `entry.get` | - | - | - | - |
| `str (src/llm_wiki_cli/services….py:link_entry_point_flows)` | - | - | - | - |
| `linked.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| link_entry_point_flows | deepcopy | 1837 | `deepcopy(dict(...))` |
| link_entry_point_flows | dict | 1837 | `dict(contracts)` |
| link_entry_point_flows | entry.get | 1840 | `entry.get('category')` |
| link_entry_point_flows | entry.get | 1840 | `entry.get('id')` |
| link_entry_point_flows | str(…).rsplit (src/llm_wiki_cli/services….py:link_entry_point_flows) | 1842 | `str(entry.get('symbol') or '').rsplit('.', 1)` |
| link_entry_point_flows | str (src/llm_wiki_cli/services….py:link_entry_point_flows) | 1842 | `str(...)` |
| link_entry_point_flows | entry.get | 1842 | `entry.get('symbol')` |
| link_entry_point_flows | str (src/llm_wiki_cli/services…:link_entry_point_flows, 1) | 1843 | `str(...)` |
| link_entry_point_flows | entry.get | 1843 | `entry.get('file')` |
| link_entry_point_flows | str (src/llm_wiki_cli/services….py:link_entry_point_flows) | 1843 | `str(entry[...])` |
| link_entry_point_flows | linked.get | 1844 | `linked.get('operations')` |

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
