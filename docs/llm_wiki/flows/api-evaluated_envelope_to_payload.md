# evaluated_envelope_to_payload

**Entry point:** `evaluated_envelope_to_payload` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [implementation_evidence](../modules/implementation_evidence.md), [knowledge_envelope](../modules/knowledge_envelope.md), and 13 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as evaluated_envelope_to_payload
    participant p1 as _validated_bundle_payload
    participant p2 as KnowledgeEnvelopeError
    participant p3 as is_valid_sha256
    participant p4 as knowledge_index_to_payload
    participant p5 as _emit_extensions
    participant p6 as _bundle_to_payload
    participant p7 as _concept_to_payload
    participant p8 as _relationship_to_payload
    participant p9 as parse_knowledge_index
    participant p10 as _knowledge_index_to_payload_unchecked
    participant p11 as _record
    participant p12 as _parse_extensions
    participant p13 as _string
    participant p14 as _basis_to_payload
    participant p15 as _relationship_target_to_payload
    participant p16 as _parse_bundle
    participant p17 as _component_to_payload
    participant p18 as _relationship_evidence_to_payload
    participant p19 as _array (src/llm_wiki_cli/services/knowledge_model.py)
    participant p20 as _actor_to_payload
    participant p21 as _parse_concept
    participant p22 as _parse_relationship
    participant p23 as _document_to_payload
    participant p24 as _validated_reserved_extensions
    participant p25 as _validate_index_references
    participant p26 as validate_implementation_collection
    participant p27 as validate_maintenance_projection
    participant p28 as validate_governance_projection
    participant p29 as isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)
    participant p30 as bundle_payload[…].get(…).get
    p0->>p1: _validated_bundle_payload
    p0->>p2: KnowledgeEnvelopeError
    p0->>p3: is_valid_sha256
    p1->>p4: knowledge_index_to_payload
    p4->>p5: _emit_extensions
    p4->>p6: _bundle_to_payload
    p4->>p7: _concept_to_payload
    p4->>p8: _relationship_to_payload
    p4->>p9: parse_knowledge_index
    p4->>p10: _knowledge_index_to_payload_unchecked
    p9->>p11: _record
    p5->>p12: _parse_extensions
    p9->>p13: _string
    p7->>p14: _basis_to_payload
    p8->>p15: _relationship_target_to_payload
    p9->>p16: _parse_bundle
    p6->>p17: _component_to_payload
    p8->>p18: _relationship_evidence_to_payload
    p9->>p19: _array (src/llm_wiki_cli/services/knowledge_model.py)
    p7->>p20: _actor_to_payload
    p9->>p21: _parse_concept
    p9->>p22: _parse_relationship
    p7->>p23: _document_to_payload
    p9->>p24: _validated_reserved_extensions
    p9->>p25: _validate_index_references
    p9->>p26: validate_implementation_collection
    p9->>p27: validate_maintenance_projection
    p9->>p28: validate_governance_projection
    p0-->>p29: isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)(envelope, EvaluatedEnvelope)
    p0-->>p30: bundle_payload[…].get(…).get(INVENTORY_HASH_EXTENSION)
```

> Call sequence diagram shows 30 of 812 interactions; 782 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 192 (191 omitted); unresolved 1 of 117 (116 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:evaluated_envelope_to_payload` | 1 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_bundle_payload` | 5 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_bundle_payload` | 5 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:knowledge_index_to_payload` | 10 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_model.py:_emit_extensions` | 13 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_parse_extensions` | 15 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 7 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 16 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 16 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 164 groups; 156 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 504; effect analysis evaluated: 330, partial: 8, unavailable: 166. Counts include steps omitted from the displayed trace.

Collector observations for 338 source steps with known totals: observed: 1567, emitted: 1516, omitted: 51. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `evaluated_envelope_to_payload` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_validated_bundle_payload` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `dict (src/llm_wiki_cli/services…_validated_bundle_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `snapshot_extensions.pop` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `replace (src/llm_wiki_cli/services…_validated_bundle_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `replace (src/llm_wiki_cli/services…_validated_bundle_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `knowledge_index_to_payload` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. evaluated_envelope_to_payload"]
    s2["2. isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)"]
    s3["3. TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)"]
    s4["4. KnowledgeEnvelopeError"]
    s5["5. _validated_bundle_payload"]
    s6["6. dict (src/llm_wiki_cli/services…_validated_bundle_payload)"]
    s7["7. snapshot_extensions.pop"]
    s8["8. replace (src/llm_wiki_cli/services…_validated_bundle_payload)"]
    s9["9. replace (src/llm_wiki_cli/services…_validated_bundle_payload)"]
    s10["10. knowledge_index_to_payload"]
    s11["11. isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload)"]
    s12["12. TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)(envelope, EvaluatedEnvelope)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)('envelope must be an EvaluatedEnvelope')" .-> s3
    s1 -->|"KnowledgeEnvelopeError('schema_version', ...)"| s4
    s1 -->|"_validated_bundle_payload(envelope.bundle)"| s5
    s5 -. "dict (src/llm_wiki_cli/services…_validated_bundle_payload)(bundle.snapshot.extensions)" .-> s6
    s5 -. "snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)" .-> s7
    s5 -. "replace (src/llm_wiki_cli/services…_validated_bundle_payload)(bundle, snapshot=replace(...))" .-> s8
    s5 -. "replace (src/llm_wiki_cli/services…_validated_bundle_payload)(bundle.snapshot, extensions=snapshot_extensions)" .-> s9
    s5 -->|"knowledge_index_to_payload(KnowledgeIndex(...))"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload)(model, KnowledgeIndex)" .-> s11
    s10 -. "TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload)('model must be a KnowledgeIndex')" .-> s12
    b0["mutation snapshot_extensions.pop"]
    s5 -. "mutation snapshot_extensions.pop" .-> b0
    click s1 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_model.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `evaluated_envelope_to_payload` | `envelope: EvaluatedEnvelope` | `EvaluatedEnvelope`, `EVALUATED_ENVELOPE_VERSION`, `EVALUATED_ENVELOPE_VERSION`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | - | `{...}` |
| `isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_validated_bundle_payload` | `bundle: BundleRecord` | `GOVERNANCE_HASH_EXTENSION_KEY`, `KNOWLEDGE_SCHEMA_VERSION`, `KnowledgeModelError` | - | `payload[...]` |
| `dict (src/llm_wiki_cli/services…_validated_bundle_payload)` | - | - | - | - |
| `snapshot_extensions.pop` | - | - | - | - |
| `replace (src/llm_wiki_cli/services…_validated_bundle_payload)` | - | - | - | - |
| `replace (src/llm_wiki_cli/services…_validated_bundle_payload)` | - | - | - | - |
| `knowledge_index_to_payload` | `model: KnowledgeIndex` | `KnowledgeIndex`, `KnowledgeModelError` | - | `_knowledge_index_to_payload_unchecked(...)` |
| `isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluated_envelope_to_payload | isinstance (src/llm_wiki_cli/services…uated_envelope_to_payload) | 1141 | `isinstance(envelope, EvaluatedEnvelope)` |
| evaluated_envelope_to_payload | TypeError (src/llm_wiki_cli/services…uated_envelope_to_payload) | 1142 | `TypeError('envelope must be an EvaluatedEnvelope')` |
| evaluated_envelope_to_payload | KnowledgeEnvelopeError | 1144 | `KnowledgeEnvelopeError('schema_version', ...)` |
| evaluated_envelope_to_payload | _validated_bundle_payload | 1148 | `_validated_bundle_payload(envelope.bundle)` |
| _validated_bundle_payload | dict (src/llm_wiki_cli/services…_validated_bundle_payload) | 1946 | `dict(bundle.snapshot.extensions)` |
| _validated_bundle_payload | snapshot_extensions.pop | 1947 | `snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)` |
| _validated_bundle_payload | replace (src/llm_wiki_cli/services…_validated_bundle_payload) | 1948 | `replace(bundle, snapshot=replace(...))` |
| _validated_bundle_payload | replace (src/llm_wiki_cli/services…_validated_bundle_payload) | 1950 | `replace(bundle.snapshot, extensions=snapshot_extensions)` |
| _validated_bundle_payload | knowledge_index_to_payload | 1956 | `knowledge_index_to_payload(KnowledgeIndex(...))` |
| knowledge_index_to_payload | isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload) | 663 | `isinstance(model, KnowledgeIndex)` |
| knowledge_index_to_payload | TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload) | 664 | `TypeError('model must be a KnowledgeIndex')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `snapshot_extensions.pop` | `_validated_bundle_payload` | 1947 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `evaluated_envelope_to_payload` | `isinstance` | 1141 |
| external_call | `evaluated_envelope_to_payload` | `TypeError` | 1142 |
| external_call | `_validated_bundle_payload` | `replace` | 1948 |
| external_call | `_validated_bundle_payload` | `replace` | 1950 |
| external_call | `knowledge_index_to_payload` | `isinstance` | 663 |
| external_call | `knowledge_index_to_payload` | `TypeError` | 664 |
| step_limit | `evaluated_envelope_to_payload` | `first 12 steps` | 0 |
| truncated_flow | `evaluated_envelope_to_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluated_envelope_to_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
