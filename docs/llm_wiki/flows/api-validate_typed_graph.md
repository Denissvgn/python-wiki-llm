# validate_typed_graph

**Entry point:** `validate_typed_graph` (`api`)
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
    participant p0 as validate_typed_graph
    participant p1 as _object
    participant p2 as require_mapping
    participant p3 as isinstance
    participant p4 as encode
    participant p5 as KnowledgeGraphError
    participant p6 as dict
    participant p7 as _only_fields
    participant p8 as require_exact_fields
    participant p9 as str
    participant p10 as set
    participant p11 as tuple
    participant p12 as sorted
    participant p13 as invalid_error
    participant p14 as error_factory
    participant p15 as _normalise_input_hashes
    participant p16 as _hash
    p0->>p1: _object
    p1->>p2: require_mapping
    p2-->>p3: isinstance
    p2-->>p3: isinstance
    p2-->>p4: encode
    p1->>p5: KnowledgeGraphError
    p1->>p5: KnowledgeGraphError
    p1-->>p6: dict
    p0->>p7: _only_fields
    p7->>p8: require_exact_fields
    p8-->>p3: isinstance
    p8-->>p9: str
    p8-->>p10: set
    p8-->>p10: set
    p8-->>p10: set
    p8-->>p11: tuple
    p8-->>p12: sorted
    p8-->>p11: tuple
    p8-->>p12: sorted
    p8-->>p13: invalid_error
    p8-->>p14: error_factory
    p7->>p5: KnowledgeGraphError
    p7->>p5: KnowledgeGraphError
    p7->>p5: KnowledgeGraphError
    p0->>p5: KnowledgeGraphError
    p0->>p15: _normalise_input_hashes
    p15->>p1: _object
    p15-->>p10: set
    p15->>p7: _only_fields
    p15->>p16: _hash
```

> Call sequence diagram shows 30 of 452 interactions; 422 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_typed_graph"]
    s2["2. _object"]
    s3["3. require_mapping"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s6["6. encode"]
    s7["7. KnowledgeGraphError"]
    s8["8. KnowledgeGraphError"]
    s9["9. dict"]
    s10["10. _only_fields"]
    s11["11. require_exact_fields"]
    s12["12. isinstance"]
    s1 -->|"_object(payload, 'typed_graph')"| s2
    s2 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s3
    s3 -. "isinstance(value, Mapping)" .-> s4
    s3 -. "isinstance(key, str)" .-> s5
    s3 -. "key.encode('utf-8')" .-> s6
    s2 -->|"KnowledgeGraphError(path, 'must be an object')"| s7
    s2 -->|"KnowledgeGraphError(path, 'object keys must be strings')"| s8
    s2 -. "dict(selected)" .-> s9
    s1 -->|"_only_fields(graph, 'typed_graph', {...}, required={...})"| s10
    s10 -->|"require_shared_exact_fields(value, allowed=allowed, required=required, mapping_error=KnowledgeGraphError(...), missing_error=..., unknown_error=..., unknown_fi…"| s11
    s11 -. "isinstance(value, Mapping)" .-> s12
    b0["mutation seen_analyzers.add"]
    s1 -. "mutation seen_analyzers.add" .-> b0
    b1["mutation coverage.append"]
    s1 -. "mutation coverage.append" .-> b1
    b2["mutation seen_keys.add"]
    s1 -. "mutation seen_keys.add" .-> b2
    b3["mutation edges.append"]
    s1 -. "mutation edges.append" .-> b3
    b4["mutation edges.sort"]
    s1 -. "mutation edges.sort" .-> b4
    b5["mutation coverage.sort"]
    s1 -. "mutation coverage.sort" .-> b5
    click s1 "../modules/knowledge_graph.md"
    click s2 "../modules/knowledge_graph.md"
    click s3 "../modules/validation.md"
    click s7 "../modules/knowledge_graph.md"
    click s8 "../modules/knowledge_graph.md"
    click s10 "../modules/knowledge_graph.md"
    click s11 "../modules/validation.md"
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
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_typed_graph | _object | 407 | `_object(payload, 'typed_graph')` |
| _object | require_mapping | 2282 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2284 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2286 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2288 | `dict(selected)` |
| validate_typed_graph | _only_fields | 408 | `_only_fields(graph, 'typed_graph', {...}, required={...})` |
| _only_fields | require_exact_fields | 2305 | `require_shared_exact_fields(value, allowed=allowed, required=required, mapping_error=KnowledgeGraphError(...), missing_error=..., unknown_error=..., unknown_first=True)` |
| require_exact_fields | isinstance | 1205 | `isinstance(value, Mapping)` |

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
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| unresolved_call | `require_exact_fields` | `isinstance` | 1205 |
| step_limit | `validate_typed_graph` | `first 12 steps` | 0 |
| truncated_flow | `validate_typed_graph` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_typed_graph` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
