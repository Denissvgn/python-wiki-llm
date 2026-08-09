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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_source_snapshot_hash
    participant p1 as hash_source_snapshot
    participant p2 as set
    participant p3 as enumerate
    participant p4 as isinstance
    participant p5 as KnowledgeEnvelopeError
    participant p6 as add
    participant p7 as append
    participant p8 as sort
    participant p9 as _hash_structured
    participant p10 as values
    participant p11 as _validate_json_tree
    participant p12 as walk
    participant p13 as sha256_bytes
    participant p14 as hexdigest
    participant p15 as sha256
    participant p16 as canonical_json_bytes
    participant p17 as encode
    participant p18 as canonical_json_text
    participant p19 as dumps
    participant p20 as runtime_consumed_inputs
    participant p21 as TypeError
    participant p22 as to_consumed_inputs
    participant p23 as _merge_explicit_consumed_input
    participant p24 as KnowledgeGenerationError
    p0->>p1: hash_source_snapshot
    p1-->>p2: set
    p1-->>p3: enumerate
    p1-->>p4: isinstance
    p1->>p5: KnowledgeEnvelopeError
    p1->>p5: KnowledgeEnvelopeError
    p1-->>p6: add
    p1-->>p7: append
    p1-->>p8: sort
    p1->>p9: _hash_structured
    p9-->>p10: values
    p9->>p11: _validate_json_tree
    p11-->>p2: set
    p11-->>p12: walk
    p9->>p13: sha256_bytes
    p13-->>p14: hexdigest
    p13-->>p15: sha256
    p9->>p16: canonical_json_bytes
    p16-->>p17: encode
    p16->>p18: canonical_json_text
    p18-->>p19: dumps
    p9->>p5: KnowledgeEnvelopeError
    p0->>p20: runtime_consumed_inputs
    p20-->>p4: isinstance
    p20-->>p21: TypeError
    p20-->>p4: isinstance
    p20-->>p21: TypeError
    p20-->>p22: to_consumed_inputs
    p20->>p23: _merge_explicit_consumed_input
    p23->>p24: KnowledgeGenerationError
```

> Call sequence diagram shows 30 of 54 interactions; 24 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. runtime_source_snapshot_hash"]
    s2["2. hash_source_snapshot"]
    s3["3. set"]
    s4["4. enumerate"]
    s5["5. isinstance"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. KnowledgeEnvelopeError"]
    s8["8. add"]
    s9["9. append"]
    s10["10. sort"]
    s11["11. _hash_structured"]
    s12["12. values"]
    s1 -->|"hash_source_snapshot(runtime_consumed_inputs(...))"| s2
    s2 -. "set(data not statically known)" .-> s3
    s2 -. "enumerate(inputs)" .-> s4
    s2 -. "isinstance(item, ConsumedInput)" .-> s5
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
| `set` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `add` | - | - | - | - |
| `append` | - | - | - | - |
| `sort` | - | - | - | - |
| `_hash_structured` | `domain: str`, `payload: Mapping[str, Any]`, `field_name: str` | `KnowledgeEnvelopeError` | - | `sha256_bytes(...)` |
| `values` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_source_snapshot_hash | hash_source_snapshot | 1237 | `hash_source_snapshot(runtime_consumed_inputs(...))` |
| hash_source_snapshot | set | 725 | `set(data not statically known)` |
| hash_source_snapshot | enumerate | 726 | `enumerate(inputs)` |
| hash_source_snapshot | isinstance | 727 | `isinstance(item, ConsumedInput)` |
| hash_source_snapshot | KnowledgeEnvelopeError | 728 | `KnowledgeEnvelopeError(..., 'must be a ConsumedInput')` |
| hash_source_snapshot | KnowledgeEnvelopeError | 733 | `KnowledgeEnvelopeError(..., ...)` |
| hash_source_snapshot | add | 737 | `seen_paths.add(item.path)` |
| hash_source_snapshot | append | 738 | `records.append({...})` |
| hash_source_snapshot | sort | 745 | `records.sort(key=...)` |
| hash_source_snapshot | _hash_structured | 746 | `_hash_structured(SOURCE_SNAPSHOT_DOMAIN, {...}, 'source_inputs')` |
| _hash_structured | values | 1484 | `payload.values(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen_paths.add` | `hash_source_snapshot` | 737 |
| mutation | `records.append` | `hash_source_snapshot` | 738 |
| mutation | `records.sort` | `hash_source_snapshot` | 745 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `hash_source_snapshot` | `enumerate` | 726 |
| unresolved_call | `hash_source_snapshot` | `isinstance` | 727 |
| unresolved_call | `_hash_structured` | `payload.values` | 1484 |
| step_limit | `runtime_source_snapshot_hash` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_source_snapshot_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
