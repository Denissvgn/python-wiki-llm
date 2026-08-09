# materialize_typed_graph

**Entry point:** `materialize_typed_graph` (`api`)
**Source:** [knowledge_graph](../modules/knowledge_graph.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md), and 1 more

**Complete modules touched:**

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as materialize_typed_graph
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as KnowledgeGraphError
    participant p4 as _normalise_graph_concepts
    participant p5 as set
    participant p6 as enumerate
    participant p7 as _locator
    participant p8 as _name
    participant p9 as require_nonempty_text
    participant p10 as strip
    participant p11 as any
    participant p12 as ord
    participant p13 as validate_exact_page_coordinate
    participant p14 as WikiSurfaceError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p1: isinstance
    p0->>p3: KnowledgeGraphError
    p0->>p4: _normalise_graph_concepts
    p4-->>p1: isinstance
    p4-->>p1: isinstance
    p4->>p3: KnowledgeGraphError
    p4-->>p5: set
    p4-->>p6: enumerate
    p4-->>p1: isinstance
    p4->>p3: KnowledgeGraphError
    p4->>p7: _locator
    p7->>p8: _name
    p8->>p9: require_nonempty_text
    p9-->>p1: isinstance
    p9-->>p10: strip
    p9-->>p11: any
    p9-->>p12: ord
    p9-->>p12: ord
    p8->>p3: KnowledgeGraphError
    p7->>p13: validate_exact_page_coordinate
    p13-->>p1: isinstance
    p13-->>p10: strip
    p13->>p14: WikiSurfaceError
    p13-->>p10: strip
    p13-->>p11: any
    p13-->>p12: ord
    p13-->>p12: ord
```

> Call sequence diagram shows 30 of 862 interactions; 832 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. materialize_typed_graph"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s6["6. KnowledgeGraphError"]
    s7["7. _normalise_graph_concepts"]
    s8["8. isinstance"]
    s9["9. isinstance"]
    s10["10. KnowledgeGraphError"]
    s11["11. set"]
    s12["12. enumerate"]
    s1 -. "isinstance(inputs, KnowledgeGraphInputs)" .-> s2
    s1 -. "TypeError('inputs must be a KnowledgeGraphInputs')" .-> s3
    s1 -. "isinstance(inputs.evidence_limit, bool)" .-> s4
    s1 -. "isinstance(inputs.evidence_limit, int)" .-> s5
    s1 -->|"KnowledgeGraphError('evidence_limit', ...)"| s6
    s1 -->|"_normalise_graph_concepts(inputs.concepts)"| s7
    s7 -. "isinstance(values, (...))" .-> s8
    s7 -. "isinstance(values, Sequence)" .-> s9
    s7 -->|"KnowledgeGraphError('concepts', 'must be a sequence')"| s10
    s7 -. "set(data not statically known)" .-> s11
    s7 -. "enumerate(values)" .-> s12
    b0["mutation seen.add"]
    s7 -. "mutation seen.add" .-> b0
    b1["mutation concepts.append"]
    s7 -. "mutation concepts.append" .-> b1
    b2["mutation concepts.sort"]
    s7 -. "mutation concepts.sort" .-> b2
    click s1 "../modules/knowledge_graph.md"
    click s6 "../modules/knowledge_graph.md"
    click s7 "../modules/knowledge_graph.md"
    click s10 "../modules/knowledge_graph.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `materialize_typed_graph` | `inputs: KnowledgeGraphInputs` | `KnowledgeGraphInputs`, `MAX_EVIDENCE_LIMIT`, `MAX_EVIDENCE_LIMIT`, `TYPED_GRAPH_SCHEMA_VERSION` | `input_hashes[...]` | `validate_typed_graph(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `_normalise_graph_concepts` | `values: Sequence[GraphConcept]` | `Mapping`, `Sequence`, `GraphConcept` | - | `tuple(...)` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `set` | - | - | - | - |
| `enumerate` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| materialize_typed_graph | isinstance | 315 | `isinstance(inputs, KnowledgeGraphInputs)` |
| materialize_typed_graph | TypeError | 316 | `TypeError('inputs must be a KnowledgeGraphInputs')` |
| materialize_typed_graph | isinstance | 318 | `isinstance(inputs.evidence_limit, bool)` |
| materialize_typed_graph | isinstance | 319 | `isinstance(inputs.evidence_limit, int)` |
| materialize_typed_graph | KnowledgeGraphError | 322 | `KnowledgeGraphError('evidence_limit', ...)` |
| materialize_typed_graph | _normalise_graph_concepts | 326 | `_normalise_graph_concepts(inputs.concepts)` |
| _normalise_graph_concepts | isinstance | 1222 | `isinstance(values, (...))` |
| _normalise_graph_concepts | isinstance | 1222 | `isinstance(values, Sequence)` |
| _normalise_graph_concepts | KnowledgeGraphError | 1223 | `KnowledgeGraphError('concepts', 'must be a sequence')` |
| _normalise_graph_concepts | set | 1225 | `set(data not statically known)` |
| _normalise_graph_concepts | enumerate | 1226 | `enumerate(values)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `_normalise_graph_concepts` | 1233 |
| mutation | `concepts.append` | `_normalise_graph_concepts` | 1253 |
| mutation | `concepts.sort` | `_normalise_graph_concepts` | 1263 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `materialize_typed_graph` | `isinstance` | 315 |
| unresolved_call | `materialize_typed_graph` | `TypeError` | 316 |
| unresolved_call | `materialize_typed_graph` | `isinstance` | 318 |
| unresolved_call | `materialize_typed_graph` | `isinstance` | 319 |
| unresolved_call | `_normalise_graph_concepts` | `isinstance` | 1222 |
| unresolved_call | `_normalise_graph_concepts` | `enumerate` | 1226 |
| step_limit | `materialize_typed_graph` | `first 12 steps` | 0 |
| truncated_flow | `materialize_typed_graph` | `depth limit` | 0 |

## Behavior

This flow starts at `materialize_typed_graph` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
