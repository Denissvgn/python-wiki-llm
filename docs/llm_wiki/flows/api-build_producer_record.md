# build_producer_record

**Entry point:** `build_producer_record` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_model](../modules/knowledge_model.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_producer_record
    participant p1 as _build_component
    participant p2 as tuple (src/llm_wiki_cli/services…e.py:build_producer_record)
    participant p3 as sorted (src/llm_wiki_cli/services…e.py:build_producer_record)
    participant p4 as enumerate (src/llm_wiki_cli/services…e.py:build_producer_record)
    participant p5 as ProducerRecord
    participant p6 as _extensions_copy
    participant p7 as len
    participant p8 as set (src/llm_wiki_cli/services…e.py:build_producer_record)
    participant p9 as next
    participant p10 as ids.count
    participant p11 as KnowledgeEnvelopeError
    participant p12 as isinstance (src/llm_wiki_cli/services…velope.py:_build_component)
    participant p13 as _COMPONENT_ID_RE.fullmatch
    participant p14 as set (src/llm_wiki_cli/services…velope.py:_build_component)
    participant p15 as _validated_limitations
    participant p16 as limitations.add
    participant p17 as value.version.strip
    participant p18 as any (src/llm_wiki_cli/services…velope.py:_build_component)
    participant p19 as ord
    p0->>p1: _build_component
    p0-->>p2: tuple (src/llm_wiki_cli/services…e.py:build_producer_record)(sorted(...))
    p0-->>p3: sorted (src/llm_wiki_cli/services…e.py:build_producer_record)(..., key=...)
    p0->>p1: _build_component
    p0-->>p4: enumerate (src/llm_wiki_cli/services…e.py:build_producer_record)(extractors)
    p0-->>p2: tuple (src/llm_wiki_cli/services…e.py:build_producer_record)(sorted(...))
    p0-->>p3: sorted (src/llm_wiki_cli/services…e.py:build_producer_record)(..., key=...)
    p0->>p1: _build_component
    p0-->>p4: enumerate (src/llm_wiki_cli/services…e.py:build_producer_record)(plugins)
    p0->>p5: ProducerRecord
    p0->>p6: _extensions_copy
    p0-->>p7: len(ids)
    p0-->>p7: len(set(...))
    p0-->>p8: set (src/llm_wiki_cli/services…e.py:build_producer_record)(ids)
    p0-->>p9: next(...)
    p0-->>p10: ids.count(item)
    p0->>p11: KnowledgeEnvelopeError
    p1-->>p12: isinstance (src/llm_wiki_cli/services…velope.py:_build_component)(value, ProducerComponentInput)
    p1->>p11: KnowledgeEnvelopeError
    p1-->>p12: isinstance (src/llm_wiki_cli/services…velope.py:_build_component)(value.component_id, str)
    p1-->>p13: _COMPONENT_ID_RE.fullmatch(value.component_id)
    p1->>p11: KnowledgeEnvelopeError
    p1-->>p14: set (src/llm_wiki_cli/services…velope.py:_build_component)(_validated_limitations(...))
    p1->>p15: _validated_limitations
    p1-->>p16: limitations.add(VERSION_UNKNOWN)
    p1-->>p12: isinstance (src/llm_wiki_cli/services…velope.py:_build_component)(value.version, str)
    p1-->>p17: value.version.strip
    p1-->>p18: any (src/llm_wiki_cli/services…velope.py:_build_component)(...)
    p1-->>p19: ord(char)
    p1->>p11: KnowledgeEnvelopeError
```

> Call sequence diagram shows 30 of 72 interactions; 42 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 31 (15 omitted); unresolved 4 of 11 (7 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_limitations` | 9 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_limitations` | 9 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validated_limitations` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_build_component` | 2 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 5 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_machine_local_paths` | 24 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_machine_local_paths` | 24 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_build_component` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_component_configuration` | 30 | - | external | 1 |
> Omission summary shows 8 of 23 groups; 15 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_producer_record"]
    s2["2. _build_component"]
    s3["3. isinstance (src/llm_wiki_cli/services…velope.py:_build_component)"]
    s4["4. KnowledgeEnvelopeError"]
    s5["5. isinstance (src/llm_wiki_cli/services…velope.py:_build_component)"]
    s6["6. _COMPONENT_ID_RE.fullmatch"]
    s7["7. KnowledgeEnvelopeError"]
    s8["8. set (src/llm_wiki_cli/services…velope.py:_build_component)"]
    s9["9. _validated_limitations"]
    s10["10. isinstance (src/llm_wiki_cli/services….py:_validated_limitations)"]
    s11["11. KnowledgeEnvelopeError"]
    s12["12. tuple (src/llm_wiki_cli/services….py:_validated_limitations)"]
    s1 -->|"_build_component(tool, 'producer.tool', analyzer=False)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…velope.py:_build_component)(value, ProducerComponentInput)" .-> s3
    s2 -->|"KnowledgeEnvelopeError(field_name, 'must be a ProducerComponentInput')"| s4
    s2 -. "isinstance (src/llm_wiki_cli/services…velope.py:_build_component)(value.component_id, str)" .-> s5
    s2 -. "_COMPONENT_ID_RE.fullmatch(value.component_id)" .-> s6
    s2 -->|"KnowledgeEnvelopeError(..., 'must be a normalized producer component ID')"| s7
    s2 -. "set (src/llm_wiki_cli/services…velope.py:_build_component)(_validated_limitations(...))" .-> s8
    s2 -->|"_validated_limitations(value.limitations, field_name)"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services….py:_validated_limitations)(value, (...))" .-> s10
    s9 -->|"KnowledgeEnvelopeError(..., 'must be an iterable of machine codes, not scalar text or bytes')"| s11
    s9 -. "tuple (src/llm_wiki_cli/services….py:_validated_limitations)(value)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…velope.py:_build_component)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…velope.py:_build_component)` | - | - | - | - |
| `_COMPONENT_ID_RE.fullmatch` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `set (src/llm_wiki_cli/services…velope.py:_build_component)` | - | - | - | - |
| `_validated_limitations` | `value: Iterable[str]`, `field_name: str` | - | - | `limitations` |
| `isinstance (src/llm_wiki_cli/services….py:_validated_limitations)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services….py:_validated_limitations)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_producer_record | _build_component | 962 | `_build_component(tool, 'producer.tool', analyzer=False)` |
| _build_component | isinstance (src/llm_wiki_cli/services…velope.py:_build_component) | 1788 | `isinstance(value, ProducerComponentInput)` |
| _build_component | KnowledgeEnvelopeError | 1789 | `KnowledgeEnvelopeError(field_name, 'must be a ProducerComponentInput')` |
| _build_component | isinstance (src/llm_wiki_cli/services…velope.py:_build_component) | 1794 | `isinstance(value.component_id, str)` |
| _build_component | _COMPONENT_ID_RE.fullmatch | 1795 | `_COMPONENT_ID_RE.fullmatch(value.component_id)` |
| _build_component | KnowledgeEnvelopeError | 1797 | `KnowledgeEnvelopeError(..., 'must be a normalized producer component ID')` |
| _build_component | set (src/llm_wiki_cli/services…velope.py:_build_component) | 1801 | `set(_validated_limitations(...))` |
| _build_component | _validated_limitations | 1801 | `_validated_limitations(value.limitations, field_name)` |
| _validated_limitations | isinstance (src/llm_wiki_cli/services….py:_validated_limitations) | 1851 | `isinstance(value, (...))` |
| _validated_limitations | KnowledgeEnvelopeError | 1852 | `KnowledgeEnvelopeError(..., 'must be an iterable of machine codes, not scalar text or bytes')` |
| _validated_limitations | tuple (src/llm_wiki_cli/services….py:_validated_limitations) | 1857 | `tuple(value)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `limitations.add` | `_build_component` | 1804 |
| mutation | `limitations.add` | `_build_component` | 1828 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_build_component` | `isinstance` | 1788 |
| external_call | `_build_component` | `isinstance` | 1794 |
| unresolved_call | `_build_component` | `_COMPONENT_ID_RE.fullmatch` | 1795 |
| external_call | `_validated_limitations` | `isinstance` | 1851 |
| step_limit | `build_producer_record` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_producer_record` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
