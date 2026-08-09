# typed_graph_from_knowledge_extensions

**Entry point:** `typed_graph_from_knowledge_extensions` (`api`)
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
    participant p0 as typed_graph_from_knowledge_extensions
    participant p1 as isinstance
    participant p2 as KnowledgeGraphError
    participant p3 as get
    participant p4 as validate_typed_graph
    participant p5 as _object
    participant p6 as require_mapping
    participant p7 as encode
    participant p8 as dict
    participant p9 as _only_fields
    participant p10 as require_exact_fields
    participant p11 as str
    participant p12 as set
    participant p13 as tuple
    participant p14 as sorted
    participant p15 as invalid_error
    participant p16 as error_factory
    participant p17 as _normalise_input_hashes
    p0-->>p1: isinstance
    p0->>p2: KnowledgeGraphError
    p0-->>p3: get
    p0->>p4: validate_typed_graph
    p4->>p5: _object
    p5->>p6: require_mapping
    p6-->>p1: isinstance
    p6-->>p1: isinstance
    p6-->>p7: encode
    p5->>p2: KnowledgeGraphError
    p5->>p2: KnowledgeGraphError
    p5-->>p8: dict
    p4->>p9: _only_fields
    p9->>p10: require_exact_fields
    p10-->>p1: isinstance
    p10-->>p11: str
    p10-->>p12: set
    p10-->>p12: set
    p10-->>p12: set
    p10-->>p13: tuple
    p10-->>p14: sorted
    p10-->>p13: tuple
    p10-->>p14: sorted
    p10-->>p15: invalid_error
    p10-->>p16: error_factory
    p9->>p2: KnowledgeGraphError
    p9->>p2: KnowledgeGraphError
    p9->>p2: KnowledgeGraphError
    p4->>p2: KnowledgeGraphError
    p4->>p17: _normalise_input_hashes
```

> Call sequence diagram shows 30 of 415 interactions; 385 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. typed_graph_from_knowledge_extensions"]
    s2["2. isinstance"]
    s3["3. KnowledgeGraphError"]
    s4["4. get"]
    s5["5. validate_typed_graph"]
    s6["6. _object"]
    s7["7. require_mapping"]
    s8["8. isinstance"]
    s9["9. isinstance"]
    s10["10. encode"]
    s11["11. KnowledgeGraphError"]
    s12["12. KnowledgeGraphError"]
    s1 -. "isinstance(extensions, Mapping)" .-> s2
    s1 -->|"KnowledgeGraphError('extensions', 'must be an object')"| s3
    s1 -. "extensions.get(TYPED_GRAPH_EXTENSION_KEY)" .-> s4
    s1 -->|"validate_typed_graph(value, concept_kinds=concept_kinds)"| s5
    s5 -->|"_object(payload, 'typed_graph')"| s6
    s6 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s7
    s7 -. "isinstance(value, Mapping)" .-> s8
    s7 -. "isinstance(key, str)" .-> s9
    s7 -. "key.encode('utf-8')" .-> s10
    s6 -->|"KnowledgeGraphError(path, 'must be an object')"| s11
    s6 -->|"KnowledgeGraphError(path, 'object keys must be strings')"| s12
    b0["mutation seen_analyzers.add"]
    s5 -. "mutation seen_analyzers.add" .-> b0
    b1["mutation coverage.append"]
    s5 -. "mutation coverage.append" .-> b1
    b2["mutation seen_keys.add"]
    s5 -. "mutation seen_keys.add" .-> b2
    b3["mutation edges.append"]
    s5 -. "mutation edges.append" .-> b3
    b4["mutation edges.sort"]
    s5 -. "mutation edges.sort" .-> b4
    b5["mutation coverage.sort"]
    s5 -. "mutation coverage.sort" .-> b5
    click s1 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s5 "../modules/knowledge_graph.md"
    click s6 "../modules/knowledge_graph.md"
    click s7 "../modules/validation.md"
    click s11 "../modules/knowledge_graph.md"
    click s12 "../modules/knowledge_graph.md"
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
| `typed_graph_from_knowledge_extensions` | `extensions: Mapping[str, Any]`, `concept_kinds: Mapping[str, str] \| None` | `Mapping`, `TYPED_GRAPH_EXTENSION_KEY` | - | `None`, `validate_typed_graph(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `get` | - | - | - | - |
| `validate_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None` | `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION` | - | `{...}` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| typed_graph_from_knowledge_extensions | isinstance | 516 | `isinstance(extensions, Mapping)` |
| typed_graph_from_knowledge_extensions | KnowledgeGraphError | 517 | `KnowledgeGraphError('extensions', 'must be an object')` |
| typed_graph_from_knowledge_extensions | get | 518 | `extensions.get(TYPED_GRAPH_EXTENSION_KEY)` |
| typed_graph_from_knowledge_extensions | validate_typed_graph | 521 | `validate_typed_graph(value, concept_kinds=concept_kinds)` |
| validate_typed_graph | _object | 407 | `_object(payload, 'typed_graph')` |
| _object | require_mapping | 2282 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2284 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2286 | `KnowledgeGraphError(path, 'object keys must be strings')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen_analyzers.add` | `validate_typed_graph` | 453 |
| mutation | `coverage.append` | `validate_typed_graph` | 454 |
| mutation | `seen_keys.add` | `validate_typed_graph` | 478 |
| mutation | `edges.append` | `validate_typed_graph` | 479 |
| mutation | `edges.sort` | `validate_typed_graph` | 480 |
| mutation | `coverage.sort` | `validate_typed_graph` | 481 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `typed_graph_from_knowledge_extensions` | `isinstance` | 516 |
| unresolved_call | `typed_graph_from_knowledge_extensions` | `extensions.get` | 518 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `typed_graph_from_knowledge_extensions` | `first 12 steps` | 0 |
| truncated_flow | `typed_graph_from_knowledge_extensions` | `depth limit` | 0 |

## Behavior

This flow starts at `typed_graph_from_knowledge_extensions` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
