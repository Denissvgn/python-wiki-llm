# governance_hash_from_knowledge

**Entry point:** `governance_hash_from_knowledge` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as governance_hash_from_knowledge
    participant p1 as validate_governance_projection
    participant p2 as isinstance
    participant p3 as TypeError
    participant p4 as get
    participant p5 as any
    participant p6 as GovernanceError
    participant p7 as _object
    participant p8 as require_mapping
    participant p9 as encode
    participant p10 as dict
    participant p11 as _exact_fields
    participant p12 as require_exact_fields
    participant p13 as str
    participant p14 as set
    participant p15 as tuple
    participant p16 as sorted
    participant p17 as invalid_error
    participant p18 as error_factory
    p0->>p1: validate_governance_projection
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1-->>p4: get
    p1-->>p4: get
    p1-->>p4: get
    p1-->>p5: any
    p1->>p6: GovernanceError
    p1->>p7: _object
    p7->>p8: require_mapping
    p8-->>p2: isinstance
    p8-->>p2: isinstance
    p8-->>p9: encode
    p7->>p6: GovernanceError
    p7->>p6: GovernanceError
    p7-->>p10: dict
    p1->>p11: _exact_fields
    p11->>p12: require_exact_fields
    p12-->>p2: isinstance
    p12-->>p13: str
    p12-->>p14: set
    p12-->>p14: set
    p12-->>p14: set
    p12-->>p15: tuple
    p12-->>p16: sorted
    p12-->>p15: tuple
    p12-->>p16: sorted
    p12-->>p17: invalid_error
    p12-->>p18: error_factory
    p11->>p6: GovernanceError
```

> Call sequence diagram shows 30 of 1116 interactions; 1086 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. governance_hash_from_knowledge"]
    s2["2. validate_governance_projection"]
    s3["3. isinstance"]
    s4["4. TypeError"]
    s5["5. get"]
    s6["6. get"]
    s7["7. get"]
    s8["8. any"]
    s9["9. GovernanceError"]
    s10["10. _object"]
    s11["11. require_mapping"]
    s12["12. isinstance"]
    s1 -->|"validate_governance_projection(knowledge)"| s2
    s2 -. "isinstance(knowledge, KnowledgeIndex)" .-> s3
    s2 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s4
    s2 -. "knowledge.extensions.get(GOVERNANCE_EXTENSION_KEY)" .-> s5
    s2 -. "knowledge.bundle.snapshot.extensions.get(GOVERNANCE_HASH_EXTENSION_KEY)" .-> s6
    s2 -. "concept.extensions.get(GOVERNANCE_EXTENSION_KEY)" .-> s7
    s2 -. "any(...)" .-> s8
    s2 -->|"GovernanceError('extensions', 'contains an incomplete governance projection', code='governance-projection-mismatch')"| s9
    s2 -->|"_object(raw, 'governance_projection')"| s10
    s10 -->|"require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))"| s11
    s11 -. "isinstance(value, Mapping)" .-> s12
    b0["mutation declared_limits.add"]
    s2 -. "mutation declared_limits.add" .-> b0
    b1["mutation seen_uids.add"]
    s2 -. "mutation seen_uids.add" .-> b1
    b2["mutation successor_pairs.add"]
    s2 -. "mutation successor_pairs.add" .-> b2
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s9 "../modules/knowledge_governance.md"
    click s10 "../modules/knowledge_governance.md"
    click s11 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `governance_hash_from_knowledge` | `knowledge: KnowledgeIndex` | - | - | `None`, `value` |
| `validate_governance_projection` | `knowledge: KnowledgeIndex`, `ledger: GovernanceLedger \| None`, `event_limit: int \| None` | `KnowledgeIndex`, `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_EXTENSION_KEY` | - | `None`, `projection` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `any` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| governance_hash_from_knowledge | validate_governance_projection | 2002 | `validate_governance_projection(knowledge)` |
| validate_governance_projection | isinstance | 1815 | `isinstance(knowledge, KnowledgeIndex)` |
| validate_governance_projection | TypeError | 1816 | `TypeError('knowledge must be a KnowledgeIndex')` |
| validate_governance_projection | get | 1817 | `knowledge.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| validate_governance_projection | get | 1818 | `knowledge.bundle.snapshot.extensions.get(GOVERNANCE_HASH_EXTENSION_KEY)` |
| validate_governance_projection | get | 1822 | `concept.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| validate_governance_projection | any | 1826 | `any(...)` |
| validate_governance_projection | GovernanceError | 1829 | `GovernanceError('extensions', 'contains an incomplete governance projection', code='governance-projection-mismatch')` |
| validate_governance_projection | _object | 1835 | `_object(raw, 'governance_projection')` |
| _object | require_mapping | 3136 | `require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `declared_limits.add` | `validate_governance_projection` | 1920 |
| mutation | `seen_uids.add` | `validate_governance_projection` | 1927 |
| mutation | `successor_pairs.add` | `validate_governance_projection` | 1942 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_governance_projection` | `isinstance` | 1815 |
| unresolved_call | `validate_governance_projection` | `TypeError` | 1816 |
| unresolved_call | `validate_governance_projection` | `knowledge.extensions.get` | 1817 |
| unresolved_call | `validate_governance_projection` | `knowledge.bundle.snapshot.extensions.get` | 1818 |
| unresolved_call | `validate_governance_projection` | `concept.extensions.get` | 1822 |
| unresolved_call | `validate_governance_projection` | `any` | 1826 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| step_limit | `governance_hash_from_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `governance_hash_from_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `governance_hash_from_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
