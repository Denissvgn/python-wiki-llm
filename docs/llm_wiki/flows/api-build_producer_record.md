# build_producer_record

**Entry point:** `build_producer_record` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_model](../modules/knowledge_model.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_producer_record
    participant p1 as _build_component
    participant p2 as isinstance
    participant p3 as KnowledgeEnvelopeError
    participant p4 as fullmatch
    participant p5 as set
    participant p6 as _validated_limitations
    participant p7 as tuple
    participant p8 as enumerate
    participant p9 as add
    participant p10 as strip
    participant p11 as any
    participant p12 as ord
    participant p13 as _reject_machine_local_paths
    participant p14 as walk
    participant p15 as hash_component_configuration
    p0->>p1: _build_component
    p1-->>p2: isinstance
    p1->>p3: KnowledgeEnvelopeError
    p1-->>p2: isinstance
    p1-->>p4: fullmatch
    p1->>p3: KnowledgeEnvelopeError
    p1-->>p5: set
    p1->>p6: _validated_limitations
    p6-->>p2: isinstance
    p6->>p3: KnowledgeEnvelopeError
    p6-->>p7: tuple
    p6->>p3: KnowledgeEnvelopeError
    p6-->>p8: enumerate
    p6-->>p2: isinstance
    p6-->>p4: fullmatch
    p6->>p3: KnowledgeEnvelopeError
    p1-->>p9: add
    p1-->>p2: isinstance
    p1-->>p10: strip
    p1-->>p11: any
    p1-->>p12: ord
    p1->>p3: KnowledgeEnvelopeError
    p1->>p13: _reject_machine_local_paths
    p13-->>p5: set
    p13-->>p14: walk
    p1->>p3: KnowledgeEnvelopeError
    p1-->>p9: add
    p1->>p3: KnowledgeEnvelopeError
    p1->>p15: hash_component_configuration
    p15-->>p2: isinstance
```

> Call sequence diagram shows 30 of 72 interactions; 42 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_producer_record"]
    s2["2. _build_component"]
    s3["3. isinstance"]
    s4["4. KnowledgeEnvelopeError"]
    s5["5. isinstance"]
    s6["6. fullmatch"]
    s7["7. KnowledgeEnvelopeError"]
    s8["8. set"]
    s9["9. _validated_limitations"]
    s10["10. isinstance"]
    s11["11. KnowledgeEnvelopeError"]
    s12["12. tuple"]
    s1 -->|"_build_component(tool, 'producer.tool', analyzer=False)"| s2
    s2 -. "isinstance(value, ProducerComponentInput)" .-> s3
    s2 -->|"KnowledgeEnvelopeError(field_name, 'must be a ProducerComponentInput')"| s4
    s2 -. "isinstance(value.component_id, str)" .-> s5
    s2 -. "_COMPONENT_ID_RE.fullmatch(value.component_id)" .-> s6
    s2 -->|"KnowledgeEnvelopeError(..., 'must be a normalized producer component ID')"| s7
    s2 -. "set(_validated_limitations(...))" .-> s8
    s2 -->|"_validated_limitations(value.limitations, field_name)"| s9
    s9 -. "isinstance(value, (...))" .-> s10
    s9 -->|"KnowledgeEnvelopeError(..., 'must be an iterable of machine codes, not scalar text or bytes')"| s11
    s9 -. "tuple(value)" .-> s12
    b0["mutation limitations.add"]
    s2 -. "mutation limitations.add" .-> b0
    b1["mutation limitations.add"]
    s2 -. "mutation limitations.add" .-> b1
    click s1 "../modules/knowledge_envelope.md"
    click s2 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s9 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_producer_record` | `tool: ProducerComponentInput`, `extractors: Iterable[ProducerComponentInput]`, `plugins: Iterable[ProducerComponentInput]`, `extensions: Mapping[str, Any] \| None` | - | - | `producer` |
| `_build_component` | `value: ProducerComponentInput`, `field_name: str`, `analyzer: bool` | `ProducerComponentInput`, `UNKNOWN_COMPONENT_VERSION`, `UNKNOWN_COMPONENT_VERSION`, `VERSION_UNKNOWN`, `VERSION_UNKNOWN`, `VERSION_UNKNOWN`, `CONFIGURATION_BASIS_UNKNOWN`, `CONFIGURATION_BASIS_UNKNOWN` | - | `ProducerComponent(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `set` | - | - | - | - |
| `_validated_limitations` | `value: Iterable[str]`, `field_name: str` | - | - | `limitations` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `tuple` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_producer_record | _build_component | 952 | `_build_component(tool, 'producer.tool', analyzer=False)` |
| _build_component | isinstance | 1664 | `isinstance(value, ProducerComponentInput)` |
| _build_component | KnowledgeEnvelopeError | 1665 | `KnowledgeEnvelopeError(field_name, 'must be a ProducerComponentInput')` |
| _build_component | isinstance | 1670 | `isinstance(value.component_id, str)` |
| _build_component | fullmatch | 1671 | `_COMPONENT_ID_RE.fullmatch(value.component_id)` |
| _build_component | KnowledgeEnvelopeError | 1673 | `KnowledgeEnvelopeError(..., 'must be a normalized producer component ID')` |
| _build_component | set | 1677 | `set(_validated_limitations(...))` |
| _build_component | _validated_limitations | 1677 | `_validated_limitations(value.limitations, field_name)` |
| _validated_limitations | isinstance | 1727 | `isinstance(value, (...))` |
| _validated_limitations | KnowledgeEnvelopeError | 1728 | `KnowledgeEnvelopeError(..., 'must be an iterable of machine codes, not scalar text or bytes')` |
| _validated_limitations | tuple | 1733 | `tuple(value)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `limitations.add` | `_build_component` | 1680 |
| mutation | `limitations.add` | `_build_component` | 1704 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_build_component` | `isinstance` | 1664 |
| unresolved_call | `_build_component` | `isinstance` | 1670 |
| unresolved_call | `_build_component` | `_COMPONENT_ID_RE.fullmatch` | 1671 |
| unresolved_call | `_validated_limitations` | `isinstance` | 1727 |
| step_limit | `build_producer_record` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_producer_record` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
