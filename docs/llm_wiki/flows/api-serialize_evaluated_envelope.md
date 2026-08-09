# serialize_evaluated_envelope

**Entry point:** `serialize_evaluated_envelope` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_evaluated_envelope
    participant p1 as formatted_json_text
    participant p2 as dumps
    participant p3 as evaluated_envelope_to_payload
    participant p4 as isinstance
    participant p5 as TypeError
    participant p6 as KnowledgeEnvelopeError
    participant p7 as _validated_bundle_payload
    participant p8 as dict
    participant p9 as pop
    participant p10 as replace
    participant p11 as knowledge_index_to_payload
    participant p12 as _emit_extensions
    participant p13 as _parse_extensions
    participant p14 as _object
    participant p15 as sorted
    participant p16 as fullmatch
    participant p17 as KnowledgeModelError
    participant p18 as _child
    participant p19 as _normalize_json_value
    participant p20 as _bundle_to_payload
    participant p21 as _wire_enum
    p0->>p1: formatted_json_text
    p1-->>p2: dumps
    p0->>p3: evaluated_envelope_to_payload
    p3-->>p4: isinstance
    p3-->>p5: TypeError
    p3->>p6: KnowledgeEnvelopeError
    p3->>p7: _validated_bundle_payload
    p7-->>p8: dict
    p7-->>p9: pop
    p7-->>p10: replace
    p7-->>p10: replace
    p7->>p11: knowledge_index_to_payload
    p11-->>p4: isinstance
    p11-->>p5: TypeError
    p11->>p12: _emit_extensions
    p12->>p13: _parse_extensions
    p13->>p14: _object
    p13-->>p15: sorted
    p13-->>p16: fullmatch
    p13->>p17: KnowledgeModelError
    p13->>p18: _child
    p13->>p19: _normalize_json_value
    p13->>p18: _child
    p13->>p17: KnowledgeModelError
    p13->>p18: _child
    p11->>p20: _bundle_to_payload
    p20->>p12: _emit_extensions
    p20->>p21: _wire_enum
    p21-->>p4: isinstance
    p20->>p12: _emit_extensions
```

> Call sequence diagram shows 30 of 269 interactions; 239 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_evaluated_envelope"]
    s2["2. formatted_json_text"]
    s3["3. dumps"]
    s4["4. evaluated_envelope_to_payload"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. KnowledgeEnvelopeError"]
    s8["8. _validated_bundle_payload"]
    s9["9. dict"]
    s10["10. pop"]
    s11["11. replace"]
    s12["12. replace"]
    s1 -->|"formatted_json_text(evaluated_envelope_to_payload(...))"| s2
    s2 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s3
    s1 -->|"evaluated_envelope_to_payload(envelope)"| s4
    s4 -. "isinstance(envelope, EvaluatedEnvelope)" .-> s5
    s4 -. "TypeError('envelope must be an EvaluatedEnvelope')" .-> s6
    s4 -->|"KnowledgeEnvelopeError('schema_version', ...)"| s7
    s4 -->|"_validated_bundle_payload(envelope.bundle)"| s8
    s8 -. "dict(bundle.snapshot.extensions)" .-> s9
    s8 -. "snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)" .-> s10
    s8 -. "replace(bundle, snapshot=replace(...))" .-> s11
    s8 -. "replace(bundle.snapshot, extensions=snapshot_extensions)" .-> s12
    b0["mutation snapshot_extensions.pop"]
    s8 -. "mutation snapshot_extensions.pop" .-> b0
    click s1 "../modules/knowledge_envelope.md"
    click s2 "../modules/knowledge_evidence.md"
    click s4 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `serialize_evaluated_envelope` | `envelope: EvaluatedEnvelope` | `KnowledgeEnvelopeError` | - | `formatted_json_text(...)` |
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `dumps` | - | - | - | - |
| `evaluated_envelope_to_payload` | `envelope: EvaluatedEnvelope` | `EvaluatedEnvelope`, `EVALUATED_ENVELOPE_VERSION`, `EVALUATED_ENVELOPE_VERSION`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | - | `{...}` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_validated_bundle_payload` | `bundle: BundleRecord` | `GOVERNANCE_HASH_EXTENSION_KEY`, `KNOWLEDGE_SCHEMA_VERSION`, `KnowledgeModelError` | - | `payload[...]` |
| `dict` | - | - | - | - |
| `pop` | - | - | - | - |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| serialize_evaluated_envelope | formatted_json_text | 1164 | `formatted_json_text(evaluated_envelope_to_payload(...))` |
| formatted_json_text | dumps | 177 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
| serialize_evaluated_envelope | evaluated_envelope_to_payload | 1164 | `evaluated_envelope_to_payload(envelope)` |
| evaluated_envelope_to_payload | isinstance | 1138 | `isinstance(envelope, EvaluatedEnvelope)` |
| evaluated_envelope_to_payload | TypeError | 1139 | `TypeError('envelope must be an EvaluatedEnvelope')` |
| evaluated_envelope_to_payload | KnowledgeEnvelopeError | 1141 | `KnowledgeEnvelopeError('schema_version', ...)` |
| evaluated_envelope_to_payload | _validated_bundle_payload | 1145 | `_validated_bundle_payload(envelope.bundle)` |
| _validated_bundle_payload | dict | 1927 | `dict(bundle.snapshot.extensions)` |
| _validated_bundle_payload | pop | 1928 | `snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)` |
| _validated_bundle_payload | replace | 1929 | `replace(bundle, snapshot=replace(...))` |
| _validated_bundle_payload | replace | 1931 | `replace(bundle.snapshot, extensions=snapshot_extensions)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `snapshot_extensions.pop` | `_validated_bundle_payload` | 1928 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `formatted_json_text` | `json.dumps` | 177 |
| unresolved_call | `evaluated_envelope_to_payload` | `isinstance` | 1138 |
| unresolved_call | `evaluated_envelope_to_payload` | `TypeError` | 1139 |
| external_call | `_validated_bundle_payload` | `replace` | 1929 |
| external_call | `_validated_bundle_payload` | `replace` | 1931 |
| step_limit | `serialize_evaluated_envelope` | `first 12 steps` | 0 |
| truncated_flow | `serialize_evaluated_envelope` | `depth limit` | 0 |

## Behavior

This flow starts at `serialize_evaluated_envelope` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
