# parse_knowledge_index

**Entry point:** `parse_knowledge_index` (`api`)
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
    participant p0 as parse_knowledge_index
    participant p1 as _record
    participant p2 as _object
    participant p3 as dict
    participant p4 as require_mapping
    participant p5 as isinstance
    participant p6 as encode
    participant p7 as KnowledgeModelError
    participant p8 as sorted
    participant p9 as set
    participant p10 as _child
    participant p11 as _parse_extensions
    participant p12 as fullmatch
    participant p13 as _normalize_json_value
    participant p14 as _normalize_json_value_inner
    participant p15 as _string
    participant p16 as require_string
    p0->>p1: _record
    p1->>p2: _object
    p2-->>p3: dict
    p2->>p4: require_mapping
    p4-->>p5: isinstance
    p4-->>p5: isinstance
    p4-->>p6: encode
    p2->>p7: KnowledgeModelError
    p2->>p7: KnowledgeModelError
    p2->>p7: KnowledgeModelError
    p1-->>p8: sorted
    p1-->>p9: set
    p1->>p7: KnowledgeModelError
    p1->>p10: _child
    p1-->>p8: sorted
    p1-->>p9: set
    p1->>p7: KnowledgeModelError
    p1->>p10: _child
    p1->>p11: _parse_extensions
    p11->>p2: _object
    p11-->>p8: sorted
    p11-->>p12: fullmatch
    p11->>p7: KnowledgeModelError
    p11->>p10: _child
    p11->>p13: _normalize_json_value
    p13->>p14: _normalize_json_value_inner
    p14-->>p5: isinstance
    p14->>p15: _string
    p15->>p16: require_string
    p15->>p7: KnowledgeModelError
```

> Call sequence diagram shows 30 of 1999 interactions; 1969 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_knowledge_index"]
    s2["2. _record"]
    s3["3. _object"]
    s4["4. dict"]
    s5["5. require_mapping"]
    s6["6. isinstance"]
    s7["7. isinstance"]
    s8["8. encode"]
    s9["9. KnowledgeModelError"]
    s10["10. KnowledgeModelError"]
    s11["11. KnowledgeModelError"]
    s12["12. sorted"]
    s1 -->|"_record(payload, '', {...}, required={...})"| s2
    s2 -->|"_object(value, ...)"| s3
    s3 -. "dict(require_mapping(...))" .-> s4
    s3 -->|"require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=Kno…"| s5
    s5 -. "isinstance(value, Mapping)" .-> s6
    s5 -. "isinstance(key, str)" .-> s7
    s5 -. "key.encode('utf-8')" .-> s8
    s3 -->|"KnowledgeModelError(path, 'must be an object')"| s9
    s3 -->|"KnowledgeModelError(path, 'object keys must be strings')"| s10
    s3 -->|"KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')"| s11
    s2 -. "sorted(...)" .-> s12
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
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `dict` | - | - | - | - |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `sorted` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _record | sorted | 1573 | `sorted(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| unresolved_call | `_record` | `sorted` | 1573 |
| step_limit | `parse_knowledge_index` | `first 12 steps` | 0 |
| truncated_flow | `parse_knowledge_index` | `depth limit` | 0 |

## Behavior

This flow starts at `parse_knowledge_index` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
