# build_knowledge_index

**Entry point:** `build_knowledge_index` (`api`)
**Source:** [knowledge_index](../modules/knowledge_index.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [immutable](../modules/immutable.md), and 22 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [markdown_sections](../modules/markdown_sections.md)
- [progress](../modules/progress.md)
- [python_implementation](../modules/python_implementation.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_index
    participant p1 as _assemble_knowledge_index
    participant p2 as _validator_identity
    participant p3 as validate_knowledge_index
    participant p4 as freeze
    participant p5 as _serialize_payload
    participant p6 as _model_to_payload
    participant p7 as _ValidatedIndexReceipt
    participant p8 as _IndexValidationProof
    participant p9 as KnowledgeIndexBuildError
    participant p10 as _validate_and_join_inputs
    participant p11 as maintenance_core
    participant p12 as parse_knowledge_index
    participant p13 as _concept_for_page
    participant p14 as _validation_module_identity
    participant p15 as _derived_relationship
    participant p16 as _validate_builder_model
    participant p17 as _link_relationship
    participant p18 as _first_difference
    participant p19 as concept_kind_for_page_kind
    participant p20 as _record
    participant p21 as _knowledge_index_to_payload_unchecked
    participant p22 as _string
    participant p23 as _validated_bundle
    participant p24 as _validated_pages
    participant p25 as _parse_bundle
    participant p26 as _validated_content
    participant p27 as _structural_facet
    participant p28 as _validate_snapshot_commitments
    participant p29 as TypeError (src/llm_wiki_cli/services….py:build_knowledge_index)
    participant p30 as _INDEX_VALIDATION_OPERATION.get
    p0->>p1: _assemble_knowledge_index
    p0->>p2: _validator_identity
    p0->>p3: validate_knowledge_index
    p0->>p4: freeze
    p0->>p5: _serialize_payload
    p0->>p6: _model_to_payload
    p0->>p7: _ValidatedIndexReceipt
    p0->>p8: _IndexValidationProof
    p0->>p9: KnowledgeIndexBuildError
    p1->>p10: _validate_and_join_inputs
    p2->>p11: maintenance_core
    p3->>p12: parse_knowledge_index
    p1->>p13: _concept_for_page
    p2->>p14: _validation_module_identity
    p1->>p15: _derived_relationship
    p3->>p16: _validate_builder_model
    p1->>p17: _link_relationship
    p3->>p18: _first_difference
    p13->>p19: concept_kind_for_page_kind
    p12->>p20: _record
    p6->>p21: _knowledge_index_to_payload_unchecked
    p12->>p22: _string
    p10->>p23: _validated_bundle
    p10->>p24: _validated_pages
    p12->>p25: _parse_bundle
    p10->>p26: _validated_content
    p13->>p27: _structural_facet
    p10->>p28: _validate_snapshot_commitments
    p0-->>p29: TypeError (src/llm_wiki_cli/services….py:build_knowledge_index)('knowledge validators changed during builder validation')
    p0-->>p30: _INDEX_VALIDATION_OPERATION.get
```

> Call sequence diagram shows 30 of 1875 interactions; 1845 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 519 (518 omitted); unresolved 1 of 288 (287 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_index.py:_validate_and_join_inputs` | 3 | - | external | 6 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validated_bundle` | 6 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validated_bundle` | 6 | [src/llm_wiki_cli/services/knowledge_index.py](../modules/knowledge_index.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validated_bundle` | 6 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:evaluated_envelope_to_payload` | 9 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:evaluated_envelope_to_payload` | 9 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_bundle_payload` | 13 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_bundle_payload` | 13 | - | unresolved | 1 |
> Omission summary shows 8 of 435 groups; 427 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1069; effect analysis evaluated: 599, partial: 30, unavailable: 440. Counts include steps omitted from the displayed trace.

Collector observations for 629 source steps with known totals: observed: 3264, emitted: 3032, omitted: 232. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `build_knowledge_index` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_assemble_knowledge_index` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_validate_and_join_inputs` | `available` | `evaluated` | `available` | `11` | `11` | `0` |
| `isinstance (src/llm_wiki_cli/services…_validate_and_join_inputs)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…_validate_and_join_inputs)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validated_bundle` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…ndex.py:_validated_bundle)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeIndexBuildError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `evaluated_envelope_to_payload` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. build_knowledge_index"]
    s2["2. _assemble_knowledge_index"]
    s3["3. _validate_and_join_inputs"]
    s4["4. isinstance (src/llm_wiki_cli/services…_validate_and_join_inputs)"]
    s5["5. TypeError (src/llm_wiki_cli/services…_validate_and_join_inputs)"]
    s6["6. _validated_bundle"]
    s7["7. isinstance (src/llm_wiki_cli/services…ndex.py:_validated_bundle)"]
    s8["8. KnowledgeIndexBuildError"]
    s9["9. evaluated_envelope_to_payload"]
    s10["10. isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)"]
    s11["11. TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)"]
    s12["12. KnowledgeEnvelopeError"]
    s1 -->|"_assemble_knowledge_index(inputs)"| s2
    s2 -->|"_validate_and_join_inputs(inputs)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…_validate_and_join_inputs)(inputs, KnowledgeIndexInputs)" .-> s4
    s3 -. "TypeError (src/llm_wiki_cli/services…_validate_and_join_inputs)('inputs must be a KnowledgeIndexInputs')" .-> s5
    s3 -->|"_validated_bundle(inputs.envelope)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…ndex.py:_validated_bundle)(envelope, EvaluatedEnvelope)" .-> s7
    s6 -->|"KnowledgeIndexBuildError('envelope', 'must be an already evaluated envelope')"| s8
    s6 -->|"evaluated_envelope_to_payload(envelope)"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)(envelope, EvaluatedEnvelope)" .-> s10
    s9 -. "TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)('envelope must be an EvaluatedEnvelope')" .-> s11
    s9 -->|"KnowledgeEnvelopeError('schema_version', ...)"| s12
    b0["mutation relationships.extend"]
    s2 -. "mutation relationships.extend" .-> b0
    b1["mutation joined.append"]
    s3 -. "mutation joined.append" .-> b1
    b2["mutation joined.sort"]
    s3 -. "mutation joined.sort" .-> b2
    click s1 "../modules/knowledge_index.md"
    click s2 "../modules/knowledge_index.md"
    click s3 "../modules/knowledge_index.md"
    click s6 "../modules/knowledge_index.md"
    click s8 "../modules/knowledge_index.md"
    click s9 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_index` | `inputs: KnowledgeIndexInputs` | `_INDEX_RECEIPT_ISSUER`, `KnowledgeModelError` | - | `validated` |
| `_assemble_knowledge_index` | `inputs: KnowledgeIndexInputs` | `KNOWLEDGE_SCHEMA_VERSION` | - | `model` |
| `_validate_and_join_inputs` | `inputs: KnowledgeIndexInputs` | `KnowledgeIndexInputs`, `ManifestPageSource`, `ManifestEvidenceBaseline`, `ManifestTombstone`, `ConceptObservationBasis`, `_MANIFEST_STRUCTURAL_PAGE_KINDS`, `PageKind` | - | `_BuildContext(...)` |
| `isinstance (src/llm_wiki_cli/services…_validate_and_join_inputs)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…_validate_and_join_inputs)` | - | - | - | - |
| `_validated_bundle` | `envelope: object` | `EvaluatedEnvelope`, `KnowledgeEnvelopeError` | - | `envelope.bundle` |
| `isinstance (src/llm_wiki_cli/services…ndex.py:_validated_bundle)` | - | - | - | - |
| `KnowledgeIndexBuildError` | - | - | - | - |
| `evaluated_envelope_to_payload` | `envelope: EvaluatedEnvelope` | `EvaluatedEnvelope`, `EVALUATED_ENVELOPE_VERSION`, `EVALUATED_ENVELOPE_VERSION`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | - | `{...}` |
| `isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_index | _assemble_knowledge_index | 251 | `_assemble_knowledge_index(inputs)` |
| _assemble_knowledge_index | _validate_and_join_inputs | 226 | `_validate_and_join_inputs(inputs)` |
| _validate_and_join_inputs | isinstance (src/llm_wiki_cli/services…_validate_and_join_inputs) | 568 | `isinstance(inputs, KnowledgeIndexInputs)` |
| _validate_and_join_inputs | TypeError (src/llm_wiki_cli/services…_validate_and_join_inputs) | 569 | `TypeError('inputs must be a KnowledgeIndexInputs')` |
| _validate_and_join_inputs | _validated_bundle | 570 | `_validated_bundle(inputs.envelope)` |
| _validated_bundle | isinstance (src/llm_wiki_cli/services…ndex.py:_validated_bundle) | 669 | `isinstance(envelope, EvaluatedEnvelope)` |
| _validated_bundle | KnowledgeIndexBuildError | 670 | `KnowledgeIndexBuildError('envelope', 'must be an already evaluated envelope')` |
| _validated_bundle | evaluated_envelope_to_payload | 675 | `evaluated_envelope_to_payload(envelope)` |
| evaluated_envelope_to_payload | isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload) | 1141 | `isinstance(envelope, EvaluatedEnvelope)` |
| evaluated_envelope_to_payload | TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload) | 1142 | `TypeError('envelope must be an EvaluatedEnvelope')` |
| evaluated_envelope_to_payload | KnowledgeEnvelopeError | 1144 | `KnowledgeEnvelopeError('schema_version', ...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `relationships.extend` | `_assemble_knowledge_index` | 233 |
| mutation | `joined.append` | `_validate_and_join_inputs` | 627 |
| mutation | `joined.sort` | `_validate_and_join_inputs` | 648 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_validate_and_join_inputs` | `isinstance` | 568 |
| external_call | `_validate_and_join_inputs` | `TypeError` | 569 |
| external_call | `_validated_bundle` | `isinstance` | 669 |
| external_call | `evaluated_envelope_to_payload` | `isinstance` | 1141 |
| external_call | `evaluated_envelope_to_payload` | `TypeError` | 1142 |
| step_limit | `build_knowledge_index` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_index` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_index` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
