# evaluate_knowledge_freshness

**Entry point:** `evaluate_knowledge_freshness` (`api`)
**Source:** [knowledge_freshness](../modules/knowledge_freshness.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_freshness](../modules/knowledge_freshness.md), and 8 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
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
    participant p0 as evaluate_knowledge_freshness
    participant p1 as isinstance
    participant p2 as parse_knowledge_index
    participant p3 as _record
    participant p4 as _object
    participant p5 as dict
    participant p6 as require_mapping
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
    p0-->>p1: isinstance
    p0->>p2: parse_knowledge_index
    p2->>p3: _record
    p3->>p4: _object
    p4-->>p5: dict
    p4->>p6: require_mapping
    p6-->>p1: isinstance
    p6-->>p1: isinstance
    p6-->>p7: encode
    p4->>p8: KnowledgeModelError
    p4->>p8: KnowledgeModelError
    p4->>p8: KnowledgeModelError
    p3-->>p9: sorted
    p3-->>p10: set
    p3->>p8: KnowledgeModelError
    p3->>p11: _child
    p3-->>p9: sorted
    p3-->>p10: set
    p3->>p8: KnowledgeModelError
    p3->>p11: _child
    p3->>p12: _parse_extensions
    p12->>p4: _object
    p12-->>p9: sorted
    p12-->>p13: fullmatch
    p12->>p8: KnowledgeModelError
    p12->>p11: _child
    p12->>p14: _normalize_json_value
    p14->>p15: _normalize_json_value_inner
    p15-->>p1: isinstance
    p15->>p16: _string
```

> Call sequence diagram shows 30 of 1629 interactions; 1599 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_knowledge_freshness"]
    s2["2. isinstance"]
    s3["3. parse_knowledge_index"]
    s4["4. _record"]
    s5["5. _object"]
    s6["6. dict"]
    s7["7. require_mapping"]
    s8["8. isinstance"]
    s9["9. isinstance"]
    s10["10. encode"]
    s11["11. KnowledgeModelError"]
    s12["12. KnowledgeModelError"]
    s1 -. "isinstance(knowledge, KnowledgeIndex)" .-> s2
    s1 -->|"parse_knowledge_index(knowledge_index_to_payload(...))"| s3
    s3 -->|"_record(payload, '', {...}, required={...})"| s4
    s4 -->|"_object(value, ...)"| s5
    s5 -. "dict(require_mapping(...))" .-> s6
    s5 -->|"require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=Kno…"| s7
    s7 -. "isinstance(value, Mapping)" .-> s8
    s7 -. "isinstance(key, str)" .-> s9
    s7 -. "key.encode('utf-8')" .-> s10
    s5 -->|"KnowledgeModelError(path, 'must be an object')"| s11
    s5 -->|"KnowledgeModelError(path, 'object keys must be strings')"| s12
    click s1 "../modules/knowledge_freshness.md"
    click s3 "../modules/knowledge_model.md"
    click s4 "../modules/knowledge_model.md"
    click s5 "../modules/knowledge_model.md"
    click s7 "../modules/validation.md"
    click s11 "../modules/knowledge_model.md"
    click s12 "../modules/knowledge_model.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `evaluate_knowledge_freshness` | `knowledge: KnowledgeIndex \| object`, `live: LiveKnowledgeEvaluation \| None` | `KnowledgeIndex`, `KnowledgeModelError`, `ComputedFreshness` | `results[...]`, `counts[...]` | `KnowledgeFreshnessReport(...)` |
| `isinstance` | - | - | - | - |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluate_knowledge_freshness | isinstance | 229 | `isinstance(knowledge, KnowledgeIndex)` |
| evaluate_knowledge_freshness | parse_knowledge_index | 228 | `parse_knowledge_index(knowledge_index_to_payload(...))` |
| parse_knowledge_index | _record | 526 | `_record(payload, '', {...}, required={...})` |
| _record | _object | 1571 | `_object(value, ...)` |
| _object | dict | 1657 | `dict(require_mapping(...))` |
| _object | require_mapping | 1658 | `require_mapping(value, error=KnowledgeModelError(...), require_string_keys=True, key_error=KnowledgeModelError(...), require_utf8_keys=True, utf8_key_error=KnowledgeModelError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeModelError | 1660 | `KnowledgeModelError(path, 'must be an object')` |
| _object | KnowledgeModelError | 1662 | `KnowledgeModelError(path, 'object keys must be strings')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `evaluate_knowledge_freshness` | `isinstance` | 229 |
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `evaluate_knowledge_freshness` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_knowledge_freshness` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_knowledge_freshness` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
