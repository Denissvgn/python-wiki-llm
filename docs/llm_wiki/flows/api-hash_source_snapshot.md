# hash_source_snapshot

**Entry point:** `hash_source_snapshot` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_source_snapshot
    participant p1 as set
    participant p2 as enumerate
    participant p3 as isinstance
    participant p4 as KnowledgeEnvelopeError
    participant p5 as add
    participant p6 as append
    participant p7 as sort
    participant p8 as _hash_structured
    participant p9 as values
    participant p10 as _validate_json_tree
    participant p11 as walk
    participant p12 as sha256_bytes
    participant p13 as hexdigest
    participant p14 as sha256
    participant p15 as canonical_json_bytes
    participant p16 as encode
    participant p17 as canonical_json_text
    participant p18 as dumps
    p0-->>p1: set
    p0-->>p2: enumerate
    p0-->>p3: isinstance
    p0->>p4: KnowledgeEnvelopeError
    p0->>p4: KnowledgeEnvelopeError
    p0-->>p5: add
    p0-->>p6: append
    p0-->>p7: sort
    p0->>p8: _hash_structured
    p8-->>p9: values
    p8->>p10: _validate_json_tree
    p10-->>p1: set
    p10-->>p11: walk
    p8->>p12: sha256_bytes
    p12-->>p13: hexdigest
    p12-->>p14: sha256
    p8->>p15: canonical_json_bytes
    p15-->>p16: encode
    p15->>p17: canonical_json_text
    p17-->>p18: dumps
    p8->>p4: KnowledgeEnvelopeError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_source_snapshot"]
    s2["2. set"]
    s3["3. enumerate"]
    s4["4. isinstance"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. add"]
    s8["8. append"]
    s9["9. sort"]
    s10["10. _hash_structured"]
    s11["11. values"]
    s12["12. _validate_json_tree"]
    s1 -. "set(data not statically known)" .-> s2
    s1 -. "enumerate(inputs)" .-> s3
    s1 -. "isinstance(item, ConsumedInput)" .-> s4
    s1 -->|"KnowledgeEnvelopeError(..., 'must be a ConsumedInput')"| s5
    s1 -->|"KnowledgeEnvelopeError(..., ...)"| s6
    s1 -. "seen_paths.add(item.path)" .-> s7
    s1 -. "records.append({...})" .-> s8
    s1 -. "records.sort(key=...)" .-> s9
    s1 -->|"_hash_structured(SOURCE_SNAPSHOT_DOMAIN, {...}, 'source_inputs')"| s10
    s10 -. "payload.values(data not statically known)" .-> s11
    s10 -->|"_validate_json_tree(value, field_name)"| s12
    b0["mutation seen_paths.add"]
    s1 -. "mutation seen_paths.add" .-> b0
    b1["mutation records.append"]
    s1 -. "mutation records.append" .-> b1
    b2["mutation records.sort"]
    s1 -. "mutation records.sort" .-> b2
    click s1 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `_validate_json_tree` | `value: object`, `field_name: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _hash_structured | _validate_json_tree | 1485 | `_validate_json_tree(value, field_name)` |

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
| step_limit | `hash_source_snapshot` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_source_snapshot` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
