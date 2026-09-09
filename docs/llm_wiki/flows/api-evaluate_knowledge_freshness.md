# evaluate_knowledge_freshness

**Entry point:** `evaluate_knowledge_freshness` (`api`)
**Source:** [knowledge_freshness](../modules/knowledge_freshness.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 10 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
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
    participant p0 as evaluate_knowledge_freshness
    participant p1 as isinstance
    participant p2 as require_validated_artifacts
    participant p3 as TypeError
    participant p4 as parse_knowledge_index
    participant p5 as _record
    participant p6 as _object
    participant p7 as dict
    participant p8 as require_mapping
    participant p9 as encode
    participant p10 as KnowledgeModelError
    participant p11 as sorted
    participant p12 as set
    participant p13 as _child
    participant p14 as _parse_extensions
    participant p15 as fullmatch
    p0-->>p1: isinstance
    p0->>p2: require_validated_artifacts
    p2-->>p1: isinstance
    p2-->>p3: TypeError
    p2-->>p1: isinstance
    p2-->>p3: TypeError
    p0-->>p1: isinstance
    p0->>p4: parse_knowledge_index
    p4->>p5: _record
    p5->>p6: _object
    p6-->>p7: dict
    p6->>p8: require_mapping
    p8-->>p1: isinstance
    p8-->>p1: isinstance
    p8-->>p9: encode
    p6->>p10: KnowledgeModelError
    p6->>p10: KnowledgeModelError
    p6->>p10: KnowledgeModelError
    p5-->>p11: sorted
    p5-->>p12: set
    p5->>p10: KnowledgeModelError
    p5->>p13: _child
    p5-->>p11: sorted
    p5-->>p12: set
    p5->>p10: KnowledgeModelError
    p5->>p13: _child
    p5->>p14: _parse_extensions
    p14->>p6: _object
    p14-->>p11: sorted
    p14-->>p15: fullmatch
```

> Call sequence diagram shows 30 of 1648 interactions; 1618 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_knowledge_freshness"]
    s2["2. isinstance"]
    s3["3. require_validated_artifacts"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. isinstance"]
    s7["7. TypeError"]
    s8["8. isinstance"]
    s9["9. parse_knowledge_index"]
    s10["10. _record"]
    s11["11. _object"]
    s12["12. dict"]
    s1 -. "isinstance(knowledge, ValidatedKnowledgeArtifacts)" .-> s2
    s1 -->|"require_validated_artifacts(knowledge)"| s3
    s3 -. "isinstance(value, ValidatedKnowledgeArtifacts)" .-> s4
    s3 -. "TypeError('expected validator-issued knowledge artifacts')" .-> s5
    s3 -. "isinstance(validation, _ArtifactValidation)" .-> s6
    s3 -. "TypeError('knowledge artifacts were not issued by the validator or were replaced')" .-> s7
    s1 -. "isinstance(knowledge, KnowledgeIndex)" .-> s8
    s1 -->|"parse_knowledge_index(_knowledge_index_to_payload_unchecked(...))"| s9
    s9 -->|"_record(payload, '', {...}, required={...})"| s10
    s10 -->|"_object(value, ...)"| s11
    s11 -. "dict(require_mapping(...))" .-> s12
    click s1 "../modules/knowledge_freshness.md"
    click s3 "../modules/knowledge_artifacts.md"
    click s9 "../modules/knowledge_model.md"
    click s10 "../modules/knowledge_model.md"
    click s11 "../modules/knowledge_model.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `evaluate_knowledge_freshness` | `knowledge: KnowledgeIndex \| object`, `live: LiveKnowledgeEvaluation \| None` | `KnowledgeIndex`, `KnowledgeModelError` | - | `_evaluate_model_freshness(...)` |
| `isinstance` | - | - | - | - |
| `require_validated_artifacts` | `value: object` | `ValidatedKnowledgeArtifacts`, `_ArtifactValidation` | - | `value` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `parse_knowledge_index` | `payload: object` | `KNOWLEDGE_SCHEMA_VERSION`, `KNOWLEDGE_SCHEMA_VERSION` | - | `model` |
| `_record` | `value: object`, `path: str`, `fields: AbstractSet[str]`, `required: AbstractSet[str]` | - | - | `(...)` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `dict` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluate_knowledge_freshness | isinstance | 235 | `isinstance(knowledge, ValidatedKnowledgeArtifacts)` |
| evaluate_knowledge_freshness | require_validated_artifacts | 234 | `require_validated_artifacts(knowledge)` |
| require_validated_artifacts | isinstance | 152 | `isinstance(value, ValidatedKnowledgeArtifacts)` |
| require_validated_artifacts | TypeError | 153 | `TypeError('expected validator-issued knowledge artifacts')` |
| require_validated_artifacts | isinstance | 156 | `isinstance(validation, _ArtifactValidation)` |
| require_validated_artifacts | TypeError | 167 | `TypeError('knowledge artifacts were not issued by the validator or were replaced')` |
| evaluate_knowledge_freshness | isinstance | 237 | `isinstance(knowledge, KnowledgeIndex)` |
| evaluate_knowledge_freshness | parse_knowledge_index | 236 | `parse_knowledge_index(_knowledge_index_to_payload_unchecked(...))` |
| parse_knowledge_index | _record | 526 | `_record(payload, '', {...}, required={...})` |
| _record | _object | 1581 | `_object(value, ...)` |
| _object | dict | 1667 | `dict(require_mapping(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `evaluate_knowledge_freshness` | `isinstance` | 235 |
| unresolved_call | `require_validated_artifacts` | `isinstance` | 152 |
| unresolved_call | `require_validated_artifacts` | `TypeError` | 153 |
| unresolved_call | `require_validated_artifacts` | `isinstance` | 156 |
| unresolved_call | `require_validated_artifacts` | `TypeError` | 167 |
| unresolved_call | `evaluate_knowledge_freshness` | `isinstance` | 237 |
| step_limit | `evaluate_knowledge_freshness` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_knowledge_freshness` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_knowledge_freshness` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
