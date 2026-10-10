# strip_governance_projection

**Entry point:** `strip_governance_projection` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md), and 2 more

**Complete modules touched:**

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as strip_governance_projection
    participant p1 as isinstance (src/llm_wiki_cli/services…rip_governance_projection)
    participant p2 as TypeError
    participant p3 as dict (src/llm_wiki_cli/services…rip_governance_projection)
    participant p4 as extensions.pop
    participant p5 as concepts.append
    participant p6 as replace
    participant p7 as extensions.get
    participant p8 as graph_payload.get
    participant p9 as edge.get
    participant p10 as validate_typed_graph
    participant p11 as snapshot_extensions.pop
    participant p12 as tuple (src/llm_wiki_cli/services…rip_governance_projection)
    participant p13 as _parse_typed_graph
    participant p14 as _object
    participant p15 as _only_fields
    participant p16 as KnowledgeGraphError
    participant p17 as _normalise_input_hashes
    participant p18 as _array
    p0-->>p1: isinstance (src/llm_wiki_cli/services…rip_governance_projection)(knowledge, KnowledgeIndex)
    p0-->>p2: TypeError('knowledge must be a KnowledgeIndex')
    p0-->>p3: dict (src/llm_wiki_cli/services…rip_governance_projection)(concept.extensions)
    p0-->>p4: extensions.pop(GOVERNANCE_EXTENSION_KEY, None)
    p0-->>p5: concepts.append(replace(...))
    p0-->>p6: replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)
    p0-->>p3: dict (src/llm_wiki_cli/services…rip_governance_projection)(knowledge.extensions)
    p0-->>p4: extensions.pop(GOVERNANCE_EXTENSION_KEY, None)
    p0-->>p7: extensions.get('llm-wiki/typed-graph-v1')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…rip_governance_projection)(graph, Mapping)
    p0-->>p3: dict (src/llm_wiki_cli/services…rip_governance_projection)(graph)
    p0-->>p8: graph_payload.get('edges')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…rip_governance_projection)(edges, list)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…rip_governance_projection)(edge, Mapping)
    p0-->>p9: edge.get('kind')
    p0-->>p9: edge.get('origin')
    p0->>p10: validate_typed_graph
    p0-->>p1: isinstance (src/llm_wiki_cli/services…rip_governance_projection)(concept.concept_kind, ConceptKind)
    p0-->>p3: dict (src/llm_wiki_cli/services…rip_governance_projection)(knowledge.bundle.snapshot.extensions)
    p0-->>p11: snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)
    p0-->>p6: replace(knowledge.bundle, snapshot=replace(...))
    p0-->>p6: replace(knowledge.bundle.snapshot, extensions=snapshot_extensions)
    p0-->>p6: replace(knowledge, bundle=bundle, concepts=tuple(...), extensions=extensions)
    p0-->>p12: tuple (src/llm_wiki_cli/services…rip_governance_projection)(concepts)
    p10->>p13: _parse_typed_graph
    p13->>p14: _object
    p13->>p15: _only_fields
    p13->>p16: KnowledgeGraphError
    p13->>p17: _normalise_input_hashes
    p13->>p18: _array
```

> Call sequence diagram shows 30 of 357 interactions; 327 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 87 (72 omitted); unresolved 8 of 58 (50 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 20 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 21 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 21 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 20 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_only_fields` | 28 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 29 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 29 | - | unresolved | 2 |
> Omission summary shows 8 of 105 groups; 97 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. strip_governance_projection"]
    s2["2. isinstance (src/llm_wiki_cli/services…rip_governance_projection)"]
    s3["3. TypeError"]
    s4["4. dict (src/llm_wiki_cli/services…rip_governance_projection)"]
    s5["5. extensions.pop"]
    s6["6. concepts.append"]
    s7["7. replace"]
    s8["8. dict (src/llm_wiki_cli/services…rip_governance_projection)"]
    s9["9. extensions.pop"]
    s10["10. extensions.get"]
    s11["11. isinstance (src/llm_wiki_cli/services…rip_governance_projection)"]
    s12["12. dict (src/llm_wiki_cli/services…rip_governance_projection)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…rip_governance_projection)(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -. "dict (src/llm_wiki_cli/services…rip_governance_projection)(concept.extensions)" .-> s4
    s1 -. "extensions.pop(GOVERNANCE_EXTENSION_KEY, None)" .-> s5
    s1 -. "concepts.append(replace(...))" .-> s6
    s1 -. "replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)" .-> s7
    s1 -. "dict (src/llm_wiki_cli/services…rip_governance_projection)(knowledge.extensions)" .-> s8
    s1 -. "extensions.pop(GOVERNANCE_EXTENSION_KEY, None)" .-> s9
    s1 -. "extensions.get('llm-wiki/typed-graph-v1')" .-> s10
    s1 -. "isinstance (src/llm_wiki_cli/services…rip_governance_projection)(graph, Mapping)" .-> s11
    s1 -. "dict (src/llm_wiki_cli/services…rip_governance_projection)(graph)" .-> s12
    b0["mutation extensions.pop"]
    s1 -. "mutation extensions.pop" .-> b0
    b1["mutation concepts.append"]
    s1 -. "mutation concepts.append" .-> b1
    b2["mutation extensions.pop"]
    s1 -. "mutation extensions.pop" .-> b2
    b3["mutation snapshot_extensions.pop"]
    s1 -. "mutation snapshot_extensions.pop" .-> b3
    click s1 "../modules/knowledge_governance.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `strip_governance_projection` | `knowledge: KnowledgeIndex` | `KnowledgeIndex`, `GOVERNANCE_EXTENSION_KEY`, `Lifecycle`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `Mapping`, `ConceptKind`, `GOVERNANCE_HASH_EXTENSION_KEY` | `graph_payload[...]`, `extensions[...]` | `replace(...)` |
| `isinstance (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `extensions.pop` | - | - | - | - |
| `concepts.append` | - | - | - | - |
| `replace` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `extensions.pop` | - | - | - | - |
| `extensions.get` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…rip_governance_projection)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| strip_governance_projection | isinstance (src/llm_wiki_cli/services…rip_governance_projection) | 1626 | `isinstance(knowledge, KnowledgeIndex)` |
| strip_governance_projection | TypeError | 1627 | `TypeError('knowledge must be a KnowledgeIndex')` |
| strip_governance_projection | dict (src/llm_wiki_cli/services…rip_governance_projection) | 1630 | `dict(concept.extensions)` |
| strip_governance_projection | extensions.pop | 1631 | `extensions.pop(GOVERNANCE_EXTENSION_KEY, None)` |
| strip_governance_projection | concepts.append | 1632 | `concepts.append(replace(...))` |
| strip_governance_projection | replace | 1633 | `replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)` |
| strip_governance_projection | dict (src/llm_wiki_cli/services…rip_governance_projection) | 1639 | `dict(knowledge.extensions)` |
| strip_governance_projection | extensions.pop | 1640 | `extensions.pop(GOVERNANCE_EXTENSION_KEY, None)` |
| strip_governance_projection | extensions.get | 1641 | `extensions.get('llm-wiki/typed-graph-v1')` |
| strip_governance_projection | isinstance (src/llm_wiki_cli/services…rip_governance_projection) | 1642 | `isinstance(graph, Mapping)` |
| strip_governance_projection | dict (src/llm_wiki_cli/services…rip_governance_projection) | 1645 | `dict(graph)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `extensions.pop` | `strip_governance_projection` | 1631 |
| mutation | `concepts.append` | `strip_governance_projection` | 1632 |
| mutation | `extensions.pop` | `strip_governance_projection` | 1640 |
| mutation | `snapshot_extensions.pop` | `strip_governance_projection` | 1669 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `strip_governance_projection` | `isinstance` | 1626 |
| external_call | `strip_governance_projection` | `TypeError` | 1627 |
| external_call | `strip_governance_projection` | `replace` | 1633 |
| unresolved_call | `strip_governance_projection` | `extensions.get` | 1641 |
| external_call | `strip_governance_projection` | `isinstance` | 1642 |
| step_limit | `strip_governance_projection` | `first 12 steps` | 0 |
| truncated_flow | `strip_governance_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `strip_governance_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
