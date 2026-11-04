# validate_knowledge_payload

**Entry point:** `validate_knowledge_payload` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [implementation_evidence](../modules/implementation_evidence.md), and 17 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [markdown_sections](../modules/markdown_sections.md)
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
    participant p0 as validate_knowledge_payload
    participant p1 as parse_knowledge_index
    participant p2 as _record
    participant p3 as _parse_bundle
    participant p4 as _parse_concept
    participant p5 as _parse_relationship
    participant p6 as _validated_reserved_extensions
    participant p7 as _validate_index_references
    participant p8 as validate_implementation_collection
    participant p9 as validate_maintenance_projection
    participant p10 as validate_governance_projection
    participant p11 as _object (src/llm_wiki_cli/services/knowledge_model.py)
    participant p12 as _parse_document
    participant p13 as validate_reuse_commitment
    participant p14 as _parse_repository
    participant p15 as _locator (src/llm_wiki_cli/services/knowledge_model.py)
    participant p16 as _parse_snapshot
    participant p17 as typed_graph_from_knowledge_extensions
    participant p18 as mcp_uri
    participant p19 as _parse_producer
    participant p20 as _parse_relationship_target
    participant p21 as validate_maintenance_binding
    participant p22 as validate_maintenance_state
    participant p23 as _open_enum_value
    participant p24 as canonical_hash
    participant p25 as _parse_extensions
    participant p26 as validate_section_ownership
    participant p27 as _object (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p28 as _parse_relationship_evidence
    participant p29 as tuple (src/llm_wiki_cli/services….py:parse_knowledge_index)
    participant p30 as validated.get
    p0->>p1: parse_knowledge_index
    p1->>p2: _record
    p1->>p3: _parse_bundle
    p1->>p4: _parse_concept
    p1->>p5: _parse_relationship
    p1->>p6: _validated_reserved_extensions
    p1->>p7: _validate_index_references
    p1->>p8: validate_implementation_collection
    p1->>p9: validate_maintenance_projection
    p1->>p10: validate_governance_projection
    p2->>p11: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p4->>p12: _parse_document
    p6->>p13: validate_reuse_commitment
    p3->>p14: _parse_repository
    p4->>p15: _locator (src/llm_wiki_cli/services/knowledge_model.py)
    p3->>p16: _parse_snapshot
    p6->>p17: typed_graph_from_knowledge_extensions
    p4->>p18: mcp_uri
    p3->>p19: _parse_producer
    p5->>p20: _parse_relationship_target
    p9->>p21: validate_maintenance_binding
    p9->>p22: validate_maintenance_state
    p4->>p23: _open_enum_value
    p9->>p24: canonical_hash
    p2->>p25: _parse_extensions
    p6->>p26: validate_section_ownership
    p10->>p27: _object (src/llm_wiki_cli/services/knowledge_governance.py)
    p5->>p28: _parse_relationship_evidence
    p1-->>p29: tuple (src/llm_wiki_cli/services….py:parse_knowledge_index)(...)
    p8-->>p30: validated.get(IMPLEMENTATION_KEY)
```

> Call sequence diagram shows 30 of 1705 interactions; 1675 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 463 (462 omitted); unresolved 1 of 303 (302 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 4 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 4 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 3 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 8 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_record` | 3 | - | external | 4 |
> Omission summary shows 8 of 419 groups; 411 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 940; effect analysis evaluated: 608, partial: 15, unavailable: 317. Counts include steps omitted from the displayed trace.

Collector observations for 623 source steps with known totals: observed: 3083, emitted: 2918, omitted: 165. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_knowledge_payload` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
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
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |

```mermaid
flowchart LR
    s1["1. validate_knowledge_payload"]
    s2["2. parse_knowledge_index"]
    s3["3. _record"]
    s4["4. _object (src/llm_wiki_cli/services/knowledge_model.py)"]
    s5["5. dict (src/llm_wiki_cli/services…nowledge_model.py:_object)"]
    s6["6. require_mapping"]
    s7["7. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s8["8. _validation_error"]
    s9["9. isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)"]
    s10["10. error"]
    s11["11. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s12["12. _validation_error"]
    s1 -->|"parse_knowledge_index(payload)"| s2
    s2 -->|"_record(payload, '', {...}, required={...})"| s3
    s3 -->|"_object (src/llm_wiki_cli/services/knowledge_model.py)(value, ...)"| s4
    s4 -. "dict (src/llm_wiki_cli/services…nowledge_model.py:_object)(require_mapping(...))" .-> s5
    s4 -->|"require_mapping(…)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s7
    s6 -->|"_validation_error(error, error_context)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)(error, Exception)" .-> s9
    s8 -. "error(context)" .-> s10
    s6 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s11
    s6 -->|"_validation_error(..., error_context)"| s12
    click s1 "../modules/knowledge_model.md"
    click s2 "../modules/knowledge_model.md"
    click s3 "../modules/knowledge_model.md"
    click s4 "../modules/knowledge_model.md"
    click s6 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_knowledge_payload` | `payload: object` | - | - | `parse_knowledge_index(...)` |
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
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_payload | parse_knowledge_index | 682 | `parse_knowledge_index(payload)` |
| parse_knowledge_index | _record | 551 | `_record(payload, '', {...}, required={...})` |
| _record | _object (src/llm_wiki_cli/services/knowledge_model.py) | 1633 | `_object(value, ...)` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | dict (src/llm_wiki_cli/services…nowledge_model.py:_object) | 1719 | `dict(require_mapping(...))` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | require_mapping | 1720 | `require_mapping(value, error=_OBJECT_ERROR, error_context=path, require_string_keys=True, key_error=_OBJECT_KEYS_ERROR, require_utf8_keys=True, utf8_key_error=_UTF8_ERROR)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 783 | `isinstance(value, Mapping)` |
| require_mapping | _validation_error | 784 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…tion.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 787 | `isinstance(key, str)` |
| require_mapping | _validation_error | 788 | `_validation_error(..., error_context)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 783 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |
| external_call | `require_mapping` | `isinstance` | 787 |
| step_limit | `validate_knowledge_payload` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
