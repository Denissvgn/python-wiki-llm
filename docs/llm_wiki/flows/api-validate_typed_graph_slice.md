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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_typed_graph_slice
    participant p1 as _parse_typed_graph
    participant p2 as _object
    participant p3 as _only_fields
    participant p4 as _normalise_input_hashes
    participant p5 as _array
    participant p6 as _name
    participant p7 as _normalise_coverage
    participant p8 as _locator
    participant p9 as _normalise_edge
    participant p10 as _validate_graph_bindings
    participant p11 as validate_exact_page_coordinate
    participant p12 as _nonnegative_int
    participant p13 as _hash
    participant p14 as _relationship_kind
    participant p15 as _normalise_endpoint
    participant p16 as _aggregate_input_hash
    participant p17 as _positive_int
    participant p18 as _limitation
    participant p19 as _validate_resolution_target
    participant p20 as _normalise_evidence
    participant p21 as _validate_endpoint_concept_references
    participant p22 as relationship_edge_key
    participant p23 as _validate_core_direction
    participant p24 as require_sha256
    participant p25 as require_nonnegative_int
    participant p26 as _open_name
    participant p27 as require_positive_int
    participant p28 as _enum
    participant p29 as set (src/llm_wiki_cli/services…aph.py:_parse_typed_graph)
    participant p30 as seen_analyzers.add
    p0->>p1: _parse_typed_graph
    p1->>p2: _object
    p1->>p3: _only_fields
    p1->>p4: _normalise_input_hashes
    p1->>p5: _array
    p1->>p6: _name
    p1->>p7: _normalise_coverage
    p1->>p8: _locator
    p1->>p9: _normalise_edge
    p1->>p10: _validate_graph_bindings
    p8->>p11: validate_exact_page_coordinate
    p7->>p12: _nonnegative_int
    p4->>p13: _hash
    p9->>p14: _relationship_kind
    p9->>p15: _normalise_endpoint
    p4->>p16: _aggregate_input_hash
    p7->>p17: _positive_int
    p7->>p18: _limitation
    p9->>p19: _validate_resolution_target
    p9->>p20: _normalise_evidence
    p9->>p21: _validate_endpoint_concept_references
    p9->>p22: relationship_edge_key
    p9->>p23: _validate_core_direction
    p13->>p24: require_sha256
    p12->>p25: require_nonnegative_int
    p14->>p26: _open_name
    p17->>p27: require_positive_int
    p15->>p28: _enum
    p1-->>p29: set (src/llm_wiki_cli/services…aph.py:_parse_typed_graph)
    p1-->>p30: seen_analyzers.add(analyzer)
```

> Call sequence diagram shows 30 of 416 interactions; 386 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 97 (96 omitted); unresolved 1 of 74 (73 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 3 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 3 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 3 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_only_fields` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 12 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 12 | - | unresolved | 2 |
> Omission summary shows 8 of 123 groups; 115 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| _object | require_mapping | 2309 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2311 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2313 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2315 | `dict(selected)` |
| _parse_typed_graph | _only_fields | 422 | `_only_fields(graph, 'typed_graph', {...}, required={...})` |
| _only_fields | require_exact_fields | 2332 | `require_shared_exact_fields(value, allowed=allowed, required=required, mapping_error=KnowledgeGraphError(...), missing_error=..., unknown_error=..., unknown_first=True)` |

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
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `validate_typed_graph_slice` | `first 12 steps` | 0 |
| truncated_flow | `validate_typed_graph_slice` | `depth limit` | 0 |

## Behavior

Validates the graph header, consumed edge shapes and their input-basis bindings. Selected observations may not exceed declared analyzer totals, but unconsumed observations are not checked. Full graph validation keeps its exact-total requirement; a slice never establishes whole-graph completeness.
