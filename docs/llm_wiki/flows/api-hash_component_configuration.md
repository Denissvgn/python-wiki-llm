# hash_component_configuration

**Entry point:** `hash_component_configuration` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [knowledge_envelope](../modules/knowledge_envelope.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_component_configuration
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as _reject_machine_local_paths
    participant p4 as _hash_structured
    participant p5 as set (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p6 as payload.values
    participant p7 as walk (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p8 as _validate_json_tree
    participant p9 as sha256_digest
    participant p10 as compact_bytes
    participant p11 as set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    participant p12 as hashlib.sha256(…).hexdigest
    participant p13 as compact_text(…).encode
    participant p14 as walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    participant p15 as hashlib.sha256
    participant p16 as compact_text
    participant p17 as json.dumps
    p0-->>p1: isinstance(configuration, Mapping)
    p0->>p2: KnowledgeEnvelopeError
    p0->>p3: _reject_machine_local_paths
    p0->>p4: _hash_structured
    p3-->>p5: set (src/llm_wiki_cli/services…reject_machine_local_paths)
    p4-->>p6: payload.values
    p3-->>p7: walk (src/llm_wiki_cli/services…reject_machine_local_paths)(value, field_name)
    p4->>p8: _validate_json_tree
    p4->>p9: sha256_digest
    p4->>p10: compact_bytes
    p4->>p2: KnowledgeEnvelopeError
    p8-->>p11: set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    p9-->>p12: hashlib.sha256(…).hexdigest
    p10-->>p13: compact_text(…).encode('utf-8')
    p8-->>p14: walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)(value, field_name)
    p9-->>p15: hashlib.sha256(data)
    p10->>p16: compact_text
    p16-->>p17: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(...), allow_nan=allow_nan)
```

> Call sequence diagram shows 18 of 18 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 5 of 5 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 9; effect analysis evaluated: 7, partial: 0, unavailable: 2. Counts include steps omitted from the displayed trace.

Collector observations for 7 source steps with known totals: observed: 21, emitted: 21, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `hash_component_configuration` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_reject_machine_local_paths` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `set (src/llm_wiki_cli/services…reject_machine_local_paths)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `walk (src/llm_wiki_cli/services…reject_machine_local_paths)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_hash_structured` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `payload.values` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validate_json_tree` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `sha256_digest` | `available` | `evaluated` | `available` | `2` | `2` | `0` |

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
    s12["12. sha256_digest"]
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
    s7 -->|"sha256_digest(canonical_json_bytes(...))"| s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s9 "../modules/knowledge_envelope.md"
    click s12 "../modules/canonical_json.md"
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
| `sha256_digest` | `data: bytes` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_component_configuration | isinstance | 860 | `isinstance(configuration, Mapping)` |
| hash_component_configuration | KnowledgeEnvelopeError | 861 | `KnowledgeEnvelopeError('configuration', 'must be an object')` |
| hash_component_configuration | _reject_machine_local_paths | 862 | `_reject_machine_local_paths(configuration, 'configuration')` |
| _reject_machine_local_paths | set (src/llm_wiki_cli/services…reject_machine_local_paths) | 1718 | `set(data not statically known)` |
| _reject_machine_local_paths | walk (src/llm_wiki_cli/services…reject_machine_local_paths) | 1762 | `walk(value, field_name)` |
| hash_component_configuration | _hash_structured | 863 | `_hash_structured(COMPONENT_CONFIGURATION_DOMAIN, {...}, 'configuration')` |
| _hash_structured | payload.values | 1609 | `payload.values(data not statically known)` |
| _hash_structured | _validate_json_tree | 1610 | `_validate_json_tree(value, field_name)` |
| _validate_json_tree | set (src/llm_wiki_cli/services…ope.py:_validate_json_tree) | 1631 | `set(data not statically known)` |
| _validate_json_tree | walk (src/llm_wiki_cli/services…ope.py:_validate_json_tree) | 1672 | `walk(value, field_name)` |
| _hash_structured | sha256_digest | 1611 | `sha256_bytes(canonical_json_bytes(...))` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_component_configuration` | `isinstance` | 860 |
| unresolved_call | `_reject_machine_local_paths` | `walk` | 1762 |
| unresolved_call | `_hash_structured` | `payload.values` | 1609 |
| unresolved_call | `_validate_json_tree` | `walk` | 1672 |
| step_limit | `hash_component_configuration` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_component_configuration` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
