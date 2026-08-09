# validate_knowledge_payload

**Entry point:** `validate_knowledge_payload` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 7 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_knowledge_payload
    participant p1 as parse_knowledge_index
    participant p2 as _record
    participant p3 as _object
    participant p4 as dict
    participant p5 as require_mapping
    participant p6 as isinstance
    participant p7 as encode
    participant p8 as KnowledgeModelError
    participant p9 as sorted
    participant p10 as set
    participant p11 as _child
    participant p12 as _parse_extensions
    participant p13 as fullmatch
    participant p14 as _normalize_json_value
    participant p15 as _normalize_json_value_inner
    participant p16 as _string
    p0->>p1: parse_knowledge_index
    p1->>p2: _record
    p2->>p3: _object
    p3-->>p4: dict
    p3->>p5: require_mapping
    p5-->>p6: isinstance
    p5-->>p6: isinstance
    p5-->>p7: encode
    p3->>p8: KnowledgeModelError
    p3->>p8: KnowledgeModelError
    p3->>p8: KnowledgeModelError
    p2-->>p9: sorted
    p2-->>p10: set
    p2->>p8: KnowledgeModelError
    p2->>p11: _child
    p2-->>p9: sorted
    p2-->>p10: set
    p2->>p8: KnowledgeModelError
    p2->>p11: _child
    p2->>p12: _parse_extensions
    p12->>p3: _object
    p12-->>p9: sorted
    p12-->>p13: fullmatch
    p12->>p8: KnowledgeModelError
    p12->>p11: _child
    p12->>p14: _normalize_json_value
    p14->>p15: _normalize_json_value_inner
    p15-->>p6: isinstance
    p15->>p16: _string
    p15-->>p6: isinstance
```

> Call sequence diagram shows 30 of 1449 interactions; 1419 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_knowledge_payload"]
    s2["2. parse_knowledge_index"]
    s3["3. _record"]
    s4["4. _object"]
    s5["5. dict"]
    s6["6. require_mapping"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. encode"]
    s10["10. KnowledgeModelError"]
    s11["11. KnowledgeModelError"]
    s12["12. KnowledgeModelError"]
    s1 -->|"parse_knowledge_index(payload)"| s2
    s2 -->|"_record(payload, '', {...}, required={...})"| s3
    s3 -->|"_object(value, ...)"| s4
    s4 -. "dict(require_mapping(...))" .-> s5
    s4 -->|"require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=Kno…"| s6
    s6 -. "isinstance(value, Mapping)" .-> s7
    s6 -. "isinstance(key, str)" .-> s8
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
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `dict` | - | - | - | - |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_payload | parse_knowledge_index | 635 | `parse_knowledge_index(payload)` |
| parse_knowledge_index | _record | 526 | `_record(payload, '', {...}, required={...})` |
| _record | _object | 1571 | `_object(value, ...)` |
| _object | dict | 1657 | `dict(require_mapping(...))` |
| _object | require_mapping | 1658 | `require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=KnowledgeModelError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeModelError | 1660 | `KnowledgeModelError(path, 'must be an object')` |
| _object | KnowledgeModelError | 1662 | `KnowledgeModelError(path, 'object keys must be strings')` |
| _object | KnowledgeModelError | 1666 | `KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `validate_knowledge_payload` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
