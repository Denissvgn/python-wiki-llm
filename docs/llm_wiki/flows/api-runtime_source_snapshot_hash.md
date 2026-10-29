# runtime_source_snapshot_hash

**Entry point:** `runtime_source_snapshot_hash` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_generation](../modules/knowledge_generation.md), and 1 more

**Complete modules touched:**

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_source_snapshot_hash
    participant p1 as hash_source_snapshot
    participant p2 as runtime_consumed_inputs
    participant p3 as _merge_explicit_consumed_input
    participant p4 as _hash_structured
    participant p5 as canonical_json_bytes
    participant p6 as KnowledgeEnvelopeError
    participant p7 as KnowledgeGenerationError
    participant p8 as is_valid_sha256
    participant p9 as _validate_json_tree
    participant p10 as sha256_bytes
    participant p11 as ConsumedInput
    participant p12 as canonical_json_text
    participant p13 as set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)
    participant p14 as source_snapshot.to_consumed_inputs
    participant p15 as isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)
    participant p16 as enumerate
    participant p17 as TypeError
    participant p18 as isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)
    participant p19 as seen_paths.add
    participant p20 as records.append
    participant p21 as generation_inputs.get
    participant p22 as records.sort
    participant p23 as tuple
    participant p24 as sorted
    participant p25 as openapi.get
    p0->>p1: hash_source_snapshot
    p0->>p2: runtime_consumed_inputs
    p2->>p3: _merge_explicit_consumed_input
    p1->>p4: _hash_structured
    p4->>p5: canonical_json_bytes
    p1->>p6: KnowledgeEnvelopeError
    p2->>p7: KnowledgeGenerationError
    p2->>p8: is_valid_sha256
    p4->>p9: _validate_json_tree
    p4->>p10: sha256_bytes
    p3->>p11: ConsumedInput
    p5->>p12: canonical_json_text
    p1-->>p13: set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)
    p2-->>p14: source_snapshot.to_consumed_inputs
    p2-->>p15: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)(source_snapshot, SourceSnapshot)
    p1-->>p16: enumerate(inputs)
    p2-->>p17: TypeError('source_snapshot must be a SourceSnapshot')
    p1-->>p18: isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)(item, ConsumedInput)
    p2-->>p15: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)(generation_inputs, Mapping)
    p2-->>p17: TypeError('generation_inputs must be a mapping')
    p1-->>p19: seen_paths.add(item.path)
    p1-->>p20: records.append({...})
    p2-->>p21: generation_inputs.get('openapi')
    p1-->>p22: records.sort(key=...)
    p2-->>p23: tuple(...)
    p2-->>p24: sorted(consumed_by_path)
    p2-->>p15: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)(openapi, Mapping)
    p2-->>p25: openapi.get('path')
    p2-->>p15: isinstance (src/llm_wiki_cli/services…py:runtime_consumed_inputs)(path, str)
    p2-->>p25: openapi.get('sha256')
```

> Call sequence diagram shows 30 of 54 interactions; 24 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 19 (8 omitted); unresolved 7 of 13 (6 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_source_snapshot` | 2 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_hash_structured` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validate_json_tree` | 13 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validate_json_tree` | 13 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 16 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 16 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_bytes` | 19 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_text` | 21 | - | external | 1 |
> Omission summary shows 8 of 18 groups; 10 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 23; effect analysis evaluated: 12, partial: 0, unavailable: 11. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `runtime_source_snapshot_hash` | `available` | `evaluated` | `available` |
| `hash_source_snapshot` | `available` | `evaluated` | `available` |
| `set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `enumerate` | `not_applicable` | `not_applicable` | `not_applicable` |
| `isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` |
| `seen_paths.add` | `not_applicable` | `not_applicable` | `not_applicable` |
| `records.append` | `not_applicable` | `not_applicable` | `not_applicable` |
| `records.sort` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_hash_structured` | `available` | `evaluated` | `available` |
| `payload.values` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. runtime_source_snapshot_hash"]
    s2["2. hash_source_snapshot"]
    s3["3. set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)"]
    s4["4. enumerate"]
    s5["5. isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. KnowledgeEnvelopeError"]
    s8["8. seen_paths.add"]
    s9["9. records.append"]
    s10["10. records.sort"]
    s11["11. _hash_structured"]
    s12["12. payload.values"]
    s1 -->|"hash_source_snapshot(runtime_consumed_inputs(...))"| s2
    s2 -. "set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)(data not statically known)" .-> s3
    s2 -. "enumerate(inputs)" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)(item, ConsumedInput)" .-> s5
    s2 -->|"KnowledgeEnvelopeError(..., 'must be a ConsumedInput')"| s6
    s2 -->|"KnowledgeEnvelopeError(..., ...)"| s7
    s2 -. "seen_paths.add(item.path)" .-> s8
    s2 -. "records.append({...})" .-> s9
    s2 -. "records.sort(key=...)" .-> s10
    s2 -->|"_hash_structured(SOURCE_SNAPSHOT_DOMAIN, {...}, 'source_inputs')"| s11
    s11 -. "payload.values(data not statically known)" .-> s12
    b0["mutation seen_paths.add"]
    s2 -. "mutation seen_paths.add" .-> b0
    b1["mutation records.append"]
    s2 -. "mutation records.append" .-> b1
    b2["mutation records.sort"]
    s2 -. "mutation records.sort" .-> b2
    click s1 "../modules/knowledge_orchestration.md"
    click s2 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `runtime_source_snapshot_hash` | `source_snapshot: SourceSnapshot`, `generation_inputs: Mapping[str, object]`, `plugin_lock_path: str \| None`, `plugin_lock_hash: str \| None` | - | - | `hash_source_snapshot(...)` |
| `hash_source_snapshot` | `inputs: Iterable[ConsumedInput]` | `ConsumedInput`, `SOURCE_SNAPSHOT_DOMAIN` | - | `_hash_structured(...)` |
| `set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `seen_paths.add` | - | - | - | - |
| `records.append` | - | - | - | - |
| `records.sort` | - | - | - | - |
| `_hash_structured` | `domain: str`, `payload: Mapping[str, Any]`, `field_name: str` | `KnowledgeEnvelopeError` | - | `sha256_bytes(...)` |
| `payload.values` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_source_snapshot_hash | hash_source_snapshot | 1548 | `hash_source_snapshot(runtime_consumed_inputs(...))` |
| hash_source_snapshot | set (src/llm_wiki_cli/services…pe.py:hash_source_snapshot) | 734 | `set(data not statically known)` |
| hash_source_snapshot | enumerate | 735 | `enumerate(inputs)` |
| hash_source_snapshot | isinstance (src/llm_wiki_cli/services…pe.py:hash_source_snapshot) | 736 | `isinstance(item, ConsumedInput)` |
| hash_source_snapshot | KnowledgeEnvelopeError | 737 | `KnowledgeEnvelopeError(..., 'must be a ConsumedInput')` |
| hash_source_snapshot | KnowledgeEnvelopeError | 742 | `KnowledgeEnvelopeError(..., ...)` |
| hash_source_snapshot | seen_paths.add | 746 | `seen_paths.add(item.path)` |
| hash_source_snapshot | records.append | 747 | `records.append({...})` |
| hash_source_snapshot | records.sort | 754 | `records.sort(key=...)` |
| hash_source_snapshot | _hash_structured | 755 | `_hash_structured(SOURCE_SNAPSHOT_DOMAIN, {...}, 'source_inputs')` |
| _hash_structured | payload.values | 1608 | `payload.values(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen_paths.add` | `hash_source_snapshot` | 746 |
| mutation | `records.append` | `hash_source_snapshot` | 747 |
| mutation | `records.sort` | `hash_source_snapshot` | 754 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_source_snapshot` | `enumerate` | 735 |
| external_call | `hash_source_snapshot` | `isinstance` | 736 |
| unresolved_call | `_hash_structured` | `payload.values` | 1608 |
| step_limit | `runtime_source_snapshot_hash` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_source_snapshot_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
