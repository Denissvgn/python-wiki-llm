# hash_aggregate_inputs

**Entry point:** `hash_aggregate_inputs` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_aggregate_inputs
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as list
    participant p4 as _hash_structured
    participant p5 as payload.values
    participant p6 as _validate_json_tree
    participant p7 as set
    participant p8 as walk
    participant p9 as sha256_bytes
    participant p10 as hashlib.sha256(…).hexdigest
    participant p11 as hashlib.sha256
    participant p12 as canonical_json_bytes
    participant p13 as canonical_json_text(…).encode
    participant p14 as canonical_json_text
    participant p15 as json.dumps
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: list
    p0->>p2: KnowledgeEnvelopeError
    p0->>p4: _hash_structured
    p4-->>p5: payload.values
    p4->>p6: _validate_json_tree
    p6-->>p7: set
    p6-->>p8: walk
    p4->>p9: sha256_bytes
    p9-->>p10: hashlib.sha256(…).hexdigest
    p9-->>p11: hashlib.sha256
    p4->>p12: canonical_json_bytes
    p12-->>p13: canonical_json_text(…).encode
    p12->>p14: canonical_json_text
    p14-->>p15: json.dumps
    p4->>p2: KnowledgeEnvelopeError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_aggregate_inputs"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. list"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. _hash_structured"]
    s7["7. payload.values"]
    s8["8. _validate_json_tree"]
    s9["9. set"]
    s10["10. walk"]
    s11["11. sha256_bytes"]
    s12["12. hashlib.sha256(…).hexdigest"]
    s1 -. "isinstance(inputs, (...))" .-> s2
    s1 -->|"KnowledgeEnvelopeError('aggregate_inputs', 'must be an ordered iterable of contributor records')"| s3
    s1 -. "list(inputs)" .-> s4
    s1 -->|"KnowledgeEnvelopeError('aggregate_inputs', 'must be an iterable of finite canonical JSON values')"| s5
    s1 -->|"_hash_structured(AGGREGATE_INPUT_DOMAIN, {...}, 'aggregate_inputs')"| s6
    s6 -. "payload.values(data not statically known)" .-> s7
    s6 -->|"_validate_json_tree(value, field_name)"| s8
    s8 -. "set(data not statically known)" .-> s9
    s8 -. "walk(value, field_name)" .-> s10
    s6 -->|"sha256_bytes(canonical_json_bytes(...))"| s11
    s11 -. "hashlib.sha256(…).hexdigest(data not statically known)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_aggregate_inputs` | `inputs: Sequence[Any] \| Iterable[Any]` | `Mapping`, `AGGREGATE_INPUT_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `list` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_hash_structured` | `domain: str`, `payload: Mapping[str, Any]`, `field_name: str` | `KnowledgeEnvelopeError` | - | `sha256_bytes(...)` |
| `payload.values` | - | - | - | - |
| `_validate_json_tree` | `value: object`, `field_name: str` | - | - | - |
| `set` | - | - | - | - |
| `walk` | - | - | - | - |
| `sha256_bytes` | `value: bytes` | - | - | `...` |
| `hashlib.sha256(…).hexdigest` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_aggregate_inputs | isinstance | 872 | `isinstance(inputs, (...))` |
| hash_aggregate_inputs | KnowledgeEnvelopeError | 873 | `KnowledgeEnvelopeError('aggregate_inputs', 'must be an ordered iterable of contributor records')` |
| hash_aggregate_inputs | list | 878 | `list(inputs)` |
| hash_aggregate_inputs | KnowledgeEnvelopeError | 880 | `KnowledgeEnvelopeError('aggregate_inputs', 'must be an iterable of finite canonical JSON values')` |
| hash_aggregate_inputs | _hash_structured | 884 | `_hash_structured(AGGREGATE_INPUT_DOMAIN, {...}, 'aggregate_inputs')` |
| _hash_structured | payload.values | 1604 | `payload.values(data not statically known)` |
| _hash_structured | _validate_json_tree | 1605 | `_validate_json_tree(value, field_name)` |
| _validate_json_tree | set | 1626 | `set(data not statically known)` |
| _validate_json_tree | walk | 1667 | `walk(value, field_name)` |
| _hash_structured | sha256_bytes | 1606 | `sha256_bytes(canonical_json_bytes(...))` |
| sha256_bytes | hashlib.sha256(…).hexdigest | 198 | `hashlib.sha256(value).hexdigest(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_aggregate_inputs` | `isinstance` | 872 |
| unresolved_call | `_hash_structured` | `payload.values` | 1604 |
| unresolved_call | `_validate_json_tree` | `walk` | 1667 |
| unresolved_call | `sha256_bytes` | `hashlib.sha256(value).hexdigest` | 198 |
| step_limit | `hash_aggregate_inputs` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_aggregate_inputs` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
