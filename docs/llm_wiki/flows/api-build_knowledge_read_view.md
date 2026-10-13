# build_knowledge_read_view

**Entry point:** `build_knowledge_read_view` (`api`)
**Source:** [knowledge_consumption](../modules/knowledge_consumption.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [implementation_evidence](../modules/implementation_evidence.md), and 17 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_read_view
    participant p1 as _read_mode
    participant p2 as _validate_load_result
    participant p3 as _loaded_freshness
    participant p4 as _knowledge_counts
    participant p5 as _snapshot_maintenance_report
    participant p6 as _implementation_report
    participant p7 as KnowledgeReadView
    participant p8 as _unsupported_reason
    participant p9 as build_maintenance_status
    participant p10 as evaluate_knowledge_freshness
    participant p11 as marker_from_validated_state
    participant p12 as compare_knowledge_implementation
    participant p13 as parse_knowledge_index
    participant p14 as _knowledge_index_to_payload_unchecked
    participant p15 as _evaluate_model_freshness
    participant p16 as owner_key
    participant p17 as compare_implementation_observations
    participant p18 as _record
    participant p19 as _bundle_to_payload
    participant p20 as _validate_live_evaluation
    participant p21 as _string
    participant p22 as _parse_bundle
    participant p23 as _evaluate_concept
    participant p24 as _array (src/llm_wiki_cli/services/knowledge_model.py)
    participant p25 as _concept_to_payload
    participant p26 as _parse_concept
    participant p27 as _relationship_to_payload
    participant p28 as _parse_relationship
    participant p29 as isinstance (src/llm_wiki_cli/services…build_knowledge_read_view)
    participant p30 as evidence.get
    p0->>p1: _read_mode
    p0->>p2: _validate_load_result
    p0->>p3: _loaded_freshness
    p0->>p4: _knowledge_counts
    p0->>p5: _snapshot_maintenance_report
    p0->>p6: _implementation_report
    p0->>p7: KnowledgeReadView
    p0->>p8: _unsupported_reason
    p5->>p9: build_maintenance_status
    p3->>p10: evaluate_knowledge_freshness
    p5->>p11: marker_from_validated_state
    p6->>p12: compare_knowledge_implementation
    p10->>p13: parse_knowledge_index
    p10->>p14: _knowledge_index_to_payload_unchecked
    p10->>p15: _evaluate_model_freshness
    p9->>p16: owner_key
    p9->>p17: compare_implementation_observations
    p13->>p18: _record
    p14->>p19: _bundle_to_payload
    p15->>p20: _validate_live_evaluation
    p13->>p21: _string
    p13->>p22: _parse_bundle
    p15->>p23: _evaluate_concept
    p13->>p24: _array (src/llm_wiki_cli/services/knowledge_model.py)
    p14->>p25: _concept_to_payload
    p13->>p26: _parse_concept
    p14->>p27: _relationship_to_payload
    p13->>p28: _parse_relationship
    p0-->>p29: isinstance (src/llm_wiki_cli/services…build_knowledge_read_view)(load_result, KnowledgeLoadResult)
    p4-->>p30: evidence.get(state, 0)
```

> Call sequence diagram shows 30 of 1117 interactions; 1087 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 309 (308 omitted); unresolved 1 of 184 (183 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_consumption.py:build_knowledge_read_view` | 1 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_consumption.py:_read_mode` | 4 | - | external | 5 |
| `src/llm_wiki_cli/services/knowledge_consumption.py:_read_mode` | 4 | [src/llm_wiki_cli/services/knowledge_consumption.py](../modules/knowledge_consumption.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_consumption.py:_validate_load_result` | 11 | - | external | 18 |
| `src/llm_wiki_cli/services/knowledge_consumption.py:_validate_load_result` | 11 | [src/llm_wiki_cli/services/knowledge_consumption.py](../modules/knowledge_consumption.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_consumption.py:_unsupported_reason` | 29 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_consumption.py:_loaded_freshness` | 32 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:require_validated_artifacts` | 33 | - | external | 4 |
> Omission summary shows 8 of 219 groups; 211 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_knowledge_read_view"]
    s2["2. isinstance (src/llm_wiki_cli/services…build_knowledge_read_view)"]
    s3["3. TypeError (src/llm_wiki_cli/services…build_knowledge_read_view)"]
    s4["4. _read_mode"]
    s5["5. isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode)"]
    s6["6. TypeError (src/llm_wiki_cli/services…consumption.py:_read_mode)"]
    s7["7. isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode)"]
    s8["8. KnowledgeReadMode"]
    s9["9. ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode)"]
    s10["10. ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode)"]
    s11["11. _validate_load_result"]
    s12["12. isinstance (src/llm_wiki_cli/services….py:_validate_load_result)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…build_knowledge_read_view)(load_result, KnowledgeLoadResult)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…build_knowledge_read_view)('load_result must be a KnowledgeLoadResult')" .-> s3
    s1 -->|"_read_mode(snapshot_only=snapshot_only, mode=mode)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode)(snapshot_only, bool)" .-> s5
    s4 -. "TypeError (src/llm_wiki_cli/services…consumption.py:_read_mode)('snapshot_only must be a boolean')" .-> s6
    s4 -. "isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode)(mode, KnowledgeReadMode)" .-> s7
    s4 -->|"KnowledgeReadMode(mode)"| s8
    s4 -. "ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode)(#34;mode must be 'evaluate-freshness' or 'snapshot-only'#34;)" .-> s9
    s4 -. "ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode)('snapshot_only conflicts with the requested mode')" .-> s10
    s1 -->|"_validate_load_result(load_result)"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services….py:_validate_load_result)(result.status, KnowledgeLoadState)" .-> s12
    click s1 "../modules/knowledge_consumption.md"
    click s4 "../modules/knowledge_consumption.md"
    click s8 "../modules/knowledge_consumption.md"
    click s11 "../modules/knowledge_consumption.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_read_view` | `load_result: KnowledgeLoadResult`, `live_evaluation: LiveKnowledgeEvaluation \| None`, `snapshot_only: bool`, `mode: KnowledgeReadMode \| str \| None` | `KnowledgeLoadResult`, `KnowledgeLoadState`, `KnowledgeLoadState`, `KnowledgeReadMode`, `KnowledgeAvailability`, `KnowledgeReadReason`, `KnowledgeReadMode`, `KnowledgeLoadState` | - | `KnowledgeReadView(...)`, `KnowledgeReadView(...)`, `KnowledgeReadView(...)` |
| `isinstance (src/llm_wiki_cli/services…build_knowledge_read_view)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…build_knowledge_read_view)` | - | - | - | - |
| `_read_mode` | `snapshot_only: bool`, `mode: KnowledgeReadMode \| str \| None` | `KnowledgeReadMode`, `KnowledgeReadMode`, `KnowledgeReadMode`, `KnowledgeReadMode` | - | `...`, `selected` |
| `isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…consumption.py:_read_mode)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode)` | - | - | - | - |
| `KnowledgeReadMode` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode)` | - | - | - | - |
| `_validate_load_result` | `result: KnowledgeLoadResult` | `KnowledgeLoadState`, `KnowledgeLoadState`, `KnowledgeLoadIssue`, `KnowledgeLoadState`, `Mapping`, `KnowledgeIndex`, `SyncManifest`, `KnowledgeLoadState` | - | `none`, `none`, `none`, `none` |
| `isinstance (src/llm_wiki_cli/services….py:_validate_load_result)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_read_view | isinstance (src/llm_wiki_cli/services…build_knowledge_read_view) | 587 | `isinstance(load_result, KnowledgeLoadResult)` |
| build_knowledge_read_view | TypeError (src/llm_wiki_cli/services…build_knowledge_read_view) | 588 | `TypeError('load_result must be a KnowledgeLoadResult')` |
| build_knowledge_read_view | _read_mode | 589 | `_read_mode(snapshot_only=snapshot_only, mode=mode)` |
| _read_mode | isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode) | 734 | `isinstance(snapshot_only, bool)` |
| _read_mode | TypeError (src/llm_wiki_cli/services…consumption.py:_read_mode) | 735 | `TypeError('snapshot_only must be a boolean')` |
| _read_mode | isinstance (src/llm_wiki_cli/services…consumption.py:_read_mode) | 745 | `isinstance(mode, KnowledgeReadMode)` |
| _read_mode | KnowledgeReadMode | 746 | `KnowledgeReadMode(mode)` |
| _read_mode | ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode) | 749 | `ValueError("mode must be 'evaluate-freshness' or 'snapshot-only'")` |
| _read_mode | ValueError (src/llm_wiki_cli/services…consumption.py:_read_mode) | 753 | `ValueError('snapshot_only conflicts with the requested mode')` |
| build_knowledge_read_view | _validate_load_result | 590 | `_validate_load_result(load_result)` |
| _validate_load_result | isinstance (src/llm_wiki_cli/services….py:_validate_load_result) | 854 | `isinstance(result.status, KnowledgeLoadState)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_knowledge_read_view` | `isinstance` | 587 |
| external_call | `build_knowledge_read_view` | `TypeError` | 588 |
| external_call | `_read_mode` | `isinstance` | 734 |
| external_call | `_read_mode` | `TypeError` | 735 |
| external_call | `_read_mode` | `isinstance` | 745 |
| external_call | `_read_mode` | `ValueError` | 749 |
| external_call | `_read_mode` | `ValueError` | 753 |
| external_call | `_validate_load_result` | `isinstance` | 854 |
| step_limit | `build_knowledge_read_view` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
