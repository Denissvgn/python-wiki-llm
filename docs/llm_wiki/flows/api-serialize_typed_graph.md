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
    participant p1 as json.dumps
    participant p2 as validate_typed_graph
    participant p3 as _parse_typed_graph
    participant p4 as _object
    participant p5 as require_mapping
    participant p6 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p7 as key.encode
    participant p8 as KnowledgeGraphError
    participant p9 as dict
    participant p10 as _only_fields
    participant p11 as require_exact_fields
    participant p12 as isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p13 as str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p14 as set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p15 as tuple
    participant p16 as sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p17 as invalid_error
    participant p18 as error_factory
    participant p19 as _normalise_input_hashes
    p0-->>p1: json.dumps
    p0->>p2: validate_typed_graph
    p2->>p3: _parse_typed_graph
    p3->>p4: _object
    p4->>p5: require_mapping
    p5-->>p6: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p5-->>p6: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p5-->>p7: key.encode
    p4->>p8: KnowledgeGraphError
    p4->>p8: KnowledgeGraphError
    p4-->>p9: dict
    p3->>p10: _only_fields
    p10->>p11: require_exact_fields
    p11-->>p12: isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p13: str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p14: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p14: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p14: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p15: tuple
    p11-->>p16: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p15: tuple
    p11-->>p16: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p11-->>p17: invalid_error
    p11-->>p18: error_factory
    p10->>p8: KnowledgeGraphError
    p10->>p8: KnowledgeGraphError
    p10->>p8: KnowledgeGraphError
    p3->>p8: KnowledgeGraphError
    p3->>p19: _normalise_input_hashes
    p19->>p4: _object
```

> Call sequence diagram shows 30 of 335 interactions; 305 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_typed_graph"]
    s2["2. json.dumps"]
    s3["3. validate_typed_graph"]
    s4["4. _parse_typed_graph"]
    s5["5. _object"]
    s6["6. require_mapping"]
    s7["7. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s8["8. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s9["9. key.encode"]
    s10["10. KnowledgeGraphError"]
    s11["11. KnowledgeGraphError"]
    s12["12. dict"]
    s1 -. "json.dumps(validate_typed_graph(...), ensure_ascii=False, indent=2, sort_keys=True)" .-> s2
    s1 -->|"validate_typed_graph(payload, concept_kinds=concept_kinds)"| s3
    s3 -->|"_parse_typed_graph(payload, concept_kinds=concept_kinds, complete=True)"| s4
    s4 -->|"_object(payload, 'typed_graph')"| s5
    s5 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s7
    s6 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s8
    s6 -. "key.encode('utf-8')" .-> s9
    s5 -->|"KnowledgeGraphError(path, 'must be an object')"| s10
    s5 -->|"KnowledgeGraphError(path, 'object keys must be strings')"| s11
    s5 -. "dict(selected)" .-> s12
    b0["mutation seen_analyzers.add"]
    s4 -. "mutation seen_analyzers.add" .-> b0
    b1["mutation coverage.append"]
    s4 -. "mutation coverage.append" .-> b1
    b2["mutation seen_keys.add"]
    s4 -. "mutation seen_keys.add" .-> b2
    b3["mutation edges.append"]
    s4 -. "mutation edges.append" .-> b3
    b4["mutation edges.sort"]
    s4 -. "mutation edges.sort" .-> b4
    b5["mutation coverage.sort"]
    s4 -. "mutation coverage.sort" .-> b5
    click s1 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s4 "../modules/knowledge_graph.md"
    click s5 "../modules/knowledge_graph.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/knowledge_graph.md"
    click s11 "../modules/knowledge_graph.md"
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
| `json.dumps` | - | - | - | - |
| `validate_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None` | - | - | `_parse_typed_graph(...)` |
| `_parse_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None`, `complete: bool` | `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION` | - | `{...}` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `dict` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| serialize_typed_graph | json.dumps | 513 | `json.dumps(validate_typed_graph(...), ensure_ascii=False, indent=2, sort_keys=True)` |
| serialize_typed_graph | validate_typed_graph | 514 | `validate_typed_graph(payload, concept_kinds=concept_kinds)` |
| validate_typed_graph | _parse_typed_graph | 407 | `_parse_typed_graph(payload, concept_kinds=concept_kinds, complete=True)` |
| _parse_typed_graph | _object | 421 | `_object(payload, 'typed_graph')` |
| _object | require_mapping | 2302 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2304 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2306 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2308 | `dict(selected)` |

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
| external_call | `serialize_typed_graph` | `json.dumps` | 513 |
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `serialize_typed_graph` | `first 12 steps` | 0 |
| truncated_flow | `serialize_typed_graph` | `depth limit` | 0 |

## Behavior

This flow starts at `serialize_typed_graph` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
