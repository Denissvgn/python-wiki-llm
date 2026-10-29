# build_runtime_live_evaluation

**Entry point:** `build_runtime_live_evaluation` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), and 10 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [normalization_diagnostics](../modules/normalization_diagnostics.md)
- [python_implementation](../modules/python_implementation.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_runtime_live_evaluation
    participant p1 as has_contract
    participant p2 as _producer_evidence
    participant p3 as _infrastructure_extractor_component
    participant p4 as build_producer_record
    participant p5 as _tool_component
    participant p6 as prepare_runtime_generation_options
    participant p7 as hash_generation_options
    participant p8 as analysis_identity
    participant p9 as _runtime_live_concept_bases
    participant p10 as current_infrastructure_bases
    participant p11 as LiveKnowledgeEvaluation
    participant p12 as component_record
    participant p13 as _build_component
    participant p14 as build_infrastructure_page_map
    participant p15 as _plugin_extractors_by_language
    participant p16 as build_infrastructure_observation_basis
    participant p17 as _source_hash
    participant p18 as _observation_hash
    participant p19 as _normalized_allowlist
    participant p20 as build_module_observation_basis
    participant p21 as _reject_unknown_option_keys
    participant p22 as build_entity_observation_basis
    participant p23 as _digest
    participant p24 as attach
    participant p25 as plugin_producer_inputs
    participant p26 as _validate_basis_inputs
    participant p27 as _unknown_basis
    participant p28 as _validate_entity_coordinate
    participant p29 as isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)
    participant p30 as inputs.infrastructure_inventory.items
    p0->>p1: has_contract
    p0->>p2: _producer_evidence
    p0->>p3: _infrastructure_extractor_component
    p0->>p4: build_producer_record
    p0->>p5: _tool_component
    p0->>p6: prepare_runtime_generation_options
    p0->>p7: hash_generation_options
    p0->>p8: analysis_identity
    p0->>p9: _runtime_live_concept_bases
    p0->>p10: current_infrastructure_bases
    p0->>p11: LiveKnowledgeEvaluation
    p1->>p12: component_record
    p4->>p13: _build_component
    p10->>p14: build_infrastructure_page_map
    p2->>p15: _plugin_extractors_by_language
    p10->>p16: build_infrastructure_observation_basis
    p10->>p17: _source_hash
    p10->>p18: _observation_hash
    p7->>p19: _normalized_allowlist
    p9->>p20: build_module_observation_basis
    p7->>p21: _reject_unknown_option_keys
    p9->>p22: build_entity_observation_basis
    p8->>p23: _digest
    p2->>p24: attach
    p2->>p25: plugin_producer_inputs
    p20->>p26: _validate_basis_inputs
    p20->>p27: _unknown_basis
    p22->>p28: _validate_entity_coordinate
    p0-->>p29: isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs, RuntimeLiveEvaluationInputs)
    p0-->>p30: inputs.infrastructure_inventory.items
```

> Call sequence diagram shows 30 of 696 interactions; 666 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 230 (229 omitted); unresolved 1 of 147 (146 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_orchestration.py:build_runtime_live_evaluation` | 1 | - | external | 18 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:component_record` | 15 | - | external | 4 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:component_record` | 15 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:component_record` | 15 | [src/llm_wiki_cli/services/analysis_compatibility.py](../modules/analysis_compatibility.md) | internal | 2 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:validate_record` | 20 | - | external | 22 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:validate_record` | 20 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:validate_record` | 20 | [src/llm_wiki_cli/services/analysis_compatibility.py](../modules/analysis_compatibility.md) | internal | 1 |
| `src/llm_wiki_cli/services/analysis_compatibility.py:digest` | 43 | - | unresolved | 2 |
> Omission summary shows 8 of 181 groups; 173 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_runtime_live_evaluation"]
    s2["2. isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s3["3. TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s4["4. isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s5["5. TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s6["6. isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s7["7. TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s8["8. isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s9["9. TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s10["10. isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s11["11. TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s12["12. isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs, RuntimeLiveEvaluationInputs)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)('inputs must be a RuntimeLiveEvaluationInputs')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs.knowledge, KnowledgeIndex)" .-> s4
    s1 -. "TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)('inputs.knowledge must be a KnowledgeIndex')" .-> s5
    s1 -. "isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs.manifest, SyncManifest)" .-> s6
    s1 -. "TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)('inputs.manifest must be a SyncManifest')" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs.source_snapshot, SourceSnapshot)" .-> s8
    s1 -. "TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)('inputs.source_snapshot must be a SourceSnapshot')" .-> s9
    s1 -. "isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs.inventory, Mapping)" .-> s10
    s1 -. "TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)('inputs.inventory must be a mapping')" .-> s11
    s1 -. "isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)(inputs.infrastructure_inventory, Mapping)" .-> s12
    click s1 "../modules/knowledge_orchestration.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_runtime_live_evaluation` | `inputs: RuntimeLiveEvaluationInputs` | `RuntimeLiveEvaluationInputs`, `KnowledgeIndex`, `SyncManifest`, `SourceSnapshot`, `Mapping`, `Mapping`, `ObservationScope`, `__version__` | `source_hashes[...]` | `LiveKnowledgeEvaluation(...)` |
| `isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_runtime_live_evaluation | isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 600 | `isinstance(inputs, RuntimeLiveEvaluationInputs)` |
| build_runtime_live_evaluation | TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 601 | `TypeError('inputs must be a RuntimeLiveEvaluationInputs')` |
| build_runtime_live_evaluation | isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 602 | `isinstance(inputs.knowledge, KnowledgeIndex)` |
| build_runtime_live_evaluation | TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 603 | `TypeError('inputs.knowledge must be a KnowledgeIndex')` |
| build_runtime_live_evaluation | isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 604 | `isinstance(inputs.manifest, SyncManifest)` |
| build_runtime_live_evaluation | TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 605 | `TypeError('inputs.manifest must be a SyncManifest')` |
| build_runtime_live_evaluation | isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 606 | `isinstance(inputs.source_snapshot, SourceSnapshot)` |
| build_runtime_live_evaluation | TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 607 | `TypeError('inputs.source_snapshot must be a SourceSnapshot')` |
| build_runtime_live_evaluation | isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 608 | `isinstance(inputs.inventory, Mapping)` |
| build_runtime_live_evaluation | TypeError (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 609 | `TypeError('inputs.inventory must be a mapping')` |
| build_runtime_live_evaluation | isinstance (src/llm_wiki_cli/services…d_runtime_live_evaluation) | 610 | `isinstance(inputs.infrastructure_inventory, Mapping)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_runtime_live_evaluation` | `isinstance` | 600 |
| external_call | `build_runtime_live_evaluation` | `TypeError` | 601 |
| external_call | `build_runtime_live_evaluation` | `isinstance` | 602 |
| external_call | `build_runtime_live_evaluation` | `TypeError` | 603 |
| external_call | `build_runtime_live_evaluation` | `isinstance` | 604 |
| external_call | `build_runtime_live_evaluation` | `TypeError` | 605 |
| external_call | `build_runtime_live_evaluation` | `isinstance` | 606 |
| external_call | `build_runtime_live_evaluation` | `TypeError` | 607 |
| external_call | `build_runtime_live_evaluation` | `isinstance` | 608 |
| external_call | `build_runtime_live_evaluation` | `TypeError` | 609 |
| external_call | `build_runtime_live_evaluation` | `isinstance` | 610 |
| step_limit | `build_runtime_live_evaluation` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_runtime_live_evaluation` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
