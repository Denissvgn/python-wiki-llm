# summarize_knowledge_view

**Entry point:** `summarize_knowledge_view` (`api`)
**Source:** [knowledge_observability](../modules/knowledge_observability.md)
**Modules touched:** [knowledge_observability](../modules/knowledge_observability.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as summarize_knowledge_view
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as KnowledgePhaseDurations
    participant p4 as int
    participant p5 as view.freshness.counts.items
    participant p6 as sum
    participant p7 as freshness_counts.values
    participant p8 as view.counts.evidence_by_state.get
    participant p9 as KnowledgeAggregateSummary
    participant p10 as selected_durations.to_payload
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: KnowledgePhaseDurations
    p0-->>p4: int
    p0-->>p5: view.freshness.counts.items
    p0-->>p6: sum
    p0-->>p7: freshness_counts.values
    p0-->>p4: int
    p0-->>p8: view.counts.evidence_by_state.get
    p0->>p9: KnowledgeAggregateSummary
    p0-->>p10: selected_durations.to_payload
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. summarize_knowledge_view"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. KnowledgePhaseDurations"]
    s5["5. int"]
    s6["6. view.freshness.counts.items"]
    s7["7. sum"]
    s8["8. freshness_counts.values"]
    s9["9. int"]
    s10["10. view.counts.evidence_by_state.get"]
    s11["11. KnowledgeAggregateSummary"]
    s12["12. selected_durations.to_payload"]
    s1 -. "isinstance(view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError('view must be a KnowledgeReadView')" .-> s3
    s1 -->|"KnowledgePhaseDurations(data not statically known)"| s4
    s1 -. "int(count)" .-> s5
    s1 -. "view.freshness.counts.items(data not statically known)" .-> s6
    s1 -. "sum(freshness_counts.values(...))" .-> s7
    s1 -. "freshness_counts.values(data not statically known)" .-> s8
    s1 -. "int(view.counts.evidence_by_state.get(...))" .-> s9
    s1 -. "view.counts.evidence_by_state.get(state, 0)" .-> s10
    s1 -->|"KnowledgeAggregateSummary(…)"| s11
    s1 -. "selected_durations.to_payload(data not statically known)" .-> s12
    click s1 "../modules/knowledge_observability.md"
    click s4 "../modules/knowledge_observability.md"
    click s11 "../modules/knowledge_observability.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `summarize_knowledge_view` | `view: KnowledgeReadView`, `durations: KnowledgePhaseDurations \| None` | `KnowledgeReadView`, `_EVIDENCE_ISSUE_STATES`, `KnowledgeAvailability` | - | `KnowledgeAggregateSummary(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `KnowledgePhaseDurations` | - | - | - | - |
| `int` | - | - | - | - |
| `view.freshness.counts.items` | - | - | - | - |
| `sum` | - | - | - | - |
| `freshness_counts.values` | - | - | - | - |
| `int` | - | - | - | - |
| `view.counts.evidence_by_state.get` | - | - | - | - |
| `KnowledgeAggregateSummary` | - | - | - | - |
| `selected_durations.to_payload` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| summarize_knowledge_view | isinstance | 403 | `isinstance(view, KnowledgeReadView)` |
| summarize_knowledge_view | TypeError | 404 | `TypeError('view must be a KnowledgeReadView')` |
| summarize_knowledge_view | KnowledgePhaseDurations | 405 | `KnowledgePhaseDurations(data not statically known)` |
| summarize_knowledge_view | int | 409 | `int(count)` |
| summarize_knowledge_view | view.freshness.counts.items | 409 | `view.freshness.counts.items(data not statically known)` |
| summarize_knowledge_view | sum | 412 | `sum(freshness_counts.values(...))` |
| summarize_knowledge_view | freshness_counts.values | 412 | `freshness_counts.values(data not statically known)` |
| summarize_knowledge_view | int | 418 | `int(view.counts.evidence_by_state.get(...))` |
| summarize_knowledge_view | view.counts.evidence_by_state.get | 418 | `view.counts.evidence_by_state.get(state, 0)` |
| summarize_knowledge_view | KnowledgeAggregateSummary | 428 | `KnowledgeAggregateSummary(availability=view.availability.value, reason=view.reason_code, concepts_evaluated=concepts_evaluated, freshness_counts=freshness_counts, evidence_issue_counts=evidence_issue_counts, degraded_reason=degraded_reason, phase_durations_ms=selected_durations.to_payload(...), freshness_evaluated=view.freshness_evaluated)` |
| summarize_knowledge_view | selected_durations.to_payload | 435 | `selected_durations.to_payload(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `summarize_knowledge_view` | `isinstance` | 403 |
| external_call | `summarize_knowledge_view` | `TypeError` | 404 |
| unresolved_call | `summarize_knowledge_view` | `view.freshness.counts.items` | 409 |
| external_call | `summarize_knowledge_view` | `sum` | 412 |
| unresolved_call | `summarize_knowledge_view` | `freshness_counts.values` | 412 |
| unresolved_call | `summarize_knowledge_view` | `view.counts.evidence_by_state.get` | 418 |
| unresolved_call | `summarize_knowledge_view` | `selected_durations.to_payload` | 435 |

## Behavior

This flow starts at `summarize_knowledge_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
