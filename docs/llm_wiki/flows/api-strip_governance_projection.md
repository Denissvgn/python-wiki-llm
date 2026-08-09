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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as strip_governance_projection
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as dict
    participant p4 as pop
    participant p5 as append
    participant p6 as replace
    participant p7 as get
    participant p8 as validate_typed_graph
    participant p9 as _object
    participant p10 as require_mapping
    participant p11 as encode
    participant p12 as KnowledgeGraphError
    participant p13 as _only_fields
    participant p14 as require_exact_fields
    participant p15 as str
    participant p16 as set
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: dict
    p0-->>p4: pop
    p0-->>p5: append
    p0-->>p6: replace
    p0-->>p3: dict
    p0-->>p4: pop
    p0-->>p7: get
    p0-->>p1: isinstance
    p0-->>p3: dict
    p0-->>p7: get
    p0-->>p1: isinstance
    p0-->>p1: isinstance
    p0-->>p7: get
    p0-->>p7: get
    p0->>p8: validate_typed_graph
    p8->>p9: _object
    p9->>p10: require_mapping
    p10-->>p1: isinstance
    p10-->>p1: isinstance
    p10-->>p11: encode
    p9->>p12: KnowledgeGraphError
    p9->>p12: KnowledgeGraphError
    p9-->>p3: dict
    p8->>p13: _only_fields
    p13->>p14: require_exact_fields
    p14-->>p1: isinstance
    p14-->>p15: str
    p14-->>p16: set
```

> Call sequence diagram shows 30 of 435 interactions; 405 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. strip_governance_projection"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. dict"]
    s5["5. pop"]
    s6["6. append"]
    s7["7. replace"]
    s8["8. dict"]
    s9["9. pop"]
    s10["10. get"]
    s11["11. isinstance"]
    s12["12. dict"]
    s1 -. "isinstance(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -. "dict(concept.extensions)" .-> s4
    s1 -. "extensions.pop(GOVERNANCE_EXTENSION_KEY, None)" .-> s5
    s1 -. "concepts.append(replace(...))" .-> s6
    s1 -. "replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)" .-> s7
    s1 -. "dict(knowledge.extensions)" .-> s8
    s1 -. "extensions.pop(GOVERNANCE_EXTENSION_KEY, None)" .-> s9
    s1 -. "extensions.get('llm-wiki/typed-graph-v1')" .-> s10
    s1 -. "isinstance(graph, Mapping)" .-> s11
    s1 -. "dict(graph)" .-> s12
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
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `dict` | - | - | - | - |
| `pop` | - | - | - | - |
| `append` | - | - | - | - |
| `replace` | - | - | - | - |
| `dict` | - | - | - | - |
| `pop` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `dict` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| strip_governance_projection | isinstance | 1613 | `isinstance(knowledge, KnowledgeIndex)` |
| strip_governance_projection | TypeError | 1614 | `TypeError('knowledge must be a KnowledgeIndex')` |
| strip_governance_projection | dict | 1617 | `dict(concept.extensions)` |
| strip_governance_projection | pop | 1618 | `extensions.pop(GOVERNANCE_EXTENSION_KEY, None)` |
| strip_governance_projection | append | 1619 | `concepts.append(replace(...))` |
| strip_governance_projection | replace | 1620 | `replace(concept, lifecycle=Lifecycle.UNKNOWN, extensions=extensions)` |
| strip_governance_projection | dict | 1626 | `dict(knowledge.extensions)` |
| strip_governance_projection | pop | 1627 | `extensions.pop(GOVERNANCE_EXTENSION_KEY, None)` |
| strip_governance_projection | get | 1628 | `extensions.get('llm-wiki/typed-graph-v1')` |
| strip_governance_projection | isinstance | 1629 | `isinstance(graph, Mapping)` |
| strip_governance_projection | dict | 1632 | `dict(graph)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `extensions.pop` | `strip_governance_projection` | 1618 |
| mutation | `concepts.append` | `strip_governance_projection` | 1619 |
| mutation | `extensions.pop` | `strip_governance_projection` | 1627 |
| mutation | `snapshot_extensions.pop` | `strip_governance_projection` | 1656 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `strip_governance_projection` | `isinstance` | 1613 |
| unresolved_call | `strip_governance_projection` | `TypeError` | 1614 |
| external_call | `strip_governance_projection` | `replace` | 1620 |
| unresolved_call | `strip_governance_projection` | `extensions.get` | 1628 |
| unresolved_call | `strip_governance_projection` | `isinstance` | 1629 |
| step_limit | `strip_governance_projection` | `first 12 steps` | 0 |
| truncated_flow | `strip_governance_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `strip_governance_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
