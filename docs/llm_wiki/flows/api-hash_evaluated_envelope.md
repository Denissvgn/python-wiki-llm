# hash_evaluated_envelope

**Entry point:** `hash_evaluated_envelope` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 1 more

**Complete modules touched:**

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_evaluated_envelope
    participant p1 as sha256_bytes
    participant p2 as hexdigest
    participant p3 as sha256
    participant p4 as encode
    participant p5 as serialize_evaluated_envelope
    participant p6 as formatted_json_text
    participant p7 as dumps
    participant p8 as evaluated_envelope_to_payload
    participant p9 as isinstance
    participant p10 as TypeError
    participant p11 as KnowledgeEnvelopeError
    participant p12 as _validated_bundle_payload
    participant p13 as dict
    participant p14 as pop
    participant p15 as replace
    participant p16 as knowledge_index_to_payload
    participant p17 as _emit_extensions
    participant p18 as _parse_extensions
    participant p19 as _bundle_to_payload
    participant p20 as _wire_enum
    participant p21 as _component_to_payload
    p0->>p1: sha256_bytes
    p1-->>p2: hexdigest
    p1-->>p3: sha256
    p0-->>p4: encode
    p0->>p5: serialize_evaluated_envelope
    p5->>p6: formatted_json_text
    p6-->>p7: dumps
    p5->>p8: evaluated_envelope_to_payload
    p8-->>p9: isinstance
    p8-->>p10: TypeError
    p8->>p11: KnowledgeEnvelopeError
    p8->>p12: _validated_bundle_payload
    p12-->>p13: dict
    p12-->>p14: pop
    p12-->>p15: replace
    p12-->>p15: replace
    p12->>p16: knowledge_index_to_payload
    p16-->>p9: isinstance
    p16-->>p10: TypeError
    p16->>p17: _emit_extensions
    p17->>p18: _parse_extensions
    p16->>p19: _bundle_to_payload
    p19->>p17: _emit_extensions
    p19->>p20: _wire_enum
    p19->>p17: _emit_extensions
    p19->>p17: _emit_extensions
    p19->>p21: _component_to_payload
    p19->>p21: _component_to_payload
    p19->>p21: _component_to_payload
    p19->>p17: _emit_extensions
```

> Call sequence diagram shows 30 of 96 interactions; 66 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_evaluated_envelope"]
    s2["2. sha256_bytes"]
    s3["3. hexdigest"]
    s4["4. sha256"]
    s5["5. encode"]
    s6["6. serialize_evaluated_envelope"]
    s7["7. formatted_json_text"]
    s8["8. dumps"]
    s9["9. evaluated_envelope_to_payload"]
    s10["10. isinstance"]
    s11["11. TypeError"]
    s12["12. KnowledgeEnvelopeError"]
    s1 -->|"sha256_bytes(...)"| s2
    s2 -. "hashlib.sha256(value).hexdigest(data not statically known)" .-> s3
    s2 -. "hashlib.sha256(value)" .-> s4
    s1 -. "serialize_evaluated_envelope(envelope).encode('utf-8')" .-> s5
    s1 -->|"serialize_evaluated_envelope(envelope)"| s6
    s6 -->|"formatted_json_text(evaluated_envelope_to_payload(...))"| s7
    s7 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s8
    s6 -->|"evaluated_envelope_to_payload(envelope)"| s9
    s9 -. "isinstance(envelope, EvaluatedEnvelope)" .-> s10
    s9 -. "TypeError('envelope must be an EvaluatedEnvelope')" .-> s11
    s9 -->|"KnowledgeEnvelopeError('schema_version', ...)"| s12
    click s1 "../modules/knowledge_envelope.md"
    click s2 "../modules/knowledge_evidence.md"
    click s6 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_evidence.md"
    click s9 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_evaluated_envelope` | `envelope: EvaluatedEnvelope` | - | - | `sha256_bytes(...)` |
| `sha256_bytes` | `value: bytes` | - | - | `...` |
| `hexdigest` | - | - | - | - |
| `sha256` | - | - | - | - |
| `encode` | - | - | - | - |
| `serialize_evaluated_envelope` | `envelope: EvaluatedEnvelope` | `KnowledgeEnvelopeError` | - | `formatted_json_text(...)` |
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `dumps` | - | - | - | - |
| `evaluated_envelope_to_payload` | `envelope: EvaluatedEnvelope` | `EvaluatedEnvelope`, `EVALUATED_ENVELOPE_VERSION`, `EVALUATED_ENVELOPE_VERSION`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | - | `{...}` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_evaluated_envelope | sha256_bytes | 1170 | `sha256_bytes(...)` |
| sha256_bytes | hexdigest | 197 | `hashlib.sha256(value).hexdigest(data not statically known)` |
| sha256_bytes | sha256 | 197 | `hashlib.sha256(value)` |
| hash_evaluated_envelope | encode | 1170 | `serialize_evaluated_envelope(envelope).encode('utf-8')` |
| hash_evaluated_envelope | serialize_evaluated_envelope | 1170 | `serialize_evaluated_envelope(envelope)` |
| serialize_evaluated_envelope | formatted_json_text | 1157 | `formatted_json_text(evaluated_envelope_to_payload(...))` |
| formatted_json_text | dumps | 177 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
| serialize_evaluated_envelope | evaluated_envelope_to_payload | 1157 | `evaluated_envelope_to_payload(envelope)` |
| evaluated_envelope_to_payload | isinstance | 1131 | `isinstance(envelope, EvaluatedEnvelope)` |
| evaluated_envelope_to_payload | TypeError | 1132 | `TypeError('envelope must be an EvaluatedEnvelope')` |
| evaluated_envelope_to_payload | KnowledgeEnvelopeError | 1134 | `KnowledgeEnvelopeError('schema_version', ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `sha256_bytes` | `hashlib.sha256(value).hexdigest` | 197 |
| external_call | `sha256_bytes` | `hashlib.sha256` | 197 |
| unresolved_call | `hash_evaluated_envelope` | `serialize_evaluated_envelope(envelope).encode` | 1170 |
| external_call | `formatted_json_text` | `json.dumps` | 177 |
| unresolved_call | `evaluated_envelope_to_payload` | `isinstance` | 1131 |
| unresolved_call | `evaluated_envelope_to_payload` | `TypeError` | 1132 |
| step_limit | `hash_evaluated_envelope` | `first 12 steps` | 0 |
| truncated_flow | `hash_evaluated_envelope` | `depth limit` | 0 |

## Behavior

This flow starts at `hash_evaluated_envelope` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
