# parse_knowledge_index

**Entry point:** `parse_knowledge_index` (`api`)
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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_knowledge_index
    participant p1 as _record
    participant p2 as _string
    participant p3 as KnowledgeModelError
    participant p4 as _parse_bundle
    participant p5 as _array (src/llm_wiki_cli/services/knowledge_model.py)
    participant p6 as tuple (src/llm_wiki_cli/services….py:parse_knowledge_index)
    participant p7 as _parse_concept
    participant p8 as enumerate (src/llm_wiki_cli/services….py:parse_knowledge_index)
    participant p9 as _parse_relationship
    participant p10 as _validated_reserved_extensions
    participant p11 as _validate_index_references
    participant p12 as KnowledgeIndex
    participant p13 as validate_implementation_collection
    participant p14 as str (src/llm_wiki_cli/services….py:parse_knowledge_index)
    participant p15 as validate_maintenance_projection
    participant p16 as validate_governance_projection
    participant p17 as getattr
    participant p18 as isinstance (src/llm_wiki_cli/services….py:parse_knowledge_index)
    p0->>p1: _record
    p0->>p2: _string
    p0->>p3: KnowledgeModelError
    p0->>p4: _parse_bundle
    p0->>p5: _array (src/llm_wiki_cli/services/knowledge_model.py)
    p0-->>p6: tuple (src/llm_wiki_cli/services….py:parse_knowledge_index)(...)
    p0->>p7: _parse_concept
    p0-->>p8: enumerate (src/llm_wiki_cli/services….py:parse_knowledge_index)(concepts_value)
    p0->>p5: _array (src/llm_wiki_cli/services/knowledge_model.py)
    p0-->>p6: tuple (src/llm_wiki_cli/services….py:parse_knowledge_index)(...)
    p0->>p9: _parse_relationship
    p0-->>p8: enumerate (src/llm_wiki_cli/services….py:parse_knowledge_index)(relationships_value)
    p0->>p10: _validated_reserved_extensions
    p0->>p11: _validate_index_references
    p0->>p12: KnowledgeIndex
    p0->>p13: validate_implementation_collection
    p0->>p3: KnowledgeModelError
    p0-->>p14: str (src/llm_wiki_cli/services….py:parse_knowledge_index)(exc)
    p0->>p15: validate_maintenance_projection
    p0->>p3: KnowledgeModelError
    p0-->>p14: str (src/llm_wiki_cli/services….py:parse_knowledge_index)(exc)
    p0->>p16: validate_governance_projection
    p0-->>p17: getattr(exc, 'field', 'extensions')
    p0-->>p17: getattr(exc, 'message', str(...))
    p0-->>p14: str (src/llm_wiki_cli/services….py:parse_knowledge_index)(exc)
    p0-->>p17: getattr(exc, 'code', None)
    p0->>p3: KnowledgeModelError
    p0-->>p14: str (src/llm_wiki_cli/services….py:parse_knowledge_index)(field)
    p0-->>p14: str (src/llm_wiki_cli/services….py:parse_knowledge_index)(message)
    p0-->>p18: isinstance (src/llm_wiki_cli/services….py:parse_knowledge_index)(code, str)
```

> Call sequence diagram shows 30 of 2314 interactions; 2284 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 13 of 676 (663 omitted); unresolved 0 of 459 (459 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_model.py:_record` | 2 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 7 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 3 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 3 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 5 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 5 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_model.py:_object` | 3 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_model.py:_record` | 2 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_model.py:_parse_extensions` | 20 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 7 |
> Omission summary shows 8 of 528 groups; 520 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_knowledge_index"]
    s2["2. _record"]
    s3["3. _object (src/llm_wiki_cli/services/knowledge_model.py)"]
    s4["4. dict (src/llm_wiki_cli/services…nowledge_model.py:_object)"]
    s5["5. require_mapping"]
    s6["6. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s7["7. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s8["8. key.encode"]
    s9["9. KnowledgeModelError"]
    s10["10. KnowledgeModelError"]
    s11["11. KnowledgeModelError"]
    s12["12. sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)"]
    s1 -->|"_record(payload, '', {...}, required={...})"| s2
    s2 -->|"_object (src/llm_wiki_cli/services/knowledge_model.py)(value, ...)"| s3
    s3 -. "dict (src/llm_wiki_cli/services…nowledge_model.py:_object)(require_mapping(...))" .-> s4
    s3 -->|"require_mapping(…)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s6
    s5 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s7
    s5 -. "key.encode('utf-8')" .-> s8
    s3 -->|"KnowledgeModelError(path, 'must be an object')"| s9
    s3 -->|"KnowledgeModelError(path, 'object keys must be strings')"| s10
    s3 -->|"KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')"| s11
    s2 -. "sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)(...)" .-> s12
    click s1 "../modules/knowledge_model.md"
    click s2 "../modules/knowledge_model.md"
    click s3 "../modules/knowledge_model.md"
    click s5 "../modules/validation.md"
    click s9 "../modules/knowledge_model.md"
    click s10 "../modules/knowledge_model.md"
    click s11 "../modules/knowledge_model.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _record | sorted (src/llm_wiki_cli/services…nowledge_model.py:_record) | 1610 | `sorted(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| external_call | `_record` | `sorted` | 1610 |
| step_limit | `parse_knowledge_index` | `first 12 steps` | 0 |
| truncated_flow | `parse_knowledge_index` | `depth limit` | 0 |

## Behavior

This flow starts at `parse_knowledge_index` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
