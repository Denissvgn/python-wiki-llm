# render_api_contracts_markdown

**Entry point:** `render_api_contracts_markdown` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_api_contracts_markdown
    participant p1 as _handler_link
    participant p2 as _entity_link
    participant p3 as _md_code
    participant p4 as _md_text
    participant p5 as _operation_anchor
    participant p6 as isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)
    participant p7 as contracts.get
    participant p8 as lines.extend
    participant p9 as openapi.get
    participant p10 as list
    participant p11 as application.get
    participant p12 as ', '.join
    participant p13 as sorted
    participant p14 as config.items
    participant p15 as lines.append
    participant p16 as ' | '.join
    p0->>p1: _handler_link
    p0->>p2: _entity_link
    p0->>p3: _md_code
    p0->>p4: _md_text
    p0->>p5: _operation_anchor
    p0-->>p6: isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)(openapi, Mapping)
    p0-->>p7: contracts.get('openapi')
    p0-->>p8: lines.extend([...])
    p0-->>p9: openapi.get('version')
    p0-->>p9: openapi.get('path')
    p0-->>p9: openapi.get('sha256')
    p0-->>p8: lines.extend([...])
    p0-->>p10: list(contracts.get(...))
    p0-->>p7: contracts.get('applications', [...])
    p0-->>p8: lines.extend([...])
    p0-->>p8: lines.extend([...])
    p0-->>p11: application.get('config')
    p0-->>p6: isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)(config, Mapping)
    p0-->>p12: ', '.join(...)
    p0-->>p13: sorted(config.items(...))
    p0-->>p14: config.items
    p0-->>p11: application.get('file', 'unknown')
    p0-->>p11: application.get('line', '?')
    p0-->>p15: lines.append(...)
    p0-->>p16: ' | '.join([...])
    p0-->>p11: application.get('binding')
    p0-->>p11: application.get('scope')
    p0-->>p15: lines.append('*No statically linked FastAPI application declaration.*')
    p0-->>p11: application.get('unknowns', [...])
    p0-->>p6: isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)(unknown, Mapping)
```

> Call sequence diagram shows 30 of 187 interactions; 157 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 28 (23 omitted); unresolved 20 of 118 (98 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/api_contracts.py:_md_code` | 6 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/api_contracts.py:_md_code` | 6 | - | external | 5 |
| `src/llm_wiki_cli/services/api_contracts.py:render_api_contracts_markdown` | 1 | [src/llm_wiki_cli/services/api_contracts.py](../modules/api_contracts.md) | internal | 31 |
| `src/llm_wiki_cli/services/api_contracts.py:_md_text` | 27 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:_md_text` | 27 | - | external | 1 |
| `src/llm_wiki_cli/services/api_contracts.py:render_api_contracts_markdown` | 1 | - | unresolved | 81 |
| `src/llm_wiki_cli/services/api_contracts.py:render_api_contracts_markdown` | 1 | - | external | 8 |
| `src/llm_wiki_cli/services/api_contracts.py:_handler_link` | 69 | - | external | 3 |
> Omission summary shows 8 of 15 groups; 7 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 42; effect analysis evaluated: 41, partial: 1, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 42 source steps with known totals: observed: 154, emitted: 128, omitted: 26. Unavailable totals are excluded.

- Effect collector omitted observations before flow assembly; displayed effects are partial.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `render_api_contracts_markdown` | `available` | `partial` | `available` | `42` | `16` | `26` |
| `contracts.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `lines.extend` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `openapi.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_md_code` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `str(…).replace(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `str(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `str (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `max` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `re.findall` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. render_api_contracts_markdown"]
    s2["2. contracts.get"]
    s3["3. isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)"]
    s4["4. lines.extend"]
    s5["5. openapi.get"]
    s6["6. _md_code"]
    s7["7. str(…).replace(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)"]
    s8["8. str(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)"]
    s9["9. str (src/llm_wiki_cli/services/api_contracts.py:_md_code)"]
    s10["10. max"]
    s11["11. len (src/llm_wiki_cli/services/api_contracts.py:_md_code)"]
    s12["12. re.findall"]
    s1 -. "contracts.get('openapi')" .-> s2
    s1 -. "isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)(openapi, Mapping)" .-> s3
    s1 -. "lines.extend([...])" .-> s4
    s1 -. "openapi.get('version')" .-> s5
    s1 -->|"_md_code(openapi.get(...))"| s6
    s6 -. "str(…).replace(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)('\n', ' ')" .-> s7
    s6 -. "str(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)('|', '\\|')" .-> s8
    s6 -. "str (src/llm_wiki_cli/services/api_contracts.py:_md_code)(value)" .-> s9
    s6 -. "max(..., default=0)" .-> s10
    s6 -. "len (src/llm_wiki_cli/services/api_contracts.py:_md_code)(match)" .-> s11
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
| `contracts.get` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown)` | - | - | - | - |
| `lines.extend` | - | - | - | - |
| `openapi.get` | - | - | - | - |
| `_md_code` | `value: Any` | - | - | `...` |
| `str(…).replace(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | - | - | - | - |
| `str(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | - | - | - | - |
| `str (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | - | - | - | - |
| `max` | - | - | - | - |
| `len (src/llm_wiki_cli/services/api_contracts.py:_md_code)` | - | - | - | - |
| `re.findall` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_api_contracts_markdown | contracts.get | 2023 | `contracts.get('openapi')` |
| render_api_contracts_markdown | isinstance (src/llm_wiki_cli/services…er_api_contracts_markdown) | 2024 | `isinstance(openapi, Mapping)` |
| render_api_contracts_markdown | lines.extend | 2025 | `lines.extend([...])` |
| render_api_contracts_markdown | openapi.get | 2027 | `openapi.get('version')` |
| render_api_contracts_markdown | _md_code | 2027 | `_md_code(openapi.get(...))` |
| _md_code | str(…).replace(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code) | 1974 | `str(value).replace('\|', '\\\|').replace('\n', ' ')` |
| _md_code | str(…).replace (src/llm_wiki_cli/services/api_contracts.py:_md_code) | 1974 | `str(value).replace('\|', '\\\|')` |
| _md_code | str (src/llm_wiki_cli/services/api_contracts.py:_md_code) | 1974 | `str(value)` |
| _md_code | max | 1976 | `max(..., default=0)` |
| _md_code | len (src/llm_wiki_cli/services/api_contracts.py:_md_code) | 1976 | `len(match)` |
| _md_code | re.findall | 1976 | `re.findall('`+', text)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `lines.extend` | `render_api_contracts_markdown` | 2025 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 2033 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 2042 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 2044 |
| mutation | `lines.append` | `render_api_contracts_markdown` | 2061 |
| mutation | `lines.append` | `render_api_contracts_markdown` | 2074 |
| mutation | `lines.extend` | `render_api_contracts_markdown` | 2082 |
| mutation | `lines.append` | `render_api_contracts_markdown` | 2084 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `render_api_contracts_markdown` | `contracts.get` | 2023 |
| external_call | `render_api_contracts_markdown` | `isinstance` | 2024 |
| unresolved_call | `render_api_contracts_markdown` | `openapi.get` | 2027 |
| unresolved_call | `_md_code` | `str(value).replace('\|', '\\\|').replace` | 1974 |
| unresolved_call | `_md_code` | `str(value).replace` | 1974 |
| external_call | `_md_code` | `max` | 1976 |
| external_call | `_md_code` | `re.findall` | 1976 |
| step_limit | `render_api_contracts_markdown` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_api_contracts_markdown` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
