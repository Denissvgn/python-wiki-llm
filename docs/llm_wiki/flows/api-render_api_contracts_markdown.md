# render_api_contracts_markdown

**Entry point:** `render_api_contracts_markdown` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_api_contracts_markdown
    participant p1 as get
    participant p2 as isinstance
    participant p3 as extend
    participant p4 as _md_code
    participant p5 as replace
    participant p6 as str
    participant p7 as max
    participant p8 as len
    participant p9 as findall
    participant p10 as startswith
    participant p11 as endswith
    participant p12 as list
    participant p13 as join
    participant p14 as _md_text
    p0-->>p1: get
    p0-->>p2: isinstance
    p0-->>p3: extend
    p0-->>p1: get
    p0->>p4: _md_code
    p4-->>p5: replace
    p4-->>p5: replace
    p4-->>p6: str
    p4-->>p7: max
    p4-->>p8: len
    p4-->>p9: findall
    p4-->>p7: max
    p4-->>p10: startswith
    p4-->>p11: endswith
    p0-->>p1: get
    p0->>p4: _md_code
    p0-->>p1: get
    p0-->>p3: extend
    p0-->>p12: list
    p0-->>p1: get
    p0-->>p3: extend
    p0-->>p3: extend
    p0-->>p1: get
    p0-->>p2: isinstance
    p0-->>p13: join
    p0->>p14: _md_text
    p14-->>p5: replace
    p14-->>p5: replace
    p14-->>p5: replace
    p14-->>p6: str
```

> Call sequence diagram shows 30 of 187 interactions; 157 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. render_api_contracts_markdown"]
    s2["2. get"]
    s3["3. isinstance"]
    s4["4. extend"]
    s5["5. get"]
    s6["6. _md_code"]
    s7["7. replace"]
    s8["8. replace"]
    s9["9. str"]
    s10["10. max"]
    s11["11. len"]
    s12["12. findall"]
    s1 -. "contracts.get('openapi')" .-> s2
    s1 -. "isinstance(openapi, Mapping)" .-> s3
    s1 -. "lines.extend([...])" .-> s4
    s1 -. "openapi.get('version')" .-> s5
    s1 -->|"_md_code(openapi.get(...))"| s6
    s6 -. "str(value).replace('|', '\\|').replace('\n', ' ')" .-> s7
    s6 -. "str(value).replace('|', '\\|')" .-> s8
    s6 -. "str(value)" .-> s9
    s6 -. "max(..., default=0)" .-> s10
    s6 -. "len(match)" .-> s11
    s6 -. "re.findall('#96;+', text)" .-> s12
    b0["mutation lines.extend"]
    s1 -. "mutation lines.extend" .-> b0
    b1["mutation lines.extend"]
    s1 -. "mutation lines.extend" .-> b1
    b2["mutation lines.extend"]
    s1 -. "mutation lines.extend" .-> b2
    b3["mutation lines.extend"]
    s1 -. "mutation lines.extend" .-> b3
    b4["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b4
    b5["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b5
    b6["mutation lines.extend"]
    s1 -. "mutation lines.extend" .-> b6
    b7["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b7
    click s1 "../modules/api_contracts.md"
    click s6 "../modules/api_contracts.md"
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
| `render_api_contracts_markdown` | `contracts: Mapping[str, Any]`, `module_page_map: Mapping[str, str] \| None`, `entity_page_map: Mapping[Any, str] \| None` | `Mapping`, `Mapping`, `Mapping`, `Mapping` | - | `...` |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `extend` | - | - | - | - |
| `get` | - | - | - | - |
| `_md_code` | `value: Any` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `str` | - | - | - | - |
| `max` | - | - | - | - |
| `len` | - | - | - | - |
| `findall` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_api_contracts_markdown | get | 1935 | `contracts.get('openapi')` |
| render_api_contracts_markdown | isinstance | 1936 | `isinstance(openapi, Mapping)` |
| render_api_contracts_markdown | extend | 1937 | `lines.extend([...])` |
| render_api_contracts_markdown | get | 1939 | `openapi.get('version')` |
| render_api_contracts_markdown | _md_code | 1939 | `_md_code(openapi.get(...))` |
| _md_code | replace | 1886 | `str(value).replace('\|', '\\\|').replace('\n', ' ')` |
| _md_code | replace | 1886 | `str(value).replace('\|', '\\\|')` |
| _md_code | str | 1886 | `str(value)` |
| _md_code | max | 1888 | `max(..., default=0)` |
| _md_code | len | 1888 | `len(match)` |
| _md_code | findall | 1888 | `re.findall('`+', text)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `lines.extend` | `render_api_contracts_markdown` | 1937 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 1945 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 1954 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 1956 |
| mutation | `lines.append` | `render_api_contracts_markdown` | 1973 |
| mutation | `lines.append` | `render_api_contracts_markdown` | 1986 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 1994 |
| mutation | `lines.append` | `render_api_contracts_markdown` | 1996 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `render_api_contracts_markdown` | `contracts.get` | 1935 |
| unresolved_call | `render_api_contracts_markdown` | `isinstance` | 1936 |
| unresolved_call | `render_api_contracts_markdown` | `openapi.get` | 1939 |
| unresolved_call | `_md_code` | `str(value).replace('\|', '\\\|').replace` | 1886 |
| unresolved_call | `_md_code` | `str(value).replace` | 1886 |
| unresolved_call | `_md_code` | `max` | 1888 |
| external_call | `_md_code` | `re.findall` | 1888 |
| step_limit | `render_api_contracts_markdown` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_api_contracts_markdown` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
