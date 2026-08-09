# hash_generation_options

**Entry point:** `hash_generation_options` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_generation_options
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as _normalized_allowlist
    participant p4 as tuple
    participant p5 as any
    participant p6 as len
    participant p7 as set
    participant p8 as sorted
    participant p9 as _reject_unknown_option_keys
    participant p10 as min
    participant p11 as _reject_machine_local_paths
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0->>p3: _normalized_allowlist
    p3-->>p1: isinstance
    p3->>p2: KnowledgeEnvelopeError
    p3-->>p4: tuple
    p3->>p2: KnowledgeEnvelopeError
    p3-->>p5: any
    p3-->>p1: isinstance
    p3->>p2: KnowledgeEnvelopeError
    p3-->>p6: len
    p3-->>p6: len
    p3-->>p7: set
    p3->>p2: KnowledgeEnvelopeError
    p3-->>p4: tuple
    p3-->>p8: sorted
    p0->>p9: _reject_unknown_option_keys
    p9-->>p5: any
    p9-->>p1: isinstance
    p9->>p2: KnowledgeEnvelopeError
    p9-->>p7: set
    p9-->>p7: set
    p9-->>p10: min
    p9->>p2: KnowledgeEnvelopeError
    p0->>p9: _reject_unknown_option_keys
    p0->>p2: KnowledgeEnvelopeError
    p0->>p11: _reject_machine_local_paths
    p11-->>p7: set
```

> Call sequence diagram shows 30 of 44 interactions; 14 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_generation_options"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. isinstance"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. _normalized_allowlist"]
    s7["7. isinstance"]
    s8["8. KnowledgeEnvelopeError"]
    s9["9. tuple"]
    s10["10. KnowledgeEnvelopeError"]
    s11["11. any"]
    s12["12. isinstance"]
    s1 -. "isinstance(values, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('generation_options', 'must be an object')"| s3
    s1 -. "isinstance(defaults, Mapping)" .-> s4
    s1 -->|"KnowledgeEnvelopeError('generation_option_defaults', 'must be an object')"| s5
    s1 -->|"_normalized_allowlist(allowlist)"| s6
    s6 -. "isinstance(value, (...))" .-> s7
    s6 -->|"KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names, not scalar text or bytes')"| s8
    s6 -. "tuple(value)" .-> s9
    s6 -->|"KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names')"| s10
    s6 -. "any(...)" .-> s11
    s6 -. "isinstance(item, str)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_generation_options` | `values: Mapping[str, Any]`, `defaults: Mapping[str, Any]`, `allowlist: Iterable[str]` | `Mapping`, `Mapping`, `GENERATION_OPTIONS_DOMAIN` | `effective[...]`, `effective[...]` | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_normalized_allowlist` | `value: Iterable[str]` | - | - | `tuple(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `tuple` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_generation_options | isinstance | 825 | `isinstance(values, Mapping)` |
| hash_generation_options | KnowledgeEnvelopeError | 826 | `KnowledgeEnvelopeError('generation_options', 'must be an object')` |
| hash_generation_options | isinstance | 827 | `isinstance(defaults, Mapping)` |
| hash_generation_options | KnowledgeEnvelopeError | 828 | `KnowledgeEnvelopeError('generation_option_defaults', 'must be an object')` |
| hash_generation_options | _normalized_allowlist | 832 | `_normalized_allowlist(allowlist)` |
| _normalized_allowlist | isinstance | 1656 | `isinstance(value, (...))` |
| _normalized_allowlist | KnowledgeEnvelopeError | 1657 | `KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names, not scalar text or bytes')` |
| _normalized_allowlist | tuple | 1662 | `tuple(value)` |
| _normalized_allowlist | KnowledgeEnvelopeError | 1664 | `KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names')` |
| _normalized_allowlist | any | 1668 | `any(...)` |
| _normalized_allowlist | isinstance | 1668 | `isinstance(item, str)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `hash_generation_options` | `isinstance` | 825 |
| unresolved_call | `hash_generation_options` | `isinstance` | 827 |
| unresolved_call | `_normalized_allowlist` | `isinstance` | 1656 |
| unresolved_call | `_normalized_allowlist` | `any` | 1668 |
| unresolved_call | `_normalized_allowlist` | `isinstance` | 1668 |
| step_limit | `hash_generation_options` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_generation_options` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
