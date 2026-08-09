# serialize_typed_graph

**Entry point:** `serialize_typed_graph` (`api`)
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
    participant p0 as serialize_typed_graph
    participant p1 as dumps
    participant p2 as validate_typed_graph
    participant p3 as _object
    participant p4 as require_mapping
    participant p5 as isinstance
    participant p6 as encode
    participant p7 as KnowledgeGraphError
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
    p0-->>p1: dumps
    p0->>p2: validate_typed_graph
    p2->>p3: _object
    p3->>p4: require_mapping
    p4-->>p5: isinstance
    p4-->>p5: isinstance
    p4-->>p6: encode
    p3->>p7: KnowledgeGraphError
    p3->>p7: KnowledgeGraphError
    p3-->>p8: dict
    p2->>p9: _only_fields
    p9->>p10: require_exact_fields
    p10-->>p5: isinstance
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
    p9->>p7: KnowledgeGraphError
    p9->>p7: KnowledgeGraphError
    p9->>p7: KnowledgeGraphError
    p2->>p7: KnowledgeGraphError
    p2->>p17: _normalise_input_hashes
    p17->>p3: _object
    p17-->>p12: set
```

> Call sequence diagram shows 30 of 413 interactions; 383 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_typed_graph"]
    s2["2. dumps"]
    s3["3. validate_typed_graph"]
    s4["4. _object"]
    s5["5. require_mapping"]
    s6["6. isinstance"]
    s7["7. isinstance"]
    s8["8. encode"]
    s9["9. KnowledgeGraphError"]
    s10["10. KnowledgeGraphError"]
    s11["11. dict"]
    s12["12. _only_fields"]
    s1 -. "json.dumps(validate_typed_graph(...), ensure_ascii=False, indent=2, sort_keys=True)" .-> s2
    s1 -->|"validate_typed_graph(payload, concept_kinds=concept_kinds)"| s3
    s3 -->|"_object(payload, 'typed_graph')"| s4
    s4 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s5
    s5 -. "isinstance(value, Mapping)" .-> s6
    s5 -. "isinstance(key, str)" .-> s7
    s5 -. "key.encode('utf-8')" .-> s8
    s4 -->|"KnowledgeGraphError(path, 'must be an object')"| s9
    s4 -->|"KnowledgeGraphError(path, 'object keys must be strings')"| s10
    s4 -. "dict(selected)" .-> s11
    s3 -->|"_only_fields(graph, 'typed_graph', {...}, required={...})"| s12
    b0["mutation seen_analyzers.add"]
    s3 -. "mutation seen_analyzers.add" .-> b0
    b1["mutation coverage.append"]
    s3 -. "mutation coverage.append" .-> b1
    b2["mutation seen_keys.add"]
    s3 -. "mutation seen_keys.add" .-> b2
    b3["mutation edges.append"]
    s3 -. "mutation edges.append" .-> b3
    b4["mutation edges.sort"]
    s3 -. "mutation edges.sort" .-> b4
    b5["mutation coverage.sort"]
    s3 -. "mutation coverage.sort" .-> b5
    click s1 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s4 "../modules/knowledge_graph.md"
    click s5 "../modules/validation.md"
    click s9 "../modules/knowledge_graph.md"
    click s10 "../modules/knowledge_graph.md"
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
| `serialize_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None` | - | - | `...` |
| `dumps` | - | - | - | - |
| `validate_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None` | `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION` | - | `{...}` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_only_fields` | `value: Mapping[str, Any]`, `path: str`, `allowed: set[str]`, `required: set[str] \| frozenset[str]` | - | - | `require_shared_exact_fields(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| serialize_typed_graph | dumps | 499 | `json.dumps(validate_typed_graph(...), ensure_ascii=False, indent=2, sort_keys=True)` |
| serialize_typed_graph | validate_typed_graph | 500 | `validate_typed_graph(payload, concept_kinds=concept_kinds)` |
| validate_typed_graph | _object | 407 | `_object(payload, 'typed_graph')` |
| _object | require_mapping | 2282 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2284 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2286 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2288 | `dict(selected)` |
| validate_typed_graph | _only_fields | 408 | `_only_fields(graph, 'typed_graph', {...}, required={...})` |

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
| external_call | `serialize_typed_graph` | `json.dumps` | 499 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `serialize_typed_graph` | `first 12 steps` | 0 |
| truncated_flow | `serialize_typed_graph` | `depth limit` | 0 |

## Behavior

This flow starts at `serialize_typed_graph` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
