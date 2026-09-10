# hash_inventory

**Entry point:** `hash_inventory` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

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
    participant p8 as set
    participant p9 as walk
    participant p10 as sha256_bytes
    participant p11 as hashlib.sha256(…).hexdigest
    participant p12 as hashlib.sha256
    participant p13 as canonical_json_bytes
    participant p14 as canonical_json_text(…).encode
    participant p15 as canonical_json_text
    participant p16 as json.dumps
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: inventory.items
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p4: _repository_relative_path
    p0->>p5: _hash_structured
    p5-->>p6: payload.values
    p5->>p7: _validate_json_tree
    p7-->>p8: set
    p7-->>p9: walk
    p5->>p10: sha256_bytes
    p10-->>p11: hashlib.sha256(…).hexdigest
    p10-->>p12: hashlib.sha256
    p5->>p13: canonical_json_bytes
    p13-->>p14: canonical_json_text(…).encode
    p13->>p15: canonical_json_text
    p15-->>p16: json.dumps
    p5->>p2: KnowledgeEnvelopeError
```

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
| _hash_structured | payload.values | 1604 | `payload.values(data not statically known)` |
| _hash_structured | _validate_json_tree | 1605 | `_validate_json_tree(value, field_name)` |
| _validate_json_tree | set | 1626 | `set(data not statically known)` |
| _validate_json_tree | walk | 1667 | `walk(value, field_name)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_inventory` | `isinstance` | 765 |
| unresolved_call | `hash_inventory` | `inventory.items` | 768 |
| external_call | `hash_inventory` | `isinstance` | 769 |
| unresolved_call | `hash_inventory` | `_repository_relative_path` | 771 |
| unresolved_call | `_hash_structured` | `payload.values` | 1604 |
| unresolved_call | `_validate_json_tree` | `walk` | 1667 |
| step_limit | `hash_inventory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_inventory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
