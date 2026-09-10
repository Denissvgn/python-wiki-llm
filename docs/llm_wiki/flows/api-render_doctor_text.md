# render_doctor_text

**Entry point:** `render_doctor_text` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [doctor_service](../modules/doctor_service.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_doctor_text
    participant p1 as report.to_payload
    participant p2 as isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    participant p3 as _format_counts
    participant p4 as isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)
    participant p5 as ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)
    participant p6 as lines.append
    participant p7 as lines.extend
    participant p8 as ', '.join (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    participant p9 as '\n'.join
    p0-->>p1: report.to_payload
    p0-->>p2: isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0->>p3: _format_counts
    p3-->>p4: isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)
    p3-->>p5: ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)
    p0-->>p6: lines.append
    p0-->>p7: lines.extend
    p0-->>p6: lines.append
    p0-->>p8: ', '.join (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p6: lines.append
    p0-->>p8: ', '.join (src/llm_wiki_cli/services…vice.py:render_doctor_text)
    p0-->>p9: '\n'.join
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. render_doctor_text"]
    s2["2. report.to_payload"]
    s3["3. isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)"]
    s4["4. isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)"]
    s5["5. isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)"]
    s6["6. isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)"]
    s7["7. isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)"]
    s8["8. isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)"]
    s9["9. _format_counts"]
    s10["10. isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)"]
    s11["11. ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)"]
    s12["12. lines.append"]
    s1 -. "report.to_payload(data not statically known)" .-> s2
    s1 -. "isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)(availability, Mapping)" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)(freshness, Mapping)" .-> s4
    s1 -. "isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)(snapshot, Mapping)" .-> s5
    s1 -. "isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)(governance, Mapping)" .-> s6
    s1 -. "isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)(drift, Mapping)" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)(verification, Mapping)" .-> s8
    s1 -->|"_format_counts(freshness[...])"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)(value, Mapping)" .-> s10
    s9 -. "', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)(...)" .-> s11
    s1 -. "lines.append(...)" .-> s12
    b0["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b0
    b1["mutation lines.extend"]
    s1 -. "mutation lines.extend" .-> b1
    b2["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b2
    b3["mutation lines.append"]
    s1 -. "mutation lines.append" .-> b3
    click s1 "../modules/doctor_service.md"
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
| `render_doctor_text` | `report: DoctorReport` | `Mapping`, `Mapping`, `Mapping`, `Mapping`, `Mapping`, `Mapping` | - | `...` |
| `report.to_payload` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text)` | - | - | - | - |
| `_format_counts` | `value: object` | `Mapping`, `_FRESHNESS_STATES` | - | `None`, `...` |
| `isinstance (src/llm_wiki_cli/services…_service.py:_format_counts)` | - | - | - | - |
| `', '.join (src/llm_wiki_cli/services…_service.py:_format_counts)` | - | - | - | - |
| `lines.append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_doctor_text | report.to_payload | 219 | `report.to_payload(data not statically known)` |
| render_doctor_text | isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text) | 226 | `isinstance(availability, Mapping)` |
| render_doctor_text | isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text) | 227 | `isinstance(freshness, Mapping)` |
| render_doctor_text | isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text) | 228 | `isinstance(snapshot, Mapping)` |
| render_doctor_text | isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text) | 229 | `isinstance(governance, Mapping)` |
| render_doctor_text | isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text) | 230 | `isinstance(drift, Mapping)` |
| render_doctor_text | isinstance (src/llm_wiki_cli/services…vice.py:render_doctor_text) | 231 | `isinstance(verification, Mapping)` |
| render_doctor_text | _format_counts | 233 | `_format_counts(freshness[...])` |
| _format_counts | isinstance (src/llm_wiki_cli/services…_service.py:_format_counts) | 651 | `isinstance(value, Mapping)` |
| _format_counts | ', '.join (src/llm_wiki_cli/services…_service.py:_format_counts) | 653 | `', '.join(...)` |
| render_doctor_text | lines.append | 244 | `lines.append(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `lines.append` | `render_doctor_text` | 244 |
| mutation | `lines.extend` | `render_doctor_text` | 245 |
| mutation | `lines.append` | `render_doctor_text` | 272 |
| mutation | `lines.append` | `render_doctor_text` | 274 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `render_doctor_text` | `report.to_payload` | 219 |
| external_call | `render_doctor_text` | `isinstance` | 226 |
| external_call | `render_doctor_text` | `isinstance` | 227 |
| external_call | `render_doctor_text` | `isinstance` | 228 |
| external_call | `render_doctor_text` | `isinstance` | 229 |
| external_call | `render_doctor_text` | `isinstance` | 230 |
| external_call | `render_doctor_text` | `isinstance` | 231 |
| external_call | `_format_counts` | `isinstance` | 651 |
| unresolved_call | `_format_counts` | `', '.join` | 653 |
| step_limit | `render_doctor_text` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_doctor_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
