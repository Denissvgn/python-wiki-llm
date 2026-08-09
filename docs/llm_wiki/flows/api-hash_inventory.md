# hash_inventory

**Entry point:** `hash_inventory` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_inventory
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as items
    participant p4 as _repository_relative_path
    participant p5 as require_repository_relative_path
    participant p6 as strip
    participant p7 as any
    participant p8 as ord
    participant p9 as startswith
    participant p10 as match
    participant p11 as split
    participant p12 as PurePosixPath
    participant p13 as normpath
    participant p14 as require_portable_relative_path
    participant p15 as _default_path_error
    participant p16 as SharedValidationError
    participant p17 as fspath
    participant p18 as encode
    participant p19 as replace
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: items
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0->>p4: _repository_relative_path
    p4->>p5: require_repository_relative_path
    p5-->>p1: isinstance
    p5-->>p6: strip
    p5-->>p7: any
    p5-->>p8: ord
    p5-->>p8: ord
    p5-->>p9: startswith
    p5-->>p9: startswith
    p5-->>p10: match
    p5-->>p11: split
    p5-->>p12: PurePosixPath
    p5-->>p7: any
    p5-->>p13: normpath
    p5->>p14: require_portable_relative_path
    p14-->>p1: isinstance
    p14->>p15: _default_path_error
    p15->>p16: SharedValidationError
    p14-->>p17: fspath
    p14-->>p1: isinstance
    p14->>p15: _default_path_error
    p14-->>p18: encode
    p14->>p15: _default_path_error
    p14->>p15: _default_path_error
    p14-->>p19: replace
```

> Call sequence diagram shows 30 of 78 interactions; 48 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_inventory"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. items"]
    s5["5. isinstance"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. _repository_relative_path"]
    s8["8. require_repository_relative_path"]
    s9["9. isinstance"]
    s10["10. strip"]
    s11["11. any"]
    s12["12. ord"]
    s1 -. "isinstance(inventory, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('inventory', 'must be an object')"| s3
    s1 -. "inventory.items(data not statically known)" .-> s4
    s1 -. "isinstance(source_path, str)" .-> s5
    s1 -->|"KnowledgeEnvelopeError('inventory', 'must use string source keys')"| s6
    s1 -->|"_repository_relative_path(source_path, 'inventory.source_path')"| s7
    s7 -->|"require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeErro…"| s8
    s8 -. "isinstance(value, str)" .-> s9
    s8 -. "value.strip(data not statically known)" .-> s10
    s8 -. "any(...)" .-> s11
    s8 -. "ord(character)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s8 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_inventory` | `inventory: Mapping[str, Any]` | `Mapping`, `INVENTORY_SNAPSHOT_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `items` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_repository_relative_path` | `value: object`, `field_name: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `require_portable_relative_path(...)` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_inventory | isinstance | 763 | `isinstance(inventory, Mapping)` |
| hash_inventory | KnowledgeEnvelopeError | 764 | `KnowledgeEnvelopeError('inventory', 'must be an object')` |
| hash_inventory | items | 766 | `inventory.items(data not statically known)` |
| hash_inventory | isinstance | 767 | `isinstance(source_path, str)` |
| hash_inventory | KnowledgeEnvelopeError | 768 | `KnowledgeEnvelopeError('inventory', 'must use string source keys')` |
| hash_inventory | _repository_relative_path | 769 | `_repository_relative_path(source_path, 'inventory.source_path')` |
| _repository_relative_path | require_repository_relative_path | 1486 | `require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeError(...))` |
| require_repository_relative_path | isinstance | 256 | `isinstance(value, str)` |
| require_repository_relative_path | strip | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any | 260 | `any(...)` |
| require_repository_relative_path | ord | 261 | `ord(character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `hash_inventory` | `isinstance` | 763 |
| unresolved_call | `hash_inventory` | `inventory.items` | 766 |
| unresolved_call | `hash_inventory` | `isinstance` | 767 |
| unresolved_call | `require_repository_relative_path` | `isinstance` | 256 |
| unresolved_call | `require_repository_relative_path` | `value.strip` | 258 |
| unresolved_call | `require_repository_relative_path` | `any` | 260 |
| unresolved_call | `require_repository_relative_path` | `ord` | 261 |
| step_limit | `hash_inventory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_inventory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
