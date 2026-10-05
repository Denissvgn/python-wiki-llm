# hash_inventory

**Entry point:** `hash_inventory` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_inventory
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as inventory.items
    participant p4 as _repository_relative_path
    participant p5 as _hash_structured
    participant p6 as payload.values
    participant p7 as _validate_json_tree
    participant p8 as sha256_bytes
    participant p9 as canonical_json_bytes
    participant p10 as set
    participant p11 as hashlib.sha256(…).hexdigest
    participant p12 as canonical_json_text(…).encode
    participant p13 as walk
    participant p14 as hashlib.sha256
    participant p15 as canonical_json_text
    participant p16 as json.dumps
    p0-->>p1: isinstance(inventory, Mapping)
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: inventory.items
    p0-->>p1: isinstance(source_path, str)
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p4: _repository_relative_path(source_path, 'inventory.source_path')
    p0->>p5: _hash_structured
    p5-->>p6: payload.values
    p5->>p7: _validate_json_tree
    p5->>p8: sha256_bytes
    p5->>p9: canonical_json_bytes
    p5->>p2: KnowledgeEnvelopeError
    p7-->>p10: set
    p8-->>p11: hashlib.sha256(…).hexdigest
    p9-->>p12: canonical_json_text(…).encode('utf-8')
    p7-->>p13: walk(value, field_name)
    p8-->>p14: hashlib.sha256(value)
    p9->>p15: canonical_json_text
    p15-->>p16: json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)
```

> Call sequence diagram shows 19 of 19 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 6 of 6 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_inventory"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. inventory.items"]
    s5["5. isinstance"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. _repository_relative_path"]
    s8["8. _hash_structured"]
    s9["9. payload.values"]
    s10["10. _validate_json_tree"]
    s11["11. set"]
    s12["12. walk"]
    s1 -. "isinstance(inventory, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('inventory', 'must be an object')"| s3
    s1 -. "inventory.items(data not statically known)" .-> s4
    s1 -. "isinstance(source_path, str)" .-> s5
    s1 -->|"KnowledgeEnvelopeError('inventory', 'must use string source keys')"| s6
    s1 -. "_repository_relative_path(source_path, 'inventory.source_path')" .-> s7
    s1 -->|"_hash_structured(INVENTORY_SNAPSHOT_DOMAIN, {...}, 'inventory')"| s8
    s8 -. "payload.values(data not statically known)" .-> s9
    s8 -->|"_validate_json_tree(value, field_name)"| s10
    s10 -. "set(data not statically known)" .-> s11
    s10 -. "walk(value, field_name)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_inventory` | `inventory: Mapping[str, Any]` | `Mapping`, `INVENTORY_SNAPSHOT_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `inventory.items` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_repository_relative_path` | - | - | - | - |
| `_hash_structured` | `domain: str`, `payload: Mapping[str, Any]`, `field_name: str` | `KnowledgeEnvelopeError` | - | `sha256_bytes(...)` |
| `payload.values` | - | - | - | - |
| `_validate_json_tree` | `value: object`, `field_name: str` | - | - | - |
| `set` | - | - | - | - |
| `walk` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_inventory | isinstance | 765 | `isinstance(inventory, Mapping)` |
| hash_inventory | KnowledgeEnvelopeError | 766 | `KnowledgeEnvelopeError('inventory', 'must be an object')` |
| hash_inventory | inventory.items | 768 | `inventory.items(data not statically known)` |
| hash_inventory | isinstance | 769 | `isinstance(source_path, str)` |
| hash_inventory | KnowledgeEnvelopeError | 770 | `KnowledgeEnvelopeError('inventory', 'must use string source keys')` |
| hash_inventory | _repository_relative_path | 771 | `_repository_relative_path(source_path, 'inventory.source_path')` |
| hash_inventory | _hash_structured | 774 | `_hash_structured(INVENTORY_SNAPSHOT_DOMAIN, {...}, 'inventory')` |
| _hash_structured | payload.values | 1608 | `payload.values(data not statically known)` |
| _hash_structured | _validate_json_tree | 1609 | `_validate_json_tree(value, field_name)` |
| _validate_json_tree | set | 1630 | `set(data not statically known)` |
| _validate_json_tree | walk | 1671 | `walk(value, field_name)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_inventory` | `isinstance` | 765 |
| unresolved_call | `hash_inventory` | `inventory.items` | 768 |
| external_call | `hash_inventory` | `isinstance` | 769 |
| unresolved_call | `hash_inventory` | `_repository_relative_path` | 771 |
| unresolved_call | `_hash_structured` | `payload.values` | 1608 |
| unresolved_call | `_validate_json_tree` | `walk` | 1671 |
| step_limit | `hash_inventory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_inventory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
