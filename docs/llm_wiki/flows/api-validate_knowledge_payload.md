# validate_knowledge_payload

**Entry point:** `validate_knowledge_payload` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 8 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
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
    participant p3 as _object (src/llm_wiki_cli/services/knowledge_model.py)
    participant p4 as dict (src/llm_wiki_cli/services…nowledge_model.py:_object)
    participant p5 as require_mapping
    participant p6 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p7 as key.encode
    participant p8 as KnowledgeModelError
    participant p9 as sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)
    participant p10 as set (src/llm_wiki_cli/services…nowledge_model.py:_record)
    participant p11 as _child
    participant p12 as _parse_extensions
    participant p13 as sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    participant p14 as _QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    participant p15 as _normalize_json_value
    participant p16 as _normalize_json_value_inner
    participant p17 as isinstance (src/llm_wiki_cli/services…ormalize_json_value_inner)
    participant p18 as _string
    p0->>p1: parse_knowledge_index
    p1->>p2: _record
    p2->>p3: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p3-->>p4: dict (src/llm_wiki_cli/services…nowledge_model.py:_object)
    p3->>p5: require_mapping
    p5-->>p6: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p5-->>p6: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p5-->>p7: key.encode
    p3->>p8: KnowledgeModelError
    p3->>p8: KnowledgeModelError
    p3->>p8: KnowledgeModelError
    p2-->>p9: sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p2-->>p10: set (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p2->>p8: KnowledgeModelError
    p2->>p11: _child
    p2-->>p9: sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p2-->>p10: set (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p2->>p8: KnowledgeModelError
    p2->>p11: _child
    p2->>p12: _parse_extensions
    p12->>p3: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p12-->>p13: sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    p12-->>p14: _QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    p12->>p8: KnowledgeModelError
    p12->>p11: _child
    p12->>p15: _normalize_json_value
    p15->>p16: _normalize_json_value_inner
    p16-->>p17: isinstance (src/llm_wiki_cli/services…ormalize_json_value_inner)
    p16->>p18: _string
    p16-->>p17: isinstance (src/llm_wiki_cli/services…ormalize_json_value_inner)
```

> Call sequence diagram shows 30 of 1475 interactions; 1445 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
| validate_knowledge_payload | parse_knowledge_index | 645 | `parse_knowledge_index(payload)` |
| parse_knowledge_index | _record | 526 | `_record(payload, '', {...}, required={...})` |
| _record | _object (src/llm_wiki_cli/services/knowledge_model.py) | 1581 | `_object(value, ...)` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | dict (src/llm_wiki_cli/services…nowledge_model.py:_object) | 1667 | `dict(require_mapping(...))` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | require_mapping | 1668 | `require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=KnowledgeModelError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 731 | `isinstance(key, str)` |
| require_mapping | key.encode | 736 | `key.encode('utf-8')` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | KnowledgeModelError | 1670 | `KnowledgeModelError(path, 'must be an object')` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | KnowledgeModelError | 1672 | `KnowledgeModelError(path, 'object keys must be strings')` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | KnowledgeModelError | 1676 | `KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 727 |
| external_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `validate_knowledge_payload` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_payload` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_payload` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
