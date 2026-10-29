# knowledge_index_to_payload

**Entry point:** `knowledge_index_to_payload` (`api`)
**Source:** [knowledge_index](../modules/knowledge_index.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [immutable](../modules/immutable.md), and 21 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [markdown_sections](../modules/markdown_sections.md)
- [progress](../modules/progress.md)
- [python_implementation](../modules/python_implementation.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as knowledge_index_to_payload
    participant p1 as _model_to_payload
    participant p2 as validate_knowledge_index
    participant p3 as _knowledge_index_to_payload_unchecked
    participant p4 as parse_knowledge_index
    participant p5 as _validate_builder_model
    participant p6 as build_knowledge_index
    participant p7 as _first_difference
    participant p8 as _bundle_to_payload
    participant p9 as _record
    participant p10 as _validate_and_join_inputs
    participant p11 as _string
    participant p12 as _concept_for_page
    participant p13 as _parse_bundle
    participant p14 as _concept_to_payload
    participant p15 as _derived_relationship
    participant p16 as _relationship_to_payload
    participant p17 as _parse_concept
    participant p18 as _link_relationship
    participant p19 as _require_structure_state
    participant p20 as _parse_relationship
    participant p21 as _validated_reserved_extensions
    participant p22 as _validate_index_references
    participant p23 as validate_implementation_collection
    participant p24 as freeze
    participant p25 as validate_maintenance_projection
    participant p26 as _validate_builder_link
    participant p27 as _serialize_payload
    participant p28 as validate_governance_projection
    participant p29 as isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)
    participant p30 as model.bundle.snapshot.extensions.get
    p0->>p1: _model_to_payload
    p0->>p2: validate_knowledge_index
    p1->>p3: _knowledge_index_to_payload_unchecked
    p2->>p4: parse_knowledge_index
    p2->>p5: _validate_builder_model
    p2->>p6: build_knowledge_index
    p2->>p7: _first_difference
    p3->>p8: _bundle_to_payload
    p4->>p9: _record
    p6->>p10: _validate_and_join_inputs
    p4->>p11: _string
    p6->>p12: _concept_for_page
    p4->>p13: _parse_bundle
    p3->>p14: _concept_to_payload
    p6->>p15: _derived_relationship
    p3->>p16: _relationship_to_payload
    p4->>p17: _parse_concept
    p6->>p18: _link_relationship
    p5->>p19: _require_structure_state
    p4->>p20: _parse_relationship
    p4->>p21: _validated_reserved_extensions
    p4->>p22: _validate_index_references
    p4->>p23: validate_implementation_collection
    p6->>p24: freeze
    p4->>p25: validate_maintenance_projection
    p5->>p26: _validate_builder_link
    p6->>p27: _serialize_payload
    p4->>p28: validate_governance_projection
    p2-->>p29: isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)(value, KnowledgeIndex)
    p5-->>p30: model.bundle.snapshot.extensions.get(INVENTORY_HASH_EXTENSION)
```

> Call sequence diagram shows 30 of 1725 interactions; 1695 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 443 (442 omitted); unresolved 1 of 268 (267 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_model.py:_bundle_to_payload` | 4 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 8 |
| `src/llm_wiki_cli/services/knowledge_model.py:_emit_extensions` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_emit_extensions` | 5 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_parse_extensions` | 7 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 7 |
| `src/llm_wiki_cli/services/knowledge_model.py:_parse_extensions` | 7 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_parse_extensions` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_wire_enum` | 17 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_component_to_payload` | 21 | - | external | 1 |
> Omission summary shows 8 of 397 groups; 389 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1015; effect analysis evaluated: 565, partial: 20, unavailable: 430. Counts include steps omitted from the displayed trace.

Collector observations for 585 source steps with known totals: observed: 2954, emitted: 2728, omitted: 226. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `knowledge_index_to_payload` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_model_to_payload` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `_knowledge_index_to_payload_unchecked` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `_bundle_to_payload` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_emit_extensions` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_parse_extensions` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeModelError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_child` | `available` | `evaluated` | `available` | `3` | `3` | `0` |

```mermaid
flowchart LR
    s1["1. knowledge_index_to_payload"]
    s2["2. _model_to_payload"]
    s3["3. _knowledge_index_to_payload_unchecked"]
    s4["4. _bundle_to_payload"]
    s5["5. _emit_extensions"]
    s6["6. isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions)"]
    s7["7. _parse_extensions"]
    s8["8. _object (src/llm_wiki_cli/services/knowledge_model.py)"]
    s9["9. sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)"]
    s10["10. _QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)"]
    s11["11. KnowledgeModelError"]
    s12["12. _child"]
    s1 -->|"_model_to_payload(validate_knowledge_index(...))"| s2
    s2 -->|"_knowledge_index_to_payload_unchecked(model)"| s3
    s3 -->|"_bundle_to_payload(model.bundle)"| s4
    s4 -->|"_emit_extensions({...}, bundle.repository.extensions, 'bundle.repository.extensions')"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions)(extensions, FrozenDict)" .-> s6
    s5 -->|"_parse_extensions(extensions, path)"| s7
    s7 -->|"_object (src/llm_wiki_cli/services/knowledge_model.py)(value, path)"| s8
    s7 -. "sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)(data)" .-> s9
    s7 -. "_QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)(key)" .-> s10
    s7 -->|"KnowledgeModelError(_child(...), 'extension key must use namespace/name syntax')"| s11
    s7 -->|"_child(path, key)"| s12
    click s1 "../modules/knowledge_index.md"
    click s2 "../modules/knowledge_index.md"
    click s3 "../modules/knowledge_model.md"
    click s4 "../modules/knowledge_model.md"
    click s5 "../modules/knowledge_model.md"
    click s7 "../modules/knowledge_model.md"
    click s8 "../modules/knowledge_model.md"
    click s11 "../modules/knowledge_model.md"
    click s12 "../modules/knowledge_model.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `knowledge_index_to_payload` | `value: KnowledgeIndex \| object` | - | - | `_model_to_payload(...)` |
| `_model_to_payload` | `model: KnowledgeIndex` | `KnowledgeModelError` | - | `_knowledge_index_to_payload_unchecked(...)` |
| `_knowledge_index_to_payload_unchecked` | `model: KnowledgeIndex` | `_canonical_relationship_key` | `producer[...]`, `producer[...]` | `_emit_extensions(...)` |
| `_bundle_to_payload` | `bundle: BundleRecord` | - | - | `_emit_extensions(...)` |
| `_emit_extensions` | `payload: dict[str, Any]`, `extensions: Extensions`, `path: str` | - | `payload[...]` | `payload` |
| `isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions)` | - | - | - | - |
| `_parse_extensions` | `value: object`, `path: str` | - | `result[...]` | `result` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `value: object`, `path: str` | - | - | `dict(...)` |
| `sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)` | - | - | - | - |
| `_QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `_child` | `path: str`, `name: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| knowledge_index_to_payload | _model_to_payload | 292 | `_model_to_payload(validate_knowledge_index(...))` |
| _model_to_payload | _knowledge_index_to_payload_unchecked | 298 | `_knowledge_index_to_payload_unchecked(model)` |
| _knowledge_index_to_payload_unchecked | _bundle_to_payload | 2224 | `_bundle_to_payload(model.bundle)` |
| _bundle_to_payload | _emit_extensions | 2043 | `_emit_extensions({...}, bundle.repository.extensions, 'bundle.repository.extensions')` |
| _emit_extensions | isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions) | 2003 | `isinstance(extensions, FrozenDict)` |
| _emit_extensions | _parse_extensions | 2004 | `_parse_extensions(extensions, path)` |
| _parse_extensions | _object (src/llm_wiki_cli/services/knowledge_model.py) | 1627 | `_object(value, path)` |
| _parse_extensions | sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions) | 1629 | `sorted(data)` |
| _parse_extensions | _QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions) | 1630 | `_QUALIFIED_NAME_RE.fullmatch(key)` |
| _parse_extensions | KnowledgeModelError | 1631 | `KnowledgeModelError(_child(...), 'extension key must use namespace/name syntax')` |
| _parse_extensions | _child | 1632 | `_child(path, key)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_emit_extensions` | `isinstance` | 2003 |
| external_call | `_parse_extensions` | `sorted` | 1629 |
| unresolved_call | `_parse_extensions` | `_QUALIFIED_NAME_RE.fullmatch` | 1630 |
| step_limit | `knowledge_index_to_payload` | `first 12 steps` | 0 |
| truncated_flow | `knowledge_index_to_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `knowledge_index_to_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
