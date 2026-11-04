# validate_knowledge_index

**Entry point:** `validate_knowledge_index` (`api`)
**Source:** [knowledge_index](../modules/knowledge_index.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [immutable](../modules/immutable.md), and 22 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
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
    participant p0 as validate_knowledge_index
    participant p1 as parse_knowledge_index
    participant p2 as _model_to_payload
    participant p3 as _validate_builder_model
    participant p4 as build_knowledge_index
    participant p5 as _first_difference
    participant p6 as canonical_json_text
    participant p7 as KnowledgeIndexBuildError
    participant p8 as _record
    participant p9 as _knowledge_index_to_payload_unchecked
    participant p10 as _assemble_knowledge_index
    participant p11 as _validator_identity
    participant p12 as _parse_bundle
    participant p13 as _parse_concept
    participant p14 as freeze
    participant p15 as _serialize_payload
    participant p16 as _require_structure_state
    participant p17 as _parse_relationship
    participant p18 as _validated_reserved_extensions
    participant p19 as _validate_index_references
    participant p20 as validate_implementation_collection
    participant p21 as validate_maintenance_projection
    participant p22 as _validate_builder_link
    participant p23 as validate_governance_projection
    participant p24 as _validate_builder_derived
    participant p25 as _object (src/llm_wiki_cli/services/knowledge_model.py)
    participant p26 as _bundle_to_payload
    participant p27 as _validate_and_join_inputs
    participant p28 as _parse_document
    participant p29 as isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)
    participant p30 as model.bundle.snapshot.extensions.get
    p0->>p1: parse_knowledge_index
    p0->>p2: _model_to_payload
    p0->>p3: _validate_builder_model
    p0->>p4: build_knowledge_index
    p0->>p5: _first_difference
    p0->>p6: canonical_json_text
    p0->>p7: KnowledgeIndexBuildError
    p1->>p8: _record
    p2->>p9: _knowledge_index_to_payload_unchecked
    p4->>p10: _assemble_knowledge_index
    p4->>p11: _validator_identity
    p1->>p12: _parse_bundle
    p1->>p13: _parse_concept
    p4->>p14: freeze
    p4->>p15: _serialize_payload
    p3->>p16: _require_structure_state
    p1->>p17: _parse_relationship
    p1->>p18: _validated_reserved_extensions
    p1->>p19: _validate_index_references
    p1->>p20: validate_implementation_collection
    p1->>p21: validate_maintenance_projection
    p3->>p22: _validate_builder_link
    p1->>p23: validate_governance_projection
    p3->>p24: _validate_builder_derived
    p8->>p25: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p9->>p26: _bundle_to_payload
    p10->>p27: _validate_and_join_inputs
    p13->>p28: _parse_document
    p0-->>p29: isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)(value, KnowledgeIndex)
    p3-->>p30: model.bundle.snapshot.extensions.get(INVENTORY_HASH_EXTENSION)
```

> Call sequence diagram shows 30 of 2362 interactions; 2332 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 669 (668 omitted); unresolved 1 of 396 (395 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 5 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 7 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 7 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 3 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 9 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_record` | 4 | - | external | 4 |
> Omission summary shows 8 of 576 groups; 568 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1298; effect analysis evaluated: 766, partial: 33, unavailable: 499. Counts include steps omitted from the displayed trace.

Collector observations for 799 source steps with known totals: observed: 4146, emitted: 3895, omitted: 251. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_knowledge_index` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `parse_knowledge_index` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_record` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `dict (src/llm_wiki_cli/services…nowledge_model.py:_object)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `require_mapping` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `error` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. validate_knowledge_index"]
    s2["2. isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)"]
    s3["3. parse_knowledge_index"]
    s4["4. _record"]
    s5["5. _object (src/llm_wiki_cli/services/knowledge_model.py)"]
    s6["6. dict (src/llm_wiki_cli/services…nowledge_model.py:_object)"]
    s7["7. require_mapping"]
    s8["8. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s9["9. _validation_error"]
    s10["10. isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)"]
    s11["11. error"]
    s12["12. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)(value, KnowledgeIndex)" .-> s2
    s1 -->|"parse_knowledge_index(_model_to_payload(...))"| s3
    s3 -->|"_record(payload, '', {...}, required={...})"| s4
    s4 -->|"_object (src/llm_wiki_cli/services/knowledge_model.py)(value, ...)"| s5
    s5 -. "dict (src/llm_wiki_cli/services…nowledge_model.py:_object)(require_mapping(...))" .-> s6
    s5 -->|"require_mapping(…)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s8
    s7 -->|"_validation_error(error, error_context)"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)(error, Exception)" .-> s10
    s9 -. "error(context)" .-> s11
    s7 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s12
    click s1 "../modules/knowledge_index.md"
    click s3 "../modules/knowledge_model.md"
    click s4 "../modules/knowledge_model.md"
    click s5 "../modules/knowledge_model.md"
    click s7 "../modules/validation.md"
    click s9 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_knowledge_index` | `value: KnowledgeIndex \| object`, `inputs: KnowledgeIndexInputs \| None` | `KnowledgeIndex` | - | `model` |
| `isinstance (src/llm_wiki_cli/services…:validate_knowledge_index)` | - | - | - | - |
| `parse_knowledge_index` | `payload: object` | `KNOWLEDGE_SCHEMA_VERSION`, `KNOWLEDGE_SCHEMA_VERSION` | - | `model` |
| `_record` | `value: object`, `path: str`, `fields: AbstractSet[str]`, `required: AbstractSet[str]` | - | - | `(...)` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `value: object`, `path: str` | `_OBJECT_ERROR`, `_OBJECT_KEYS_ERROR`, `_UTF8_ERROR` | - | `dict(...)` |
| `dict (src/llm_wiki_cli/services…nowledge_model.py:_object)` | - | - | - | - |
| `require_mapping` | `value: object`, `error: _ValidationError`, `error_context: str`, `require_string_keys: bool`, `key_error: _ValidationError \| None`, `require_utf8_keys: bool`, `utf8_key_error: _ValidationError \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_index | isinstance (src/llm_wiki_cli/services…:validate_knowledge_index) | 280 | `isinstance(value, KnowledgeIndex)` |
| validate_knowledge_index | parse_knowledge_index | 282 | `parse_knowledge_index(_model_to_payload(...))` |
| parse_knowledge_index | _record | 551 | `_record(payload, '', {...}, required={...})` |
| _record | _object (src/llm_wiki_cli/services/knowledge_model.py) | 1633 | `_object(value, ...)` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | dict (src/llm_wiki_cli/services…nowledge_model.py:_object) | 1719 | `dict(require_mapping(...))` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | require_mapping | 1720 | `require_mapping(value, error=_OBJECT_ERROR, error_context=path, require_string_keys=True, key_error=_OBJECT_KEYS_ERROR, require_utf8_keys=True, utf8_key_error=_UTF8_ERROR)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 783 | `isinstance(value, Mapping)` |
| require_mapping | _validation_error | 784 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…tion.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 787 | `isinstance(key, str)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_knowledge_index` | `isinstance` | 280 |
| external_call | `require_mapping` | `isinstance` | 783 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |
| external_call | `require_mapping` | `isinstance` | 787 |
| step_limit | `validate_knowledge_index` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_index` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_index` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
