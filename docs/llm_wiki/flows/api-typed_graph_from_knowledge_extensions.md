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
    participant p1 as isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)
    participant p2 as KnowledgeGraphError
    participant p3 as extensions.get
    participant p4 as validate_typed_graph
    participant p5 as _parse_typed_graph
    participant p6 as _object
    participant p7 as require_mapping
    participant p8 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p9 as key.encode
    participant p10 as dict
    participant p11 as _only_fields
    participant p12 as require_exact_fields
    participant p13 as isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p14 as str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p15 as set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p16 as tuple
    participant p17 as sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    participant p18 as invalid_error
    participant p19 as error_factory
    p0-->>p1: isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)
    p0->>p2: KnowledgeGraphError
    p0-->>p3: extensions.get
    p0->>p4: validate_typed_graph
    p4->>p5: _parse_typed_graph
    p5->>p6: _object
    p6->>p7: require_mapping
    p7-->>p8: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p7-->>p8: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p7-->>p9: key.encode
    p6->>p2: KnowledgeGraphError
    p6->>p2: KnowledgeGraphError
    p6-->>p10: dict
    p5->>p11: _only_fields
    p11->>p12: require_exact_fields
    p12-->>p13: isinstance (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p14: str (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p15: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p15: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p15: set (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p16: tuple
    p12-->>p17: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p16: tuple
    p12-->>p17: sorted (src/llm_wiki_cli/services…n.py:require_exact_fields)
    p12-->>p18: invalid_error
    p12-->>p19: error_factory
    p11->>p2: KnowledgeGraphError
    p11->>p2: KnowledgeGraphError
    p11->>p2: KnowledgeGraphError
    p5->>p2: KnowledgeGraphError
```

> Call sequence diagram shows 30 of 338 interactions; 308 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. typed_graph_from_knowledge_extensions"]
    s2["2. isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)"]
    s3["3. KnowledgeGraphError"]
    s4["4. extensions.get"]
    s5["5. validate_typed_graph"]
    s6["6. _parse_typed_graph"]
    s7["7. _object"]
    s8["8. require_mapping"]
    s9["9. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s10["10. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s11["11. key.encode"]
    s12["12. KnowledgeGraphError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)(extensions, Mapping)" .-> s2
    s1 -->|"KnowledgeGraphError('extensions', 'must be an object')"| s3
    s1 -. "extensions.get(TYPED_GRAPH_EXTENSION_KEY)" .-> s4
    s1 -->|"validate_typed_graph(value, concept_kinds=concept_kinds)"| s5
    s5 -->|"_parse_typed_graph(payload, concept_kinds=concept_kinds, complete=True)"| s6
    s6 -->|"_object(payload, 'typed_graph')"| s7
    s7 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s9
    s8 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s10
    s8 -. "key.encode('utf-8')" .-> s11
    s7 -->|"KnowledgeGraphError(path, 'must be an object')"| s12
    b0["mutation seen_analyzers.add"]
    s6 -. "mutation seen_analyzers.add" .-> b0
    b1["mutation coverage.append"]
    s6 -. "mutation coverage.append" .-> b1
    b2["mutation seen_keys.add"]
    s6 -. "mutation seen_keys.add" .-> b2
    b3["mutation edges.append"]
    s6 -. "mutation edges.append" .-> b3
    b4["mutation edges.sort"]
    s6 -. "mutation edges.sort" .-> b4
    b5["mutation coverage.sort"]
    s6 -. "mutation coverage.sort" .-> b5
    click s1 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s5 "../modules/knowledge_graph.md"
    click s6 "../modules/knowledge_graph.md"
    click s7 "../modules/knowledge_graph.md"
    click s8 "../modules/validation.md"
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
| `isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `extensions.get` | - | - | - | - |
| `validate_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None` | - | - | `_parse_typed_graph(...)` |
| `_parse_typed_graph` | `payload: object`, `concept_kinds: Mapping[str, str] \| None`, `complete: bool` | `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION`, `TYPED_GRAPH_SCHEMA_VERSION` | - | `{...}` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| typed_graph_from_knowledge_extensions | isinstance (src/llm_wiki_cli/services…from_knowledge_extensions) | 530 | `isinstance(extensions, Mapping)` |
| typed_graph_from_knowledge_extensions | KnowledgeGraphError | 531 | `KnowledgeGraphError('extensions', 'must be an object')` |
| typed_graph_from_knowledge_extensions | extensions.get | 532 | `extensions.get(TYPED_GRAPH_EXTENSION_KEY)` |
| typed_graph_from_knowledge_extensions | validate_typed_graph | 535 | `validate_typed_graph(value, concept_kinds=concept_kinds)` |
| validate_typed_graph | _parse_typed_graph | 407 | `_parse_typed_graph(payload, concept_kinds=concept_kinds, complete=True)` |
| _parse_typed_graph | _object | 421 | `_object(payload, 'typed_graph')` |
| _object | require_mapping | 2302 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 731 | `isinstance(key, str)` |
| require_mapping | key.encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2304 | `KnowledgeGraphError(path, 'must be an object')` |

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
| external_call | `typed_graph_from_knowledge_extensions` | `isinstance` | 530 |
| unresolved_call | `typed_graph_from_knowledge_extensions` | `extensions.get` | 532 |
| external_call | `require_mapping` | `isinstance` | 727 |
| external_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `typed_graph_from_knowledge_extensions` | `first 12 steps` | 0 |
| truncated_flow | `typed_graph_from_knowledge_extensions` | `depth limit` | 0 |

## Behavior

This flow starts at `typed_graph_from_knowledge_extensions` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
