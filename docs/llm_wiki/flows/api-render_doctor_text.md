# render_doctor_text

**Entry point:** `render_doctor_text` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [doctor_service](../modules/doctor_service.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_doctor_text
    participant p1 as to_payload
    participant p2 as isinstance
    participant p3 as _format_counts
    participant p4 as join
    participant p5 as append
    participant p6 as extend
    p0-->>p1: to_payload
    p0-->>p2: isinstance
    p0-->>p2: isinstance
    p0-->>p2: isinstance
    p0-->>p2: isinstance
    p0-->>p2: isinstance
    p0-->>p2: isinstance
    p0->>p3: _format_counts
    p3-->>p2: isinstance
    p3-->>p4: join
    p0-->>p5: append
    p0-->>p6: extend
    p0-->>p5: append
    p0-->>p4: join
    p0-->>p5: append
    p0-->>p4: join
    p0-->>p4: join
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. render_doctor_text"]
    s2["2. to_payload"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s6["6. isinstance"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. _format_counts"]
    s10["10. isinstance"]
    s11["11. join"]
    s12["12. append"]
    s1 -. "report.to_payload(data not statically known)" .-> s2
    s1 -. "isinstance(availability, Mapping)" .-> s3
    s1 -. "isinstance(freshness, Mapping)" .-> s4
    s1 -. "isinstance(snapshot, Mapping)" .-> s5
    s1 -. "isinstance(governance, Mapping)" .-> s6
    s1 -. "isinstance(drift, Mapping)" .-> s7
    s1 -. "isinstance(verification, Mapping)" .-> s8
    s1 -->|"_format_counts(freshness[...])"| s9
    s9 -. "isinstance(value, Mapping)" .-> s10
    s9 -. "', '.join(...)" .-> s11
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
| `to_payload` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `_format_counts` | `value: object` | `Mapping`, `_FRESHNESS_STATES` | - | `None`, `...` |
| `isinstance` | - | - | - | - |
| `join` | - | - | - | - |
| `append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_doctor_text | to_payload | 219 | `report.to_payload(data not statically known)` |
| render_doctor_text | isinstance | 226 | `isinstance(availability, Mapping)` |
| render_doctor_text | isinstance | 227 | `isinstance(freshness, Mapping)` |
| render_doctor_text | isinstance | 228 | `isinstance(snapshot, Mapping)` |
| render_doctor_text | isinstance | 229 | `isinstance(governance, Mapping)` |
| render_doctor_text | isinstance | 230 | `isinstance(drift, Mapping)` |
| render_doctor_text | isinstance | 231 | `isinstance(verification, Mapping)` |
| render_doctor_text | _format_counts | 233 | `_format_counts(freshness[...])` |
| _format_counts | isinstance | 651 | `isinstance(value, Mapping)` |
| _format_counts | join | 653 | `', '.join(...)` |
| render_doctor_text | append | 244 | `lines.append(...)` |

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
| unresolved_call | `render_doctor_text` | `isinstance` | 226 |
| unresolved_call | `render_doctor_text` | `isinstance` | 227 |
| unresolved_call | `render_doctor_text` | `isinstance` | 228 |
| unresolved_call | `render_doctor_text` | `isinstance` | 229 |
| unresolved_call | `render_doctor_text` | `isinstance` | 230 |
| unresolved_call | `render_doctor_text` | `isinstance` | 231 |
| unresolved_call | `_format_counts` | `isinstance` | 651 |
| unresolved_call | `_format_counts` | `', '.join` | 653 |
| step_limit | `render_doctor_text` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_doctor_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
