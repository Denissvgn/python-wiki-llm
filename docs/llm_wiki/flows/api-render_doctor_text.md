# render_doctor_text

**Entry point:** `render_doctor_text` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [doctor_service](../modules/doctor_service.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_doctor_text
    participant p1 as _render_doctor_payload
    participant p2 as isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    participant p3 as _format_counts
    participant p4 as isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)
    participant p5 as ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)
    participant p6 as lines.append
    participant p7 as lines.extend
    participant p8 as ', '.join (src/llm_wiki_cli/services….py:_render_doctor_payload)
    participant p9 as '\n'.join
    participant p10 as report.to_payload
    p0->>p1: _render_doctor_payload
    p1-->>p2: isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p2: isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p2: isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p2: isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p2: isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p2: isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1->>p3: _format_counts
    p3-->>p4: isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)
    p3-->>p5: ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)
    p1-->>p6: lines.append
    p1-->>p7: lines.extend
    p1-->>p6: lines.append
    p1-->>p8: ', '.join (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p6: lines.append
    p1-->>p8: ', '.join (src/llm_wiki_cli/services….py:_render_doctor_payload)
    p1-->>p9: '\n'.join
    p0-->>p10: report.to_payload
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. render_doctor_text"]
    s2["2. _render_doctor_payload"]
    s3["3. isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)"]
    s4["4. isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)"]
    s5["5. isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)"]
    s6["6. isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)"]
    s7["7. isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)"]
    s8["8. isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)"]
    s9["9. _format_counts"]
    s10["10. isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)"]
    s11["11. ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)"]
    s12["12. lines.append"]
    s1 -->|"_render_doctor_payload(report.to_payload(...))"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)(availability, Mapping)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)(freshness, Mapping)" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)(snapshot, Mapping)" .-> s5
    s2 -. "isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)(governance, Mapping)" .-> s6
    s2 -. "isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)(drift, Mapping)" .-> s7
    s2 -. "isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)(verification, Mapping)" .-> s8
    s2 -->|"_format_counts(freshness[...])"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)(value, Mapping)" .-> s10
    s9 -. "', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)(...)" .-> s11
    s2 -. "lines.append(...)" .-> s12
    b0["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b0
    b1["mutation lines.extend"]
    s2 -. "mutation lines.extend" .-> b1
    b2["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b2
    b3["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b3
    click s1 "../modules/doctor_service.md"
    click s2 "../modules/doctor_service.md"
    click s9 "../modules/doctor_service.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `render_doctor_text` | `report: DoctorReport` | - | - | `_render_doctor_payload(...)` |
| `_render_doctor_payload` | `payload: Mapping[str, Any]` | `Mapping`, `Mapping`, `Mapping`, `Mapping`, `Mapping`, `Mapping` | - | `...` |
| `isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload)` | - | - | - | - |
| `_format_counts` | `value: object` | `Mapping`, `_FRESHNESS_STATES` | - | `None`, `...` |
| `isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)` | - | - | - | - |
| `', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)` | - | - | - | - |
| `lines.append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_doctor_text | _render_doctor_payload | 219 | `_render_doctor_payload(report.to_payload(...))` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload) | 229 | `isinstance(availability, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload) | 230 | `isinstance(freshness, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload) | 231 | `isinstance(snapshot, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload) | 232 | `isinstance(governance, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload) | 233 | `isinstance(drift, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services….py:_render_doctor_payload) | 234 | `isinstance(verification, Mapping)` |
| _render_doctor_payload | _format_counts | 236 | `_format_counts(freshness[...])` |
| _format_counts | isinstance (src/llm_wiki_cli/services…_service.py:_format_counts) | 654 | `isinstance(value, Mapping)` |
| _format_counts | ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts) | 656 | `', '.join(...)` |
| _render_doctor_payload | lines.append | 247 | `lines.append(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `lines.append` | `_render_doctor_payload` | 247 |
| mutation | `lines.extend` | `_render_doctor_payload` | 248 |
| mutation | `lines.append` | `_render_doctor_payload` | 275 |
| mutation | `lines.append` | `_render_doctor_payload` | 277 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_render_doctor_payload` | `isinstance` | 229 |
| external_call | `_render_doctor_payload` | `isinstance` | 230 |
| external_call | `_render_doctor_payload` | `isinstance` | 231 |
| external_call | `_render_doctor_payload` | `isinstance` | 232 |
| external_call | `_render_doctor_payload` | `isinstance` | 233 |
| external_call | `_render_doctor_payload` | `isinstance` | 234 |
| external_call | `_format_counts` | `isinstance` | 654 |
| unresolved_call | `_format_counts` | `', '.join` | 656 |
| step_limit | `render_doctor_text` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_doctor_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
