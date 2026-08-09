# build_knowledge_read_view

**Entry point:** `build_knowledge_read_view` (`api`)
**Source:** [knowledge_consumption](../modules/knowledge_consumption.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 9 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_read_view
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _read_mode
    participant p4 as KnowledgeReadMode
    participant p5 as ValueError
    participant p6 as _validate_load_result
    participant p7 as any
    participant p8 as _unsupported_reason
    participant p9 as get
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: _read_mode
    p3-->>p1: isinstance
    p3-->>p2: TypeError
    p3-->>p1: isinstance
    p3->>p4: KnowledgeReadMode
    p3-->>p5: ValueError
    p3-->>p5: ValueError
    p0->>p6: _validate_load_result
    p6-->>p1: isinstance
    p6-->>p2: TypeError
    p6-->>p1: isinstance
    p6-->>p2: TypeError
    p6-->>p1: isinstance
    p6-->>p7: any
    p6-->>p1: isinstance
    p6-->>p2: TypeError
    p6-->>p1: isinstance
    p6-->>p1: isinstance
    p6-->>p1: isinstance
    p6-->>p5: ValueError
    p6-->>p1: isinstance
    p6-->>p1: isinstance
    p6-->>p5: ValueError
    p6-->>p1: isinstance
    p6-->>p5: ValueError
    p6->>p8: _unsupported_reason
    p8-->>p9: get
    p6-->>p5: ValueError
```

> Call sequence diagram shows 30 of 1204 interactions; 1174 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_knowledge_read_view"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _read_mode"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. isinstance"]
    s8["8. KnowledgeReadMode"]
    s9["9. ValueError"]
    s10["10. ValueError"]
    s11["11. _validate_load_result"]
    s12["12. isinstance"]
    s1 -. "isinstance(load_result, KnowledgeLoadResult)" .-> s2
    s1 -. "TypeError('load_result must be a KnowledgeLoadResult')" .-> s3
    s1 -->|"_read_mode(snapshot_only=snapshot_only, mode=mode)"| s4
    s4 -. "isinstance(snapshot_only, bool)" .-> s5
    s4 -. "TypeError('snapshot_only must be a boolean')" .-> s6
    s4 -. "isinstance(mode, KnowledgeReadMode)" .-> s7
    s4 -->|"KnowledgeReadMode(mode)"| s8
    s4 -. "ValueError(#34;mode must be 'evaluate-freshness' or 'snapshot-only'#34;)" .-> s9
    s4 -. "ValueError('snapshot_only conflicts with the requested mode')" .-> s10
    s1 -->|"_validate_load_result(load_result)"| s11
    s11 -. "isinstance(result.status, KnowledgeLoadState)" .-> s12
    click s1 "../modules/knowledge_consumption.md"
    click s4 "../modules/knowledge_consumption.md"
    click s8 "../modules/knowledge_consumption.md"
    click s11 "../modules/knowledge_consumption.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_read_view` | `load_result: KnowledgeLoadResult`, `live_evaluation: LiveKnowledgeEvaluation \| None`, `snapshot_only: bool`, `mode: KnowledgeReadMode \| str \| None` | `KnowledgeLoadResult`, `KnowledgeLoadState`, `KnowledgeLoadState`, `KnowledgeReadMode`, `KnowledgeAvailability`, `KnowledgeReadReason`, `KnowledgeLoadState`, `KnowledgeAvailability` | - | `KnowledgeReadView(...)`, `KnowledgeReadView(...)`, `KnowledgeReadView(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_read_mode` | `snapshot_only: bool`, `mode: KnowledgeReadMode \| str \| None` | `KnowledgeReadMode`, `KnowledgeReadMode`, `KnowledgeReadMode`, `KnowledgeReadMode` | - | `...`, `selected` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeReadMode` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `_validate_load_result` | `result: KnowledgeLoadResult` | `KnowledgeLoadState`, `KnowledgeLoadState`, `KnowledgeLoadIssue`, `KnowledgeLoadState`, `Mapping`, `KnowledgeIndex`, `SyncManifest`, `KnowledgeLoadState` | - | `none`, `none`, `none`, `none` |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_read_view | isinstance | 574 | `isinstance(load_result, KnowledgeLoadResult)` |
| build_knowledge_read_view | TypeError | 575 | `TypeError('load_result must be a KnowledgeLoadResult')` |
| build_knowledge_read_view | _read_mode | 576 | `_read_mode(snapshot_only=snapshot_only, mode=mode)` |
| _read_mode | isinstance | 719 | `isinstance(snapshot_only, bool)` |
| _read_mode | TypeError | 720 | `TypeError('snapshot_only must be a boolean')` |
| _read_mode | isinstance | 730 | `isinstance(mode, KnowledgeReadMode)` |
| _read_mode | KnowledgeReadMode | 731 | `KnowledgeReadMode(mode)` |
| _read_mode | ValueError | 734 | `ValueError("mode must be 'evaluate-freshness' or 'snapshot-only'")` |
| _read_mode | ValueError | 738 | `ValueError('snapshot_only conflicts with the requested mode')` |
| build_knowledge_read_view | _validate_load_result | 577 | `_validate_load_result(load_result)` |
| _validate_load_result | isinstance | 743 | `isinstance(result.status, KnowledgeLoadState)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_knowledge_read_view` | `isinstance` | 574 |
| unresolved_call | `build_knowledge_read_view` | `TypeError` | 575 |
| unresolved_call | `_read_mode` | `isinstance` | 719 |
| unresolved_call | `_read_mode` | `TypeError` | 720 |
| unresolved_call | `_read_mode` | `isinstance` | 730 |
| unresolved_call | `_read_mode` | `ValueError` | 734 |
| unresolved_call | `_read_mode` | `ValueError` | 738 |
| unresolved_call | `_validate_load_result` | `isinstance` | 743 |
| step_limit | `build_knowledge_read_view` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
