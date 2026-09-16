# validate_typed_graph_slice

**Entry point:** `validate_typed_graph_slice` (`api`)
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
    participant p0 as validate_typed_graph_slice
    participant p1 as _parse_typed_graph
    participant p2 as _object
    participant p3 as require_mapping
    participant p4 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p5 as key.encode
    participant p6 as KnowledgeGraphError
    participant p7 as dict
    participant p8 as _only_fields
    participant p9 as require_exact_fields
    participant p10 as isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p11 as str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p12 as set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p13 as tuple
    participant p14 as sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p15 as invalid_error
    participant p16 as error_factory
    participant p17 as _normalise_input_hashes
    participant p18 as set (src/llm_wiki_cli/services…y:_normalise_input_hashes)
    p0->>p1: _parse_typed_graph
    p1->>p2: _object
    p2->>p3: require_mapping
    p3-->>p4: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p3-->>p4: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p3-->>p5: key.encode
    p2->>p6: KnowledgeGraphError
    p2->>p6: KnowledgeGraphError
    p2-->>p7: dict
    p1->>p8: _only_fields
    p8->>p9: require_exact_fields
    p9-->>p10: isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p11: str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p12: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p12: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p12: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p13: tuple
    p9-->>p14: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p13: tuple
    p9-->>p14: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p9-->>p15: invalid_error
    p9-->>p16: error_factory
    p8->>p6: KnowledgeGraphError
    p8->>p6: KnowledgeGraphError
    p8->>p6: KnowledgeGraphError
    p1->>p6: KnowledgeGraphError
    p1->>p17: _normalise_input_hashes
    p17->>p2: _object
    p17-->>p18: set (src/llm_wiki_cli/services…y:_normalise_input_hashes)
    p17->>p8: _only_fields
```

> Call sequence diagram shows 30 of 413 interactions; 383 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_typed_graph_slice"]
    s2["2. _parse_typed_graph"]
    s3["3. _object"]
    s4["4. require_mapping"]
    s5["5. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s6["6. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s7["7. key.encode"]
    s8["8. KnowledgeGraphError"]
    s9["9. KnowledgeGraphError"]
    s10["10. dict"]
    s11["11. _only_fields"]
    s12["12. require_exact_fields"]
    s1 -->|"_parse_typed_graph(payload, concept_kinds=concept_kinds, complete=False)"| s2
    s2 -->|"_object(payload, 'typed_graph')"| s3
    s3 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s6
    s4 -. "key.encode('utf-8')" .-> s7
    s3 -->|"KnowledgeGraphError(path, 'must be an object')"| s8
    s3 -->|"KnowledgeGraphError(path, 'object keys must be strings')"| s9
    s3 -. "dict(selected)" .-> s10
    s2 -->|"_only_fields(graph, 'typed_graph', {...}, required={...})"| s11
    s11 -->|"require_exact_fields(…)"| s12
    b0["mutation seen_analyzers.add"]
    s2 -. "mutation seen_analyzers.add" .-> b0
    b1["mutation coverage.append"]
    s2 -. "mutation coverage.append" .-> b1
    b2["mutation seen_keys.add"]
    s2 -. "mutation seen_keys.add" .-> b2
    b3["mutation edges.append"]
    s2 -. "mutation edges.append" .-> b3
    b4["mutation edges.sort"]
    s2 -. "mutation edges.sort" .-> b4
    b5["mutation coverage.sort"]
    s2 -. "mutation coverage.sort" .-> b5
    click s1 "../modules/knowledge_graph.md"
    click s2 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s4 "../modules/validation.md"
    click s8 "../modules/knowledge_graph.md"
    click s9 "../modules/knowledge_graph.md"
    click s11 "../modules/knowledge_graph.md"
    click s12 "../modules/validation.md"
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
| `validate_typed_graph_slice` | `payload: object`, `concept_kinds: Mapping[str, str] \| None` | - | - | `_parse_typed_graph(...)` |
| `_parse_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None`, `complete: bool` | `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION` | - | `{...}` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_only_fields` | `value: Mapping[str, Any]`, `path: str`, `allowed: set[str]`, `required: set[str] \| frozenset[str]` | - | - | `require_shared_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_typed_graph_slice | _parse_typed_graph | 414 | `_parse_typed_graph(payload, concept_kinds=concept_kinds, complete=False)` |
| _parse_typed_graph | _object | 421 | `_object(payload, 'typed_graph')` |
| _object | require_mapping | 2302 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 731 | `isinstance(key, str)` |
| require_mapping | key.encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2304 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2306 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2308 | `dict(selected)` |
| _parse_typed_graph | _only_fields | 422 | `_only_fields(graph, 'typed_graph', {...}, required={...})` |
| _only_fields | require_exact_fields | 2325 | `require_shared_exact_fields(value, allowed=allowed, required=required, mapping_error=KnowledgeGraphError(...), missing_error=..., unknown_error=..., unknown_first=True)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen_analyzers.add` | `_parse_typed_graph` | 467 |
| mutation | `coverage.append` | `_parse_typed_graph` | 468 |
| mutation | `seen_keys.add` | `_parse_typed_graph` | 492 |
| mutation | `edges.append` | `_parse_typed_graph` | 493 |
| mutation | `edges.sort` | `_parse_typed_graph` | 494 |
| mutation | `coverage.sort` | `_parse_typed_graph` | 495 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 727 |
| external_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `validate_typed_graph_slice` | `first 12 steps` | 0 |
| truncated_flow | `validate_typed_graph_slice` | `depth limit` | 0 |

## Behavior

Validates the graph header, consumed edge shapes and their input-basis bindings. Selected observations may not exceed declared analyzer totals, but unconsumed observations are not checked. Full graph validation keeps its exact-total requirement; a slice never establishes whole-graph completeness.
