# render_flow_api_contract_section

**Entry point:** `render_flow_api_contract_section` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_flow_api_contract_section
    participant p1 as sorted
    participant p2 as str
    participant p3 as get
    participant p4 as _operation_anchor
    participant p5 as lower
    participant p6 as strip
    participant p7 as sub
    participant p8 as append
    participant p9 as _md_code
    participant p10 as replace
    participant p11 as max
    participant p12 as len
    participant p13 as findall
    participant p14 as startswith
    participant p15 as endswith
    participant p16 as join
    p0-->>p1: sorted
    p0-->>p2: str
    p0-->>p3: get
    p0-->>p2: str
    p0-->>p3: get
    p0->>p4: _operation_anchor
    p4-->>p3: get
    p4-->>p3: get
    p4-->>p3: get
    p4-->>p5: lower
    p4-->>p6: strip
    p4-->>p7: sub
    p4-->>p2: str
    p0-->>p3: get
    p0-->>p3: get
    p0-->>p8: append
    p0->>p9: _md_code
    p9-->>p10: replace
    p9-->>p10: replace
    p9-->>p2: str
    p9-->>p11: max
    p9-->>p12: len
    p9-->>p13: findall
    p9-->>p11: max
    p9-->>p14: startswith
    p9-->>p15: endswith
    p0-->>p8: append
    p0-->>p16: join
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. render_flow_api_contract_section"]
    s2["2. sorted"]
    s3["3. str"]
    s4["4. get"]
    s5["5. str"]
    s6["6. get"]
    s7["7. _operation_anchor"]
    s8["8. get"]
    s9["9. get"]
    s10["10. get"]
    s11["11. lower"]
    s12["12. strip"]
    s1 -. "sorted(operations, key=...)" .-> s2
    s1 -. "str(...)" .-> s3
    s1 -. "item.get('path')" .-> s4
    s1 -. "str(...)" .-> s5
    s1 -. "item.get('method')" .-> s6
    s1 -->|"_operation_anchor(operation)"| s7
    s7 -. "operation.get('id')" .-> s8
    s7 -. "operation.get('method', '')" .-> s9
    s7 -. "operation.get('path', '')" .-> s10
    s7 -. "_SAFE_ID_RE.sub('-', str(identity)).strip('-').lower(data not statically known)" .-> s11
    s7 -. "_SAFE_ID_RE.sub('-', str(identity)).strip('-')" .-> s12
    b0["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b0
    b1["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b1
    click s1 "../modules/api_contracts.md"
    click s7 "../modules/api_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `render_flow_api_contract_section` | `operations: Sequence[Mapping[str, Any]]` | - | - | `''`, `...` |
| `sorted` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |
| `str` | - | - | - | - |
| `get` | - | - | - | - |
| `_operation_anchor` | `operation: Mapping[str, Any]` | - | - | `...` |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `lower` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_flow_api_contract_section | sorted | 2162 | `sorted(operations, key=...)` |
| render_flow_api_contract_section | str | 2163 | `str(...)` |
| render_flow_api_contract_section | get | 2163 | `item.get('path')` |
| render_flow_api_contract_section | str | 2163 | `str(...)` |
| render_flow_api_contract_section | get | 2163 | `item.get('method')` |
| render_flow_api_contract_section | _operation_anchor | 2165 | `_operation_anchor(operation)` |
| _operation_anchor | get | 1895 | `operation.get('id')` |
| _operation_anchor | get | 1896 | `operation.get('method', '')` |
| _operation_anchor | get | 1896 | `operation.get('path', '')` |
| _operation_anchor | lower | 1898 | `_SAFE_ID_RE.sub('-', str(identity)).strip('-').lower(data not statically known)` |
| _operation_anchor | strip | 1898 | `_SAFE_ID_RE.sub('-', str(identity)).strip('-')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `lines.append` | `render_flow_api_contract_section` | 2167 |
| mutation | `lines.append` | `render_flow_api_contract_section` | 2171 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `render_flow_api_contract_section` | `sorted` | 2162 |
| unresolved_call | `render_flow_api_contract_section` | `item.get` | 2163 |
| unresolved_call | `_operation_anchor` | `operation.get` | 1895 |
| unresolved_call | `_operation_anchor` | `operation.get` | 1896 |
| unresolved_call | `_operation_anchor` | `_SAFE_ID_RE.sub('-', str(identity)).strip('-').lower` | 1898 |
| unresolved_call | `_operation_anchor` | `_SAFE_ID_RE.sub('-', str(identity)).strip` | 1898 |
| step_limit | `render_flow_api_contract_section` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_flow_api_contract_section` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
