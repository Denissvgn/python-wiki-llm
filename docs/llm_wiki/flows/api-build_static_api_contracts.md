# build_static_api_contracts

**Entry point:** `build_static_api_contracts` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [imports](../modules/imports.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_static_api_contracts
    participant p1 as _declaration_nodes
    participant p2 as _framework_records
    participant p3 as items
    participant p4 as get
    participant p5 as isinstance
    participant p6 as str
    participant p7 as _node_key
    participant p8 as dict
    participant p9 as append
    participant p10 as _candidate_scopes
    participant p11 as split
    participant p12 as join
    participant p13 as range
    participant p14 as len
    p0->>p1: _declaration_nodes
    p1->>p2: _framework_records
    p2-->>p3: items
    p2-->>p4: get
    p2-->>p5: isinstance
    p2-->>p4: get
    p2-->>p5: isinstance
    p1-->>p4: get
    p1-->>p5: isinstance
    p1-->>p6: str
    p1-->>p4: get
    p1-->>p6: str
    p1-->>p4: get
    p1->>p7: _node_key
    p1-->>p8: dict
    p1-->>p9: append
    p1->>p2: _framework_records
    p1-->>p4: get
    p1-->>p5: isinstance
    p1-->>p6: str
    p1-->>p4: get
    p1-->>p6: str
    p1-->>p4: get
    p1-->>p6: str
    p1-->>p4: get
    p1->>p10: _candidate_scopes
    p10-->>p11: split
    p10-->>p12: join
    p10-->>p13: range
    p10-->>p14: len
```

> Call sequence diagram shows 30 of 207 interactions; 177 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_static_api_contracts"]
    s2["2. _declaration_nodes"]
    s3["3. _framework_records"]
    s4["4. items"]
    s5["5. get"]
    s6["6. isinstance"]
    s7["7. get"]
    s8["8. isinstance"]
    s9["9. get"]
    s10["10. isinstance"]
    s11["11. str"]
    s12["12. get"]
    s1 -->|"_declaration_nodes(inventory)"| s2
    s2 -->|"_framework_records(inventory)"| s3
    s3 -. "inventory.items(data not statically known)" .-> s4
    s3 -. "file_data.get('frameworks')" .-> s5
    s3 -. "isinstance(frameworks, Mapping)" .-> s6
    s3 -. "frameworks.get('fastapi')" .-> s7
    s3 -. "isinstance(fastapi, Mapping)" .-> s8
    s2 -. "fastapi.get(plural, [...])" .-> s9
    s2 -. "isinstance(record, Mapping)" .-> s10
    s2 -. "str(...)" .-> s11
    s2 -. "record.get('binding')" .-> s12
    b0["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b0
    b1["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b1
    b2["mutation unknowns.append"]
    s1 -. "mutation unknowns.append" .-> b2
    b3["mutation unknowns.append"]
    s1 -. "mutation unknowns.append" .-> b3
    b4["mutation applications.append"]
    s1 -. "mutation applications.append" .-> b4
    b5["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b5
    b6["mutation assembled.sort"]
    s1 -. "mutation assembled.sort" .-> b6
    b7["mutation applications.append"]
    s2 -. "mutation applications.append" .-> b7
    click s1 "../modules/api_contracts.md"
    click s2 "../modules/api_contracts.md"
    click s3 "../modules/api_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_static_api_contracts` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping`, `Mapping`, `_UNKNOWN`, `_UNKNOWN` | `config[...]`, `ids[...]`, `operation[...]` | `{...}` |
| `_declaration_nodes` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping`, `Mapping` | `nodes[...]` | `(...)` |
| `_framework_records` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping`, `Mapping` | - | - |
| `items` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_static_api_contracts | _declaration_nodes | 736 | `_declaration_nodes(inventory)` |
| _declaration_nodes | _framework_records | 228 | `_framework_records(inventory)` |
| _framework_records | items | 218 | `inventory.items(data not statically known)` |
| _framework_records | get | 219 | `file_data.get('frameworks')` |
| _framework_records | isinstance | 220 | `isinstance(frameworks, Mapping)` |
| _framework_records | get | 220 | `frameworks.get('fastapi')` |
| _framework_records | isinstance | 221 | `isinstance(fastapi, Mapping)` |
| _declaration_nodes | get | 230 | `fastapi.get(plural, [...])` |
| _declaration_nodes | isinstance | 231 | `isinstance(record, Mapping)` |
| _declaration_nodes | str | 233 | `str(...)` |
| _declaration_nodes | get | 233 | `record.get('binding')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `diagnostics.append` | `build_static_api_contracts` | 755 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 792 |
| mutation | `unknowns.append` | `build_static_api_contracts` | 809 |
| mutation | `unknowns.append` | `build_static_api_contracts` | 818 |
| mutation | `applications.append` | `build_static_api_contracts` | 827 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 1136 |
| mutation | `assembled.sort` | `build_static_api_contracts` | 1154 |
| mutation | `applications.append` | `_declaration_nodes` | 240 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_framework_records` | `inventory.items` | 218 |
| unresolved_call | `_framework_records` | `file_data.get` | 219 |
| unresolved_call | `_framework_records` | `isinstance` | 220 |
| unresolved_call | `_framework_records` | `frameworks.get` | 220 |
| unresolved_call | `_framework_records` | `isinstance` | 221 |
| unresolved_call | `_declaration_nodes` | `fastapi.get` | 230 |
| unresolved_call | `_declaration_nodes` | `isinstance` | 231 |
| unresolved_call | `_declaration_nodes` | `record.get` | 233 |
| step_limit | `build_static_api_contracts` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_static_api_contracts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
