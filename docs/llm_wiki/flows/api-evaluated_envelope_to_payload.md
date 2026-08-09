# evaluated_envelope_to_payload

**Entry point:** `evaluated_envelope_to_payload` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 6 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as evaluated_envelope_to_payload
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as KnowledgeEnvelopeError
    participant p4 as _validated_bundle_payload
    participant p5 as dict
    participant p6 as pop
    participant p7 as replace
    participant p8 as knowledge_index_to_payload
    participant p9 as _emit_extensions
    participant p10 as _parse_extensions
    participant p11 as _object
    participant p12 as require_mapping
    participant p13 as KnowledgeModelError
    participant p14 as sorted
    participant p15 as fullmatch
    participant p16 as _child
    participant p17 as _normalize_json_value
    participant p18 as _normalize_json_value_inner
    participant p19 as set
    participant p20 as _bundle_to_payload
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: KnowledgeEnvelopeError
    p0->>p4: _validated_bundle_payload
    p4-->>p5: dict
    p4-->>p6: pop
    p4-->>p7: replace
    p4-->>p7: replace
    p4->>p8: knowledge_index_to_payload
    p8-->>p1: isinstance
    p8-->>p2: TypeError
    p8->>p9: _emit_extensions
    p9->>p10: _parse_extensions
    p10->>p11: _object
    p11-->>p5: dict
    p11->>p12: require_mapping
    p11->>p13: KnowledgeModelError
    p11->>p13: KnowledgeModelError
    p11->>p13: KnowledgeModelError
    p10-->>p14: sorted
    p10-->>p15: fullmatch
    p10->>p13: KnowledgeModelError
    p10->>p16: _child
    p10->>p17: _normalize_json_value
    p17->>p18: _normalize_json_value_inner
    p17-->>p19: set
    p10->>p16: _child
    p10->>p13: KnowledgeModelError
    p10->>p16: _child
    p8->>p20: _bundle_to_payload
```

> Call sequence diagram shows 30 of 685 interactions; 655 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluated_envelope_to_payload"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. KnowledgeEnvelopeError"]
    s5["5. _validated_bundle_payload"]
    s6["6. dict"]
    s7["7. pop"]
    s8["8. replace"]
    s9["9. replace"]
    s10["10. knowledge_index_to_payload"]
    s11["11. isinstance"]
    s12["12. TypeError"]
    s1 -. "isinstance(envelope, EvaluatedEnvelope)" .-> s2
    s1 -. "TypeError('envelope must be an EvaluatedEnvelope')" .-> s3
    s1 -->|"KnowledgeEnvelopeError('schema_version', ...)"| s4
    s1 -->|"_validated_bundle_payload(envelope.bundle)"| s5
    s5 -. "dict(bundle.snapshot.extensions)" .-> s6
    s5 -. "snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)" .-> s7
    s5 -. "replace(bundle, snapshot=replace(...))" .-> s8
    s5 -. "replace(bundle.snapshot, extensions=snapshot_extensions)" .-> s9
    s5 -->|"knowledge_index_to_payload(KnowledgeIndex(...))"| s10
    s10 -. "isinstance(model, KnowledgeIndex)" .-> s11
    s10 -. "TypeError('model must be a KnowledgeIndex')" .-> s12
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
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_validated_bundle_payload` | `bundle: BundleRecord` | `GOVERNANCE_HASH_EXTENSION_KEY`, `KNOWLEDGE_SCHEMA_VERSION`, `KnowledgeModelError` | - | `payload[...]` |
| `dict` | - | - | - | - |
| `pop` | - | - | - | - |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `knowledge_index_to_payload` | `model: KnowledgeIndex` | `KnowledgeIndex`, `KnowledgeModelError` | - | `_knowledge_index_to_payload_unchecked(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluated_envelope_to_payload | isinstance | 1138 | `isinstance(envelope, EvaluatedEnvelope)` |
| evaluated_envelope_to_payload | TypeError | 1139 | `TypeError('envelope must be an EvaluatedEnvelope')` |
| evaluated_envelope_to_payload | KnowledgeEnvelopeError | 1141 | `KnowledgeEnvelopeError('schema_version', ...)` |
| evaluated_envelope_to_payload | _validated_bundle_payload | 1145 | `_validated_bundle_payload(envelope.bundle)` |
| _validated_bundle_payload | dict | 1927 | `dict(bundle.snapshot.extensions)` |
| _validated_bundle_payload | pop | 1928 | `snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)` |
| _validated_bundle_payload | replace | 1929 | `replace(bundle, snapshot=replace(...))` |
| _validated_bundle_payload | replace | 1931 | `replace(bundle.snapshot, extensions=snapshot_extensions)` |
| _validated_bundle_payload | knowledge_index_to_payload | 1937 | `knowledge_index_to_payload(KnowledgeIndex(...))` |
| knowledge_index_to_payload | isinstance | 641 | `isinstance(model, KnowledgeIndex)` |
| knowledge_index_to_payload | TypeError | 642 | `TypeError('model must be a KnowledgeIndex')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `snapshot_extensions.pop` | `_validated_bundle_payload` | 1928 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `evaluated_envelope_to_payload` | `isinstance` | 1138 |
| unresolved_call | `evaluated_envelope_to_payload` | `TypeError` | 1139 |
| external_call | `_validated_bundle_payload` | `replace` | 1929 |
| external_call | `_validated_bundle_payload` | `replace` | 1931 |
| unresolved_call | `knowledge_index_to_payload` | `isinstance` | 641 |
| unresolved_call | `knowledge_index_to_payload` | `TypeError` | 642 |
| step_limit | `evaluated_envelope_to_payload` | `first 12 steps` | 0 |
| truncated_flow | `evaluated_envelope_to_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluated_envelope_to_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
