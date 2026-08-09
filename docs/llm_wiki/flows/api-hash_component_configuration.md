# hash_component_configuration

**Entry point:** `hash_component_configuration` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_component_configuration
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as _reject_machine_local_paths
    participant p4 as set
    participant p5 as walk
    participant p6 as _hash_structured
    participant p7 as values
    participant p8 as _validate_json_tree
    participant p9 as sha256_bytes
    participant p10 as hexdigest
    participant p11 as sha256
    participant p12 as canonical_json_bytes
    participant p13 as encode
    participant p14 as canonical_json_text
    participant p15 as dumps
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0->>p3: _reject_machine_local_paths
    p3-->>p4: set
    p3-->>p5: walk
    p0->>p6: _hash_structured
    p6-->>p7: values
    p6->>p8: _validate_json_tree
    p8-->>p4: set
    p8-->>p5: walk
    p6->>p9: sha256_bytes
    p9-->>p10: hexdigest
    p9-->>p11: sha256
    p6->>p12: canonical_json_bytes
    p12-->>p13: encode
    p12->>p14: canonical_json_text
    p14-->>p15: dumps
    p6->>p2: KnowledgeEnvelopeError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_component_configuration"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. _reject_machine_local_paths"]
    s5["5. set"]
    s6["6. walk"]
    s7["7. _hash_structured"]
    s8["8. values"]
    s9["9. _validate_json_tree"]
    s10["10. set"]
    s11["11. walk"]
    s12["12. sha256_bytes"]
    s1 -. "isinstance(configuration, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('configuration', 'must be an object')"| s3
    s1 -->|"_reject_machine_local_paths(configuration, 'configuration')"| s4
    s4 -. "set(data not statically known)" .-> s5
    s4 -. "walk(value, field_name)" .-> s6
    s1 -->|"_hash_structured(COMPONENT_CONFIGURATION_DOMAIN, {...}, 'configuration')"| s7
    s7 -. "payload.values(data not statically known)" .-> s8
    s7 -->|"_validate_json_tree(value, field_name)"| s9
    s9 -. "set(data not statically known)" .-> s10
    s9 -. "walk(value, field_name)" .-> s11
    s7 -->|"sha256_bytes(canonical_json_bytes(...))"| s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s9 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_component_configuration` | `configuration: Mapping[str, Any]` | `Mapping`, `COMPONENT_CONFIGURATION_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_reject_machine_local_paths` | `value: object`, `field_name: str` | - | - | - |
| `set` | - | - | - | - |
| `walk` | - | - | - | - |
| `_hash_structured` | `domain: str`, `payload: Mapping[str, Any]`, `field_name: str` | `KnowledgeEnvelopeError` | - | `sha256_bytes(...)` |
| `values` | - | - | - | - |
| `_validate_json_tree` | `value: object`, `field_name: str` | - | - | - |
| `set` | - | - | - | - |
| `walk` | - | - | - | - |
| `sha256_bytes` | `value: bytes` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_component_configuration | isinstance | 850 | `isinstance(configuration, Mapping)` |
| hash_component_configuration | KnowledgeEnvelopeError | 851 | `KnowledgeEnvelopeError('configuration', 'must be an object')` |
| hash_component_configuration | _reject_machine_local_paths | 852 | `_reject_machine_local_paths(configuration, 'configuration')` |
| _reject_machine_local_paths | set | 1593 | `set(data not statically known)` |
| _reject_machine_local_paths | walk | 1637 | `walk(value, field_name)` |
| hash_component_configuration | _hash_structured | 853 | `_hash_structured(COMPONENT_CONFIGURATION_DOMAIN, {...}, 'configuration')` |
| _hash_structured | values | 1484 | `payload.values(data not statically known)` |
| _hash_structured | _validate_json_tree | 1485 | `_validate_json_tree(value, field_name)` |
| _validate_json_tree | set | 1506 | `set(data not statically known)` |
| _validate_json_tree | walk | 1547 | `walk(value, field_name)` |
| _hash_structured | sha256_bytes | 1486 | `sha256_bytes(canonical_json_bytes(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `hash_component_configuration` | `isinstance` | 850 |
| unresolved_call | `_reject_machine_local_paths` | `walk` | 1637 |
| unresolved_call | `_hash_structured` | `payload.values` | 1484 |
| unresolved_call | `_validate_json_tree` | `walk` | 1547 |
| step_limit | `hash_component_configuration` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_component_configuration` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
