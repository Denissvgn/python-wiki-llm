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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as apply_governance_projection
    participant p1 as _event_limit
    participant p2 as strip_governance_projection
    participant p3 as validate_governance_ledger
    participant p4 as concept_references_from_knowledge
    participant p5 as current.concepts.values
    participant p6 as set (src/llm_wiki_cli/services…ply_governance_projection)
    participant p7 as min (src/llm_wiki_cli/services…ply_governance_projection)
    participant p8 as GovernanceError
    participant p9 as lifecycle_state_by_uid
    participant p10 as defaultdict (src/llm_wiki_cli/services…ply_governance_projection)
    participant p11 as current.aliases.values
    participant p12 as aliases_by_uid[…].append
    participant p13 as current.lifecycle_events.values (src/llm_wiki_cli/services…ply_governance_projection)
    participant p14 as lifecycle_by_uid[…].append
    participant p15 as current.review_events.values
    participant p16 as reviews_by_uid[…].append
    participant p17 as _lifecycle_event_summary
    participant p18 as _ordered_lifecycle_events
    participant p19 as sorted (src/llm_wiki_cli/services…ply_governance_projection)
    participant p20 as evaluate_review_event
    participant p21 as review_items.append
    participant p22 as _review_event_summary
    participant p23 as _bounded_event_payload
    participant p24 as dict (src/llm_wiki_cli/services…ply_governance_projection)
    p0->>p1: _event_limit
    p0->>p2: strip_governance_projection
    p0->>p3: validate_governance_ledger
    p0->>p4: concept_references_from_knowledge
    p0-->>p5: current.concepts.values
    p0-->>p6: set (src/llm_wiki_cli/services…ply_governance_projection)(active_by_locator)
    p0-->>p6: set (src/llm_wiki_cli/services…ply_governance_projection)(allocations_by_locator)
    p0-->>p7: min (src/llm_wiki_cli/services…ply_governance_projection)(missing)
    p0->>p8: GovernanceError
    p0->>p9: lifecycle_state_by_uid
    p0-->>p10: defaultdict (src/llm_wiki_cli/services…ply_governance_projection)(list)
    p0-->>p11: current.aliases.values
    p0-->>p12: aliases_by_uid[…].append(alias)
    p0-->>p10: defaultdict (src/llm_wiki_cli/services…ply_governance_projection)(list)
    p0-->>p13: current.lifecycle_events.values (src/llm_wiki_cli/services…ply_governance_projection)
    p0-->>p14: lifecycle_by_uid[…].append(event)
    p0-->>p10: defaultdict (src/llm_wiki_cli/services…ply_governance_projection)(list)
    p0-->>p15: current.review_events.values
    p0-->>p16: reviews_by_uid[…].append(event)
    p0->>p8: GovernanceError
    p0->>p17: _lifecycle_event_summary
    p0->>p18: _ordered_lifecycle_events
    p0-->>p19: sorted (src/llm_wiki_cli/services…ply_governance_projection)(reviews_by_uid[...], key=...)
    p0->>p20: evaluate_review_event
    p0-->>p21: review_items.append(_review_event_summary(...))
    p0->>p22: _review_event_summary
    p0-->>p19: sorted (src/llm_wiki_cli/services…ply_governance_projection)(aliases_by_uid[...], key=...)
    p0->>p23: _bounded_event_payload
    p0->>p23: _bounded_event_payload
    p0-->>p24: dict (src/llm_wiki_cli/services…ply_governance_projection)(concept.extensions)
```

> Call sequence diagram shows 30 of 1397 interactions; 1367 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 417 (408 omitted); unresolved 8 of 326 (318 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:_event_limit` | 2 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_event_limit` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_governance.py:strip_governance_projection` | 6 | - | external | 15 |
| `src/llm_wiki_cli/services/knowledge_governance.py:strip_governance_projection` | 6 | - | unresolved | 8 |
| `src/llm_wiki_cli/services/knowledge_governance.py:strip_governance_projection` | 6 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:validate_typed_graph` | 23 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_parse_typed_graph` | 24 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 16 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 25 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 296 groups; 288 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. apply_governance_projection"]
    s2["2. _event_limit"]
    s3["3. isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit)"]
    s4["4. isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit)"]
    s5["5. GovernanceError"]
    s6["6. strip_governance_projection"]
    s7["7. isinstance (src/llm_wiki_cli/services…rip_governance_projection)"]
    s8["8. TypeError (src/llm_wiki_cli/services…rip_governance_projection)"]
    s9["9. dict (src/llm_wiki_cli/services…rip_governance_projection)"]
    s10["10. extensions.pop"]
    s11["11. concepts.append (src/llm_wiki_cli/services…rip_governance_projection)"]
    s12["12. replace (src/llm_wiki_cli/services…rip_governance_projection)"]
    s1 -->|"_event_limit(event_limit)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit)(value, bool)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit)(value, int)" .-> s4
    s2 -->|"GovernanceError('event_limit', ...)"| s5
    s1 -->|"strip_governance_projection(knowledge)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…rip_governance_projection)(knowledge, KnowledgeIndex)" .-> s7
    s6 -. "TypeError (src/llm_wiki_cli/services…rip_governance_projection)('knowledge must be a KnowledgeIndex')" .-> s8
    s6 -. "dict (src/llm_wiki_cli/services…rip_governance_projection)(concept.extensions)" .-> s9
    s6 -. "extensions.pop(GOVERNANCE_EXTENSION_KEY, None)" .-> s10
    s6 -. "concepts.append (src/llm_wiki_cli/services…rip_governance_projection)(replace(...))" .-> s11
    s6 -. "replace (src/llm_wiki_cli/services…rip_governance_projection)(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit)` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `strip_governance_projection` | `knowledge: KnowledgeIndex` | `KnowledgeIndex`, `GOVERNANCE_EXTENSION_KEY`, `Lifecycle`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `Mapping`, `ConceptKind`, `GOVERNANCE_HASH_EXTENSION_KEY` | `graph_payload[...]`, `extensions[...]` | `replace(...)` |
| `isinstance (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `extensions.pop` | - | - | - | - |
| `concepts.append (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `replace (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| apply_governance_projection | _event_limit | 1693 | `_event_limit(event_limit)` |
| _event_limit | isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit) | 2558 | `isinstance(value, bool)` |
| _event_limit | isinstance (src/llm_wiki_cli/services…overnance.py:_event_limit) | 2559 | `isinstance(value, int)` |
| _event_limit | GovernanceError | 2562 | `GovernanceError('event_limit', ...)` |
| apply_governance_projection | strip_governance_projection | 1694 | `strip_governance_projection(knowledge)` |
| strip_governance_projection | isinstance (src/llm_wiki_cli/services…rip_governance_projection) | 1626 | `isinstance(knowledge, KnowledgeIndex)` |
| strip_governance_projection | TypeError (src/llm_wiki_cli/services…rip_governance_projection) | 1627 | `TypeError('knowledge must be a KnowledgeIndex')` |
| strip_governance_projection | dict (src/llm_wiki_cli/services…rip_governance_projection) | 1630 | `dict(concept.extensions)` |
| strip_governance_projection | extensions.pop | 1631 | `extensions.pop(GOVERNANCE_EXTENSION_KEY, None)` |
| strip_governance_projection | concepts.append (src/llm_wiki_cli/services…rip_governance_projection) | 1632 | `concepts.append(replace(...))` |
| strip_governance_projection | replace (src/llm_wiki_cli/services…rip_governance_projection) | 1633 | `replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `review_items.append` | `apply_governance_projection` | 1748 |
| mutation | `projected_concepts.append` | `apply_governance_projection` | 1773 |
| mutation | `extensions.pop` | `strip_governance_projection` | 1631 |
| mutation | `concepts.append` | `strip_governance_projection` | 1632 |
| mutation | `extensions.pop` | `strip_governance_projection` | 1640 |
| mutation | `snapshot_extensions.pop` | `strip_governance_projection` | 1669 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_event_limit` | `isinstance` | 2558 |
| external_call | `_event_limit` | `isinstance` | 2559 |
| external_call | `strip_governance_projection` | `isinstance` | 1626 |
| external_call | `strip_governance_projection` | `TypeError` | 1627 |
| external_call | `strip_governance_projection` | `replace` | 1633 |
| step_limit | `apply_governance_projection` | `first 12 steps` | 0 |
| truncated_flow | `apply_governance_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `apply_governance_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
