# build_knowledge_index

**Entry point:** `build_knowledge_index` (`api`)
**Source:** [knowledge_index](../modules/knowledge_index.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_index](../modules/knowledge_index.md), and 5 more

**Complete modules touched:**

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_index
    participant p1 as _validate_and_join_inputs
    participant p2 as isinstance
    participant p3 as TypeError
    participant p4 as _validated_bundle
    participant p5 as KnowledgeIndexBuildError
    participant p6 as evaluated_envelope_to_payload
    participant p7 as KnowledgeEnvelopeError
    participant p8 as _validated_bundle_payload
    participant p9 as dict
    participant p10 as pop
    participant p11 as replace
    participant p12 as knowledge_index_to_payload
    participant p13 as _emit_extensions
    participant p14 as _bundle_to_payload
    participant p15 as _concept_to_payload
    participant p16 as _relationship_to_payload
    participant p17 as KnowledgeModelError
    participant p18 as parse_knowledge_index
    participant p19 as _knowledge_index_to_payload_unchecked
    participant p20 as KnowledgeIndex
    participant p21 as get
    participant p22 as is_valid_sha256
    p0->>p1: _validate_and_join_inputs
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1->>p4: _validated_bundle
    p4-->>p2: isinstance
    p4->>p5: KnowledgeIndexBuildError
    p4->>p6: evaluated_envelope_to_payload
    p6-->>p2: isinstance
    p6-->>p3: TypeError
    p6->>p7: KnowledgeEnvelopeError
    p6->>p8: _validated_bundle_payload
    p8-->>p9: dict
    p8-->>p10: pop
    p8-->>p11: replace
    p8-->>p11: replace
    p8->>p12: knowledge_index_to_payload
    p12-->>p2: isinstance
    p12-->>p3: TypeError
    p12->>p13: _emit_extensions
    p12->>p14: _bundle_to_payload
    p12->>p15: _concept_to_payload
    p12->>p16: _relationship_to_payload
    p12->>p17: KnowledgeModelError
    p12->>p18: parse_knowledge_index
    p12->>p19: _knowledge_index_to_payload_unchecked
    p8->>p20: KnowledgeIndex
    p8->>p7: KnowledgeEnvelopeError
    p6-->>p21: get
    p6-->>p21: get
    p6->>p22: is_valid_sha256
```

> Call sequence diagram shows 30 of 590 interactions; 560 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_knowledge_index"]
    s2["2. _validate_and_join_inputs"]
    s3["3. isinstance"]
    s4["4. TypeError"]
    s5["5. _validated_bundle"]
    s6["6. isinstance"]
    s7["7. KnowledgeIndexBuildError"]
    s8["8. evaluated_envelope_to_payload"]
    s9["9. isinstance"]
    s10["10. TypeError"]
    s11["11. KnowledgeEnvelopeError"]
    s12["12. _validated_bundle_payload"]
    s1 -->|"_validate_and_join_inputs(inputs)"| s2
    s2 -. "isinstance(inputs, KnowledgeIndexInputs)" .-> s3
    s2 -. "TypeError('inputs must be a KnowledgeIndexInputs')" .-> s4
    s2 -->|"_validated_bundle(inputs.envelope)"| s5
    s5 -. "isinstance(envelope, EvaluatedEnvelope)" .-> s6
    s5 -->|"KnowledgeIndexBuildError('envelope', 'must be an already evaluated envelope')"| s7
    s5 -->|"evaluated_envelope_to_payload(envelope)"| s8
    s8 -. "isinstance(envelope, EvaluatedEnvelope)" .-> s9
    s8 -. "TypeError('envelope must be an EvaluatedEnvelope')" .-> s10
    s8 -->|"KnowledgeEnvelopeError('schema_version', ...)"| s11
    s8 -->|"_validated_bundle_payload(envelope.bundle)"| s12
    b0["mutation relationships.extend"]
    s1 -. "mutation relationships.extend" .-> b0
    b1["mutation joined.append"]
    s2 -. "mutation joined.append" .-> b1
    b2["mutation joined.sort"]
    s2 -. "mutation joined.sort" .-> b2
    b3["mutation snapshot_extensions.pop"]
    s12 -. "mutation snapshot_extensions.pop" .-> b3
    click s1 "../modules/knowledge_index.md"
    click s2 "../modules/knowledge_index.md"
    click s5 "../modules/knowledge_index.md"
    click s7 "../modules/knowledge_index.md"
    click s8 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_index` | `inputs: KnowledgeIndexInputs` | `KNOWLEDGE_SCHEMA_VERSION`, `KnowledgeModelError` | - | `validate_knowledge_index(...)` |
| `_validate_and_join_inputs` | `inputs: KnowledgeIndexInputs` | `KnowledgeIndexInputs`, `ManifestPageSource`, `ManifestEvidenceBaseline`, `ManifestTombstone`, `ConceptObservationBasis`, `_MANIFEST_STRUCTURAL_PAGE_KINDS`, `PageKind` | - | `_BuildContext(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_validated_bundle` | `envelope: object` | `EvaluatedEnvelope`, `KnowledgeEnvelopeError` | - | `envelope.bundle` |
| `isinstance` | - | - | - | - |
| `KnowledgeIndexBuildError` | - | - | - | - |
| `evaluated_envelope_to_payload` | `envelope: EvaluatedEnvelope` | `EvaluatedEnvelope`, `EVALUATED_ENVELOPE_VERSION`, `EVALUATED_ENVELOPE_VERSION`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | - | `{...}` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_validated_bundle_payload` | `bundle: BundleRecord` | `GOVERNANCE_HASH_EXTENSION_KEY`, `KNOWLEDGE_SCHEMA_VERSION`, `KnowledgeModelError` | - | `payload[...]` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_index | _validate_and_join_inputs | 218 | `_validate_and_join_inputs(inputs)` |
| _validate_and_join_inputs | isinstance | 286 | `isinstance(inputs, KnowledgeIndexInputs)` |
| _validate_and_join_inputs | TypeError | 287 | `TypeError('inputs must be a KnowledgeIndexInputs')` |
| _validate_and_join_inputs | _validated_bundle | 288 | `_validated_bundle(inputs.envelope)` |
| _validated_bundle | isinstance | 387 | `isinstance(envelope, EvaluatedEnvelope)` |
| _validated_bundle | KnowledgeIndexBuildError | 388 | `KnowledgeIndexBuildError('envelope', 'must be an already evaluated envelope')` |
| _validated_bundle | evaluated_envelope_to_payload | 393 | `evaluated_envelope_to_payload(envelope)` |
| evaluated_envelope_to_payload | isinstance | 1131 | `isinstance(envelope, EvaluatedEnvelope)` |
| evaluated_envelope_to_payload | TypeError | 1132 | `TypeError('envelope must be an EvaluatedEnvelope')` |
| evaluated_envelope_to_payload | KnowledgeEnvelopeError | 1134 | `KnowledgeEnvelopeError('schema_version', ...)` |
| evaluated_envelope_to_payload | _validated_bundle_payload | 1138 | `_validated_bundle_payload(envelope.bundle)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `relationships.extend` | `build_knowledge_index` | 225 |
| mutation | `joined.append` | `_validate_and_join_inputs` | 345 |
| mutation | `joined.sort` | `_validate_and_join_inputs` | 366 |
| mutation | `snapshot_extensions.pop` | `_validated_bundle_payload` | 1823 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_validate_and_join_inputs` | `isinstance` | 286 |
| unresolved_call | `_validate_and_join_inputs` | `TypeError` | 287 |
| unresolved_call | `_validated_bundle` | `isinstance` | 387 |
| unresolved_call | `evaluated_envelope_to_payload` | `isinstance` | 1131 |
| unresolved_call | `evaluated_envelope_to_payload` | `TypeError` | 1132 |
| step_limit | `build_knowledge_index` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_index` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_index` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
