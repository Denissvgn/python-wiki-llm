# apply_governance_projection

**Entry point:** `apply_governance_projection` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 5 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as apply_governance_projection
    participant p1 as _event_limit
    participant p2 as isinstance
    participant p3 as GovernanceError
    participant p4 as strip_governance_projection
    participant p5 as TypeError
    participant p6 as dict
    participant p7 as pop
    participant p8 as append
    participant p9 as replace
    participant p10 as get
    participant p11 as validate_typed_graph
    participant p12 as _object
    participant p13 as require_mapping
    participant p14 as encode
    participant p15 as KnowledgeGraphError
    p0->>p1: _event_limit
    p1-->>p2: isinstance
    p1-->>p2: isinstance
    p1->>p3: GovernanceError
    p0->>p4: strip_governance_projection
    p4-->>p2: isinstance
    p4-->>p5: TypeError
    p4-->>p6: dict
    p4-->>p7: pop
    p4-->>p8: append
    p4-->>p9: replace
    p4-->>p6: dict
    p4-->>p7: pop
    p4-->>p10: get
    p4-->>p2: isinstance
    p4-->>p6: dict
    p4-->>p10: get
    p4-->>p2: isinstance
    p4-->>p2: isinstance
    p4-->>p10: get
    p4-->>p10: get
    p4->>p11: validate_typed_graph
    p11->>p12: _object
    p12->>p13: require_mapping
    p13-->>p2: isinstance
    p13-->>p2: isinstance
    p13-->>p14: encode
    p12->>p15: KnowledgeGraphError
    p12->>p15: KnowledgeGraphError
    p12-->>p6: dict
```

> Call sequence diagram shows 30 of 1394 interactions; 1364 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. apply_governance_projection"]
    s2["2. _event_limit"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. GovernanceError"]
    s6["6. strip_governance_projection"]
    s7["7. isinstance"]
    s8["8. TypeError"]
    s9["9. dict"]
    s10["10. pop"]
    s11["11. append"]
    s12["12. replace"]
    s1 -->|"_event_limit(event_limit)"| s2
    s2 -. "isinstance(value, bool)" .-> s3
    s2 -. "isinstance(value, int)" .-> s4
    s2 -->|"GovernanceError('event_limit', ...)"| s5
    s1 -->|"strip_governance_projection(knowledge)"| s6
    s6 -. "isinstance(knowledge, KnowledgeIndex)" .-> s7
    s6 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s8
    s6 -. "dict(concept.extensions)" .-> s9
    s6 -. "extensions.pop(GOVERNANCE_EXTENSION_KEY, None)" .-> s10
    s6 -. "concepts.append(replace(...))" .-> s11
    s6 -. "replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)" .-> s12
    b0["mutation review_items.append"]
    s1 -. "mutation review_items.append" .-> b0
    b1["mutation projected_concepts.append"]
    s1 -. "mutation projected_concepts.append" .-> b1
    b2["mutation extensions.pop"]
    s6 -. "mutation extensions.pop" .-> b2
    b3["mutation concepts.append"]
    s6 -. "mutation concepts.append" .-> b3
    b4["mutation extensions.pop"]
    s6 -. "mutation extensions.pop" .-> b4
    b5["mutation snapshot_extensions.pop"]
    s6 -. "mutation snapshot_extensions.pop" .-> b5
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `apply_governance_projection` | `knowledge: KnowledgeIndex`, `ledger: GovernanceLedger`, `event_limit: int` | `GOVERNANCE_SCHEMA_VERSION`, `INVENTORY_HASH_EXTENSION` | `summary[...]`, `concept_summaries[...]`, `concept_extensions[...]`, `extensions[...]`, `snapshot_extensions[...]` | `projected` |
| `_event_limit` | `value: object` | `MAX_EVENT_LIMIT`, `MAX_EVENT_LIMIT` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `strip_governance_projection` | `knowledge: KnowledgeIndex` | `KnowledgeIndex`, `GOVERNANCE_EXTENSION_KEY`, `Lifecycle`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `Mapping`, `ConceptKind`, `GOVERNANCE_HASH_EXTENSION_KEY` | `graph_payload[...]`, `extensions[...]` | `replace(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `dict` | - | - | - | - |
| `pop` | - | - | - | - |
| `append` | - | - | - | - |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| apply_governance_projection | _event_limit | 1680 | `_event_limit(event_limit)` |
| _event_limit | isinstance | 2545 | `isinstance(value, bool)` |
| _event_limit | isinstance | 2546 | `isinstance(value, int)` |
| _event_limit | GovernanceError | 2549 | `GovernanceError('event_limit', ...)` |
| apply_governance_projection | strip_governance_projection | 1681 | `strip_governance_projection(knowledge)` |
| strip_governance_projection | isinstance | 1613 | `isinstance(knowledge, KnowledgeIndex)` |
| strip_governance_projection | TypeError | 1614 | `TypeError('knowledge must be a KnowledgeIndex')` |
| strip_governance_projection | dict | 1617 | `dict(concept.extensions)` |
| strip_governance_projection | pop | 1618 | `extensions.pop(GOVERNANCE_EXTENSION_KEY, None)` |
| strip_governance_projection | append | 1619 | `concepts.append(replace(...))` |
| strip_governance_projection | replace | 1620 | `replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `review_items.append` | `apply_governance_projection` | 1735 |
| mutation | `projected_concepts.append` | `apply_governance_projection` | 1760 |
| mutation | `extensions.pop` | `strip_governance_projection` | 1618 |
| mutation | `concepts.append` | `strip_governance_projection` | 1619 |
| mutation | `extensions.pop` | `strip_governance_projection` | 1627 |
| mutation | `snapshot_extensions.pop` | `strip_governance_projection` | 1656 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_event_limit` | `isinstance` | 2545 |
| unresolved_call | `_event_limit` | `isinstance` | 2546 |
| unresolved_call | `strip_governance_projection` | `isinstance` | 1613 |
| unresolved_call | `strip_governance_projection` | `TypeError` | 1614 |
| external_call | `strip_governance_projection` | `replace` | 1620 |
| step_limit | `apply_governance_projection` | `first 12 steps` | 0 |
| truncated_flow | `apply_governance_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `apply_governance_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
