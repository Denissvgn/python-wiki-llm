# render_doctor_text

**Entry point:** `render_doctor_text` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [doctor_service](../modules/doctor_service.md), [health_summary](../modules/health_summary.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_doctor_text
    participant p1 as _render_doctor_payload
    participant p2 as assurance_rows
    participant p3 as detailed_health_rows
    participant p4 as captured_analysis_diagnostic
    participant p5 as analysis_diagnostic
    participant p6 as captured_components
    participant p7 as component_record
    participant p8 as _format_counts
    participant p9 as health_policy
    participant p10 as summary_cell
    participant p11 as optional_status
    participant p12 as reason_list
    participant p13 as detailed_health_rows.<locals>.value
    participant p14 as freshness_counts
    participant p15 as _versions
    participant p16 as validate_record
    participant p17 as configuration_commitment
    participant p18 as isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)
    participant p19 as report.to_payload
    participant p20 as dict
    participant p21 as lines.append
    participant p22 as lines.extend
    participant p23 as ', '.join (src/llm_wiki_cli/services…py:_render_doctor_payload)
    p0->>p1: _render_doctor_payload
    p1->>p2: assurance_rows
    p1->>p3: detailed_health_rows
    p3->>p4: captured_analysis_diagnostic
    p4->>p5: analysis_diagnostic
    p4->>p6: captured_components
    p5->>p7: component_record
    p1->>p8: _format_counts
    p1->>p9: health_policy
    p1->>p10: summary_cell
    p2->>p11: optional_status
    p2->>p12: reason_list
    p3->>p13: detailed_health_rows.<locals>.value
    p3->>p14: freshness_counts
    p3->>p15: _versions
    p6->>p16: validate_record
    p7->>p17: configuration_commitment
    p1-->>p18: isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(availability, Mapping)
    p0-->>p19: report.to_payload(report_schema=report_schema)
    p1-->>p18: isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(freshness, Mapping)
    p1-->>p18: isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(snapshot, Mapping)
    p1-->>p18: isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(governance, Mapping)
    p1-->>p18: isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(drift, Mapping)
    p1-->>p18: isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(verification, Mapping)
    p1-->>p20: dict(assurance_rows(...))
    p1-->>p21: lines.append(...)
    p1-->>p22: lines.extend([...])
    p1-->>p21: lines.append(...)
    p1-->>p21: lines.append(...)
    p1-->>p23: ', '.join (src/llm_wiki_cli/services…py:_render_doctor_payload)(payload[...])
```

> Call sequence diagram shows 30 of 128 interactions; 98 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 44 (37 omitted); unresolved 6 of 57 (51 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/health_summary.py:reason_list` | 12 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/health_summary.py:reason_list` | 12 | - | external | 2 |
| `src/llm_wiki_cli/services/health_summary.py:assurance_rows` | 10 | [src/llm_wiki_cli/services/health_summary.py](../modules/health_summary.md) | internal | 1 |
| `src/llm_wiki_cli/services/doctor_service.py:_format_counts` | 17 | - | external | 1 |
| `src/llm_wiki_cli/services/doctor_service.py:_format_counts` | 17 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/health_summary.py:summary_cell` | 23 | - | external | 7 |
| `src/llm_wiki_cli/services/health_summary.py:summary_cell` | 23 | - | unresolved | 8 |
| `src/llm_wiki_cli/services/doctor_service.py:_render_doctor_payload` | 2 | [src/llm_wiki_cli/services/health_summary.py](../modules/health_summary.md) | internal | 3 |
> Omission summary shows 8 of 26 groups; 18 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. render_doctor_text"]
    s2["2. _render_doctor_payload"]
    s3["3. isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)"]
    s4["4. isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)"]
    s5["5. isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)"]
    s6["6. isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)"]
    s7["7. isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)"]
    s8["8. isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)"]
    s9["9. dict"]
    s10["10. assurance_rows"]
    s11["11. optional_status"]
    s12["12. reason_list"]
    s1 -->|"_render_doctor_payload(report.to_payload(...))"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(availability, Mapping)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(freshness, Mapping)" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(snapshot, Mapping)" .-> s5
    s2 -. "isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(governance, Mapping)" .-> s6
    s2 -. "isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(drift, Mapping)" .-> s7
    s2 -. "isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)(verification, Mapping)" .-> s8
    s2 -. "dict(assurance_rows(...))" .-> s9
    s2 -->|"assurance_rows(payload)"| s10
    s10 -->|"optional_status(governance[...], absent='not-present')"| s11
    s10 -->|"reason_list(governance[...])"| s12
    b0["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b0
    b1["mutation lines.extend"]
    s2 -. "mutation lines.extend" .-> b1
    b2["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b2
    b3["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b3
    b4["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b4
    b5["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b5
    b6["mutation lines.append"]
    s2 -. "mutation lines.append" .-> b6
    b7["mutation lines.extend"]
    s2 -. "mutation lines.extend" .-> b7
    click s1 "../modules/doctor_service.md"
    click s2 "../modules/doctor_service.md"
    click s10 "../modules/health_summary.md"
    click s11 "../modules/health_summary.md"
    click s12 "../modules/health_summary.md"
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
| `render_doctor_text` | `report: DoctorReport`, `report_schema: str` | - | - | `_render_doctor_payload(...)` |
| `_render_doctor_payload` | `payload: Mapping[str, Any]` | `Mapping`, `Mapping`, `Mapping`, `Mapping`, `Mapping`, `Mapping`, `RELEASE_POLICY_UNAVAILABLE`, `ASSURANCE_DISCLOSURE` | - | `...` |
| `isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload)` | - | - | - | - |
| `dict` | - | - | - | - |
| `assurance_rows` | `report: Mapping` | - | - | `[...]` |
| `optional_status` | `state: str`, `absent: str` | - | - | `...` |
| `reason_list` | `reasons: Sequence[str]`, `limit: int` | - | - | `shown` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_doctor_text | _render_doctor_payload | 234 | `_render_doctor_payload(report.to_payload(...))` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload) | 244 | `isinstance(availability, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload) | 245 | `isinstance(freshness, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload) | 246 | `isinstance(snapshot, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload) | 247 | `isinstance(governance, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload) | 248 | `isinstance(drift, Mapping)` |
| _render_doctor_payload | isinstance (src/llm_wiki_cli/services…py:_render_doctor_payload) | 249 | `isinstance(verification, Mapping)` |
| _render_doctor_payload | dict | 250 | `dict(assurance_rows(...))` |
| _render_doctor_payload | assurance_rows | 250 | `assurance_rows(payload)` |
| assurance_rows | optional_status | 74 | `optional_status(governance[...], absent='not-present')` |
| assurance_rows | reason_list | 78 | `reason_list(governance[...])` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `lines.append` | `_render_doctor_payload` | 265 |
| mutation | `lines.extend` | `_render_doctor_payload` | 266 |
| mutation | `lines.append` | `_render_doctor_payload` | 292 |
| mutation | `lines.append` | `_render_doctor_payload` | 294 |
| mutation | `lines.append` | `_render_doctor_payload` | 296 |
| mutation | `lines.append` | `_render_doctor_payload` | 297 |
| mutation | `lines.append` | `_render_doctor_payload` | 298 |
| mutation | `lines.extend` | `_render_doctor_payload` | 299 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_render_doctor_payload` | `isinstance` | 244 |
| external_call | `_render_doctor_payload` | `isinstance` | 245 |
| external_call | `_render_doctor_payload` | `isinstance` | 246 |
| external_call | `_render_doctor_payload` | `isinstance` | 247 |
| external_call | `_render_doctor_payload` | `isinstance` | 248 |
| external_call | `_render_doctor_payload` | `isinstance` | 249 |
| step_limit | `render_doctor_text` | `first 12 steps` | 0 |
| truncated_flow | `render_doctor_text` | `depth limit` | 0 |

## Behavior

This flow starts at `render_doctor_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
