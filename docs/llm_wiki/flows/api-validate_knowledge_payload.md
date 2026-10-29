# validate_knowledge_payload

**Entry point:** `validate_knowledge_payload` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [implementation_evidence](../modules/implementation_evidence.md), and 16 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [implementation_evidence](../modules/implementation_evidence.md)
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
    participant p23 as _object (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p24 as _open_enum_value
    participant p25 as canonical_hash
    participant p26 as _exact_fields
    participant p27 as _parse_extensions
    participant p28 as validate_section_ownership
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
    p10->>p23: _object (src/llm_wiki_cli/services/knowledge_governance.py)
    p4->>p24: _open_enum_value
    p9->>p25: canonical_hash
    p10->>p26: _exact_fields
    p2->>p27: _parse_extensions
    p6->>p28: validate_section_ownership
    p1-->>p29: tuple (src/llm_wiki_cli/services….py:parse_knowledge_index)(...)
    p8-->>p30: validated.get(IMPLEMENTATION_KEY)
```

> Call sequence diagram shows 30 of 1720 interactions; 1690 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 470 (469 omitted); unresolved 1 of 308 (307 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 4 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 4 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 6 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 4 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_model.py:_record` | 3 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_model.py:_record` | 3 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 5 |
| `src/llm_wiki_cli/services/knowledge_model.py:_parse_extensions` | 21 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 7 |
> Omission summary shows 8 of 413 groups; 405 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 943; effect analysis evaluated: 610, partial: 0, unavailable: 333. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `validate_knowledge_payload` | `available` | `evaluated` | `available` |
| `parse_knowledge_index` | `available` | `evaluated` | `available` |
| `_record` | `available` | `evaluated` | `available` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `available` | `evaluated` | `available` |
| `dict (src/llm_wiki_cli/services…nowledge_model.py:_object)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `require_mapping` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `key.encode` | `not_applicable` | `not_applicable` | `not_applicable` |
| `KnowledgeModelError` | `unavailable` | `unavailable` | `unavailable` |
| `KnowledgeModelError` | `unavailable` | `unavailable` | `unavailable` |
| `KnowledgeModelError` | `unavailable` | `unavailable` | `unavailable` |

```mermaid
flowchart LR
    s1["1. validate_knowledge_payload"]
    s2["2. parse_knowledge_index"]
    s3["3. _record"]
    s4["4. _object (src/llm_wiki_cli/services/knowledge_model.py)"]
    s5["5. dict (src/llm_wiki_cli/services…nowledge_model.py:_object)"]
    s6["6. require_mapping"]
    s7["7. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s8["8. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s9["9. key.encode"]
    s10["10. KnowledgeModelError"]
    s11["11. KnowledgeModelError"]
    s12["12. KnowledgeModelError"]
    s1 -->|"parse_knowledge_index(payload)"| s2
    s2 -->|"_record(payload, '', {...}, required={...})"| s3
    s3 -->|"_object (src/llm_wiki_cli/services/knowledge_model.py)(value, ...)"| s4
    s4 -. "dict (src/llm_wiki_cli/services…nowledge_model.py:_object)(require_mapping(...))" .-> s5
    s4 -->|"require_mapping(…)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s7
    s6 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s8
    s6 -. "key.encode('utf-8')" .-> s9
    s4 -->|"KnowledgeModelError(path, 'must be an object')"| s10
    s4 -->|"KnowledgeModelError(path, 'object keys must be strings')"| s11
    s4 -->|"KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')"| s12
    click s1 "../modules/knowledge_model.md"
    click s2 "../modules/knowledge_model.md"
    click s3 "../modules/knowledge_model.md"
    click s4 "../modules/knowledge_model.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/knowledge_model.md"
    click s11 "../modules/knowledge_model.md"
    click s12 "../modules/knowledge_model.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_knowledge_payload` | `payload: object` | - | - | `parse_knowledge_index(...)` |
| `parse_knowledge_index` | `payload: object` | `KNOWLEDGE_SCHEMA_VERSION`, `KNOWLEDGE_SCHEMA_VERSION` | - | `model` |
| `_record` | `value: object`, `path: str`, `fields: AbstractSet[str]`, `required: AbstractSet[str]` | - | - | `(...)` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `value: object`, `path: str` | - | - | `dict(...)` |
| `dict (src/llm_wiki_cli/services…nowledge_model.py:_object)` | - | - | - | - |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_payload | parse_knowledge_index | 657 | `parse_knowledge_index(payload)` |
| parse_knowledge_index | _record | 526 | `_record(payload, '', {...}, required={...})` |
| _record | _object (src/llm_wiki_cli/services/knowledge_model.py) | 1608 | `_object(value, ...)` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | dict (src/llm_wiki_cli/services…nowledge_model.py:_object) | 1694 | `dict(require_mapping(...))` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | require_mapping | 1695 | `require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=KnowledgeModelError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | KnowledgeModelError | 1697 | `KnowledgeModelError(path, 'must be an object')` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | KnowledgeModelError | 1699 | `KnowledgeModelError(path, 'object keys must be strings')` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | KnowledgeModelError | 1703 | `KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `validate_knowledge_payload` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
