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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_typed_graph
    participant p1 as validate_typed_graph
    participant p2 as _parse_typed_graph
    participant p3 as _object
    participant p4 as _only_fields
    participant p5 as _normalise_input_hashes
    participant p6 as _array
    participant p7 as _name
    participant p8 as _normalise_coverage
    participant p9 as _locator
    participant p10 as _normalise_edge
    participant p11 as _validate_graph_bindings
    participant p12 as require_nonempty_text
    participant p13 as validate_exact_page_coordinate
    participant p14 as _nonnegative_int
    participant p15 as _hash
    participant p16 as _relationship_kind
    participant p17 as _normalise_endpoint
    participant p18 as _aggregate_input_hash
    participant p19 as _positive_int
    participant p20 as _limitation
    participant p21 as _validate_resolution_target
    participant p22 as _normalise_evidence
    participant p23 as _validate_endpoint_concept_references
    participant p24 as relationship_edge_key
    participant p25 as _validate_core_direction
    participant p26 as require_sha256
    participant p27 as require_nonnegative_int
    participant p28 as _open_name
    participant p29 as json.dumps
    participant p30 as seen_analyzers.add
    p0->>p1: validate_typed_graph
    p1->>p2: _parse_typed_graph
    p2->>p3: _object
    p2->>p4: _only_fields
    p2->>p5: _normalise_input_hashes
    p2->>p6: _array
    p2->>p7: _name
    p2->>p8: _normalise_coverage
    p2->>p9: _locator
    p2->>p10: _normalise_edge
    p2->>p11: _validate_graph_bindings
    p7->>p12: require_nonempty_text
    p9->>p13: validate_exact_page_coordinate
    p8->>p14: _nonnegative_int
    p5->>p15: _hash
    p10->>p16: _relationship_kind
    p10->>p17: _normalise_endpoint
    p5->>p18: _aggregate_input_hash
    p8->>p19: _positive_int
    p8->>p20: _limitation
    p10->>p21: _validate_resolution_target
    p10->>p22: _normalise_evidence
    p10->>p23: _validate_endpoint_concept_references
    p10->>p24: relationship_edge_key
    p10->>p25: _validate_core_direction
    p15->>p26: require_sha256
    p14->>p27: require_nonnegative_int
    p16->>p28: _open_name
    p0-->>p29: json.dumps(validate_typed_graph(...), ensure_ascii=False, indent=2, sort_keys=True)
    p2-->>p30: seen_analyzers.add(analyzer)
```

> Call sequence diagram shows 30 of 335 interactions; 305 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 73 (72 omitted); unresolved 1 of 50 (49 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 5 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 5 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_only_fields` | 13 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 14 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 14 | - | unresolved | 2 |
> Omission summary shows 8 of 101 groups; 93 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| _object | require_mapping | 2309 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2311 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2313 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2315 | `dict(selected)` |

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
