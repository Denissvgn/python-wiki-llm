# build_evaluated_envelope

**Entry point:** `build_evaluated_envelope` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_evaluated_envelope
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as KnowledgeEnvelopeError
    participant p4 as _extensions_copy
    participant p5 as any
    participant p6 as _reject_machine_local_paths
    participant p7 as set
    participant p8 as walk
    participant p9 as dict
    participant p10 as hash_source_snapshot
    participant p11 as enumerate
    participant p12 as add
    participant p13 as append
    participant p14 as sort
    participant p15 as _hash_structured
    participant p16 as values
    participant p17 as _validate_json_tree
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0->>p3: KnowledgeEnvelopeError
    p0->>p4: _extensions_copy
    p4-->>p1: isinstance
    p4->>p3: KnowledgeEnvelopeError
    p4-->>p5: any
    p4-->>p1: isinstance
    p4->>p3: KnowledgeEnvelopeError
    p4->>p6: _reject_machine_local_paths
    p6-->>p7: set
    p6-->>p8: walk
    p4-->>p9: dict
    p0-->>p1: isinstance
    p0->>p3: KnowledgeEnvelopeError
    p0->>p10: hash_source_snapshot
    p10-->>p7: set
    p10-->>p11: enumerate
    p10-->>p1: isinstance
    p10->>p3: KnowledgeEnvelopeError
    p10->>p3: KnowledgeEnvelopeError
    p10-->>p12: add
    p10-->>p13: append
    p10-->>p14: sort
    p10->>p15: _hash_structured
    p15-->>p16: values
    p15->>p17: _validate_json_tree
    p17-->>p7: set
    p17-->>p8: walk
```

> Call sequence diagram shows 30 of 490 interactions; 460 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_evaluated_envelope"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. _extensions_copy"]
    s7["7. isinstance"]
    s8["8. KnowledgeEnvelopeError"]
    s9["9. any"]
    s10["10. isinstance"]
    s11["11. KnowledgeEnvelopeError"]
    s12["12. _reject_machine_local_paths"]
    s1 -. "isinstance(inputs, EnvelopeInputs)" .-> s2
    s1 -. "TypeError('inputs must be an EnvelopeInputs')" .-> s3
    s1 -. "isinstance(inputs.repository, RepositoryRecord)" .-> s4
    s1 -->|"KnowledgeEnvelopeError('repository', 'must be a pre-evaluated RepositoryRecord')"| s5
    s1 -->|"_extensions_copy(inputs.repository.extensions, 'repository.extensions')"| s6
    s6 -. "isinstance(value, Mapping)" .-> s7
    s6 -->|"KnowledgeEnvelopeError(field_name, 'must be an object')"| s8
    s6 -. "any(...)" .-> s9
    s6 -. "isinstance(key, str)" .-> s10
    s6 -->|"KnowledgeEnvelopeError(field_name, 'must use string extension keys')"| s11
    s6 -->|"_reject_machine_local_paths(value, field_name)"| s12
    click s1 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_evaluated_envelope` | `inputs: EnvelopeInputs` | `EnvelopeInputs`, `RepositoryRecord`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | `snapshot_extensions[...]` | `envelope` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_extensions_copy` | `value: Mapping[str, Any]`, `field_name: str` | `Mapping` | - | `dict(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_reject_machine_local_paths` | `value: object`, `field_name: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_evaluated_envelope | isinstance | 892 | `isinstance(inputs, EnvelopeInputs)` |
| build_evaluated_envelope | TypeError | 893 | `TypeError('inputs must be an EnvelopeInputs')` |
| build_evaluated_envelope | isinstance | 894 | `isinstance(inputs.repository, RepositoryRecord)` |
| build_evaluated_envelope | KnowledgeEnvelopeError | 895 | `KnowledgeEnvelopeError('repository', 'must be a pre-evaluated RepositoryRecord')` |
| build_evaluated_envelope | _extensions_copy | 899 | `_extensions_copy(inputs.repository.extensions, 'repository.extensions')` |
| _extensions_copy | isinstance | 1755 | `isinstance(value, Mapping)` |
| _extensions_copy | KnowledgeEnvelopeError | 1756 | `KnowledgeEnvelopeError(field_name, 'must be an object')` |
| _extensions_copy | any | 1757 | `any(...)` |
| _extensions_copy | isinstance | 1757 | `isinstance(key, str)` |
| _extensions_copy | KnowledgeEnvelopeError | 1758 | `KnowledgeEnvelopeError(field_name, 'must use string extension keys')` |
| _extensions_copy | _reject_machine_local_paths | 1759 | `_reject_machine_local_paths(value, field_name)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_evaluated_envelope` | `isinstance` | 892 |
| unresolved_call | `build_evaluated_envelope` | `TypeError` | 893 |
| unresolved_call | `build_evaluated_envelope` | `isinstance` | 894 |
| unresolved_call | `_extensions_copy` | `isinstance` | 1755 |
| unresolved_call | `_extensions_copy` | `any` | 1757 |
| unresolved_call | `_extensions_copy` | `isinstance` | 1757 |
| step_limit | `build_evaluated_envelope` | `first 12 steps` | 0 |
| truncated_flow | `build_evaluated_envelope` | `depth limit` | 0 |

## Behavior

This flow starts at `build_evaluated_envelope` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
