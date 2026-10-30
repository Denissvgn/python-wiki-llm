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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as typed_graph_from_knowledge_extensions
    participant p1 as validate_typed_graph
    participant p2 as KnowledgeGraphError
    participant p3 as _parse_typed_graph
    participant p4 as _object
    participant p5 as _only_fields
    participant p6 as _normalise_input_hashes
    participant p7 as _array
    participant p8 as _name
    participant p9 as _normalise_coverage
    participant p10 as _locator
    participant p11 as _normalise_edge
    participant p12 as _validate_graph_bindings
    participant p13 as require_nonempty_text
    participant p14 as validate_exact_page_coordinate
    participant p15 as _nonnegative_int
    participant p16 as _hash
    participant p17 as _relationship_kind
    participant p18 as _normalise_endpoint
    participant p19 as _aggregate_input_hash
    participant p20 as _positive_int
    participant p21 as _limitation
    participant p22 as _validate_resolution_target
    participant p23 as _normalise_evidence
    participant p24 as _validate_endpoint_concept_references
    participant p25 as relationship_edge_key
    participant p26 as _validate_core_direction
    participant p27 as require_sha256
    participant p28 as require_nonnegative_int
    participant p29 as isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)
    participant p30 as extensions.get
    p0->>p1: validate_typed_graph
    p0->>p2: KnowledgeGraphError
    p1->>p3: _parse_typed_graph
    p3->>p4: _object
    p3->>p5: _only_fields
    p3->>p6: _normalise_input_hashes
    p3->>p7: _array
    p3->>p8: _name
    p3->>p9: _normalise_coverage
    p3->>p10: _locator
    p3->>p11: _normalise_edge
    p3->>p12: _validate_graph_bindings
    p8->>p13: require_nonempty_text
    p10->>p14: validate_exact_page_coordinate
    p9->>p15: _nonnegative_int
    p6->>p16: _hash
    p11->>p17: _relationship_kind
    p11->>p18: _normalise_endpoint
    p6->>p19: _aggregate_input_hash
    p9->>p20: _positive_int
    p9->>p21: _limitation
    p11->>p22: _validate_resolution_target
    p11->>p23: _normalise_evidence
    p11->>p24: _validate_endpoint_concept_references
    p11->>p25: relationship_edge_key
    p11->>p26: _validate_core_direction
    p16->>p27: require_sha256
    p15->>p28: require_nonnegative_int
    p0-->>p29: isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)(extensions, Mapping)
    p0-->>p30: extensions.get(TYPED_GRAPH_EXTENSION_KEY)
```

> Call sequence diagram shows 30 of 337 interactions; 307 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 73 (72 omitted); unresolved 1 of 51 (50 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 7 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 8 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 7 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 7 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_only_fields` | 15 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 16 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 16 | - | unresolved | 2 |
> Omission summary shows 8 of 101 groups; 93 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 214; effect analysis evaluated: 147, partial: 2, unavailable: 65. Counts include steps omitted from the displayed trace.

Collector observations for 149 source steps with known totals: observed: 656, emitted: 651, omitted: 5. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `typed_graph_from_knowledge_extensions` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `isinstance (src/llm_wiki_cli/services…from_knowledge_extensions)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeGraphError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `extensions.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `validate_typed_graph` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `_parse_typed_graph` | `available` | `evaluated` | `available` | `13` | `13` | `0` |
| `_object` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_mapping` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `key.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeGraphError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

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
| _object | require_mapping | 2309 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2311 | `KnowledgeGraphError(path, 'must be an object')` |

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
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `typed_graph_from_knowledge_extensions` | `first 12 steps` | 0 |
| truncated_flow | `typed_graph_from_knowledge_extensions` | `depth limit` | 0 |

## Behavior

This flow starts at `typed_graph_from_knowledge_extensions` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
