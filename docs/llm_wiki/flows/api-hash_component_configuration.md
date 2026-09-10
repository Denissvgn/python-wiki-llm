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
    participant p4 as set (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p5 as walk (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p6 as _hash_structured
    participant p7 as payload.values
    participant p8 as _validate_json_tree
    participant p9 as set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    participant p10 as walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    participant p11 as sha256_bytes
    participant p12 as hashlib.sha256(…).hexdigest
    participant p13 as hashlib.sha256
    participant p14 as canonical_json_bytes
    participant p15 as canonical_json_text(…).encode
    participant p16 as canonical_json_text
    participant p17 as json.dumps
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0->>p3: _reject_machine_local_paths
    p3-->>p4: set (src/llm_wiki_cli/services…reject_machine_local_paths)
    p3-->>p5: walk (src/llm_wiki_cli/services…reject_machine_local_paths)
    p0->>p6: _hash_structured
    p6-->>p7: payload.values
    p6->>p8: _validate_json_tree
    p8-->>p9: set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    p8-->>p10: walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    p6->>p11: sha256_bytes
    p11-->>p12: hashlib.sha256(…).hexdigest
    p11-->>p13: hashlib.sha256
    p6->>p14: canonical_json_bytes
    p14-->>p15: canonical_json_text(…).encode
    p14->>p16: canonical_json_text
    p16-->>p17: json.dumps
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
    s5["5. set (src/llm_wiki_cli/services…reject_machine_local_paths)"]
    s6["6. walk (src/llm_wiki_cli/services…reject_machine_local_paths)"]
    s7["7. _hash_structured"]
    s8["8. payload.values"]
    s9["9. _validate_json_tree"]
    s10["10. set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)"]
    s11["11. walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)"]
    s12["12. sha256_bytes"]
    s1 -. "isinstance(configuration, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('configuration', 'must be an object')"| s3
    s1 -->|"_reject_machine_local_paths(configuration, 'configuration')"| s4
    s4 -. "set (src/llm_wiki_cli/services…reject_machine_local_paths)(data not statically known)" .-> s5
    s4 -. "walk (src/llm_wiki_cli/services…reject_machine_local_paths)(value, field_name)" .-> s6
    s1 -->|"_hash_structured(COMPONENT_CONFIGURATION_DOMAIN, {...}, 'configuration')"| s7
    s7 -. "payload.values(data not statically known)" .-> s8
    s7 -->|"_validate_json_tree(value, field_name)"| s9
    s9 -. "set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)(data not statically known)" .-> s10
    s9 -. "walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)(value, field_name)" .-> s11
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
| `set (src/llm_wiki_cli/services…reject_machine_local_paths)` | - | - | - | - |
| `walk (src/llm_wiki_cli/services…reject_machine_local_paths)` | - | - | - | - |
| `_hash_structured` | `domain: str`, `payload: Mapping[str, Any]`, `field_name: str` | `KnowledgeEnvelopeError` | - | `sha256_bytes(...)` |
| `payload.values` | - | - | - | - |
| `_validate_json_tree` | `value: object`, `field_name: str` | - | - | - |
| `set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)` | - | - | - | - |
| `walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)` | - | - | - | - |
| `sha256_bytes` | `value: bytes` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_component_configuration | isinstance | 859 | `isinstance(configuration, Mapping)` |
| hash_component_configuration | KnowledgeEnvelopeError | 860 | `KnowledgeEnvelopeError('configuration', 'must be an object')` |
| hash_component_configuration | _reject_machine_local_paths | 861 | `_reject_machine_local_paths(configuration, 'configuration')` |
| _reject_machine_local_paths | set (src/llm_wiki_cli/services…reject_machine_local_paths) | 1713 | `set(data not statically known)` |
| _reject_machine_local_paths | walk (src/llm_wiki_cli/services…reject_machine_local_paths) | 1757 | `walk(value, field_name)` |
| hash_component_configuration | _hash_structured | 862 | `_hash_structured(COMPONENT_CONFIGURATION_DOMAIN, {...}, 'configuration')` |
| _hash_structured | payload.values | 1604 | `payload.values(data not statically known)` |
| _hash_structured | _validate_json_tree | 1605 | `_validate_json_tree(value, field_name)` |
| _validate_json_tree | set (src/llm_wiki_cli/services…ope.py:_validate_json_tree) | 1626 | `set(data not statically known)` |
| _validate_json_tree | walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree) | 1667 | `walk(value, field_name)` |
| _hash_structured | sha256_bytes | 1606 | `sha256_bytes(canonical_json_bytes(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_component_configuration` | `isinstance` | 859 |
| unresolved_call | `_reject_machine_local_paths` | `walk` | 1757 |
| unresolved_call | `_hash_structured` | `payload.values` | 1604 |
| unresolved_call | `_validate_json_tree` | `walk` | 1667 |
| step_limit | `hash_component_configuration` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_component_configuration` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
