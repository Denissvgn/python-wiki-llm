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
    participant p1 as isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)
    participant p2 as require_validated_artifacts
    participant p3 as isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)
    participant p4 as TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)
    participant p5 as parse_knowledge_index
    participant p6 as _record
    participant p7 as _object (src/llm_wiki_cli/services/knowledge_model.py)
    participant p8 as dict (src/llm_wiki_cli/services…nowledge_model.py:_object)
    participant p9 as require_mapping
    participant p10 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p11 as key.encode
    participant p12 as KnowledgeModelError
    participant p13 as sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)
    participant p14 as set (src/llm_wiki_cli/services…nowledge_model.py:_record)
    participant p15 as _child
    participant p16 as _parse_extensions
    participant p17 as sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    participant p18 as _QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)
    p0->>p2: require_validated_artifacts
    p2-->>p3: isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)
    p2-->>p4: TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)
    p2-->>p3: isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)
    p2-->>p4: TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)
    p0->>p5: parse_knowledge_index
    p5->>p6: _record
    p6->>p7: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p7-->>p8: dict (src/llm_wiki_cli/services…nowledge_model.py:_object)
    p7->>p9: require_mapping
    p9-->>p10: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p9-->>p10: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p9-->>p11: key.encode
    p7->>p12: KnowledgeModelError
    p7->>p12: KnowledgeModelError
    p7->>p12: KnowledgeModelError
    p6-->>p13: sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p6-->>p14: set (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p6->>p12: KnowledgeModelError
    p6->>p15: _child
    p6-->>p13: sorted (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p6-->>p14: set (src/llm_wiki_cli/services…nowledge_model.py:_record)
    p6->>p12: KnowledgeModelError
    p6->>p15: _child
    p6->>p16: _parse_extensions
    p16->>p7: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p16-->>p17: sorted (src/llm_wiki_cli/services…odel.py:_parse_extensions)
    p16-->>p18: _QUALIFIED_NAME_RE.fullmatch (src/llm_wiki_cli/services…odel.py:_parse_extensions)
```

> Call sequence diagram shows 30 of 1663 interactions; 1633 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_knowledge_freshness"]
    s2["2. isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)"]
    s3["3. require_validated_artifacts"]
    s4["4. isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s5["5. TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s6["6. isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s7["7. TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s8["8. isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)"]
    s9["9. parse_knowledge_index"]
    s10["10. _record"]
    s11["11. _object (src/llm_wiki_cli/services/knowledge_model.py)"]
    s12["12. dict (src/llm_wiki_cli/services…nowledge_model.py:_object)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)(knowledge, ValidatedKnowledgeArtifacts)" .-> s2
    s1 -->|"require_validated_artifacts(knowledge)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)(value, ValidatedKnowledgeArtifacts)" .-> s4
    s3 -. "TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)('expected validator-issued knowledge artifacts')" .-> s5
    s3 -. "isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)(validation, _ArtifactValidation)" .-> s6
    s3 -. "TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)('knowledge artifacts were not issued by the validator or were replaced')" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)(knowledge, KnowledgeIndex)" .-> s8
    s1 -->|"parse_knowledge_index(_knowledge_index_to_payload_unchecked(...))"| s9
    s9 -->|"_record(payload, '', {...}, required={...})"| s10
    s10 -->|"_object (src/llm_wiki_cli/services/knowledge_model.py)(value, ...)"| s11
    s11 -. "dict (src/llm_wiki_cli/services…nowledge_model.py:_object)(require_mapping(...))" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)` | - | - | - | - |
| `require_validated_artifacts` | `value: object` | `ValidatedKnowledgeArtifacts`, `_ArtifactValidation` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness)` | - | - | - | - |
| `parse_knowledge_index` | `payload: object` | `KNOWLEDGE_SCHEMA_VERSION`, `KNOWLEDGE_SCHEMA_VERSION` | - | `model` |
| `_record` | `value: object`, `path: str`, `fields: AbstractSet[str]`, `required: AbstractSet[str]` | - | - | `(...)` |
| `_object (src/llm_wiki_cli/services/knowledge_model.py)` | `value: object`, `path: str` | - | - | `dict(...)` |
| `dict (src/llm_wiki_cli/services…nowledge_model.py:_object)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluate_knowledge_freshness | isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness) | 235 | `isinstance(knowledge, ValidatedKnowledgeArtifacts)` |
| evaluate_knowledge_freshness | require_validated_artifacts | 234 | `require_validated_artifacts(knowledge)` |
| require_validated_artifacts | isinstance (src/llm_wiki_cli/services…quire_validated_artifacts) | 152 | `isinstance(value, ValidatedKnowledgeArtifacts)` |
| require_validated_artifacts | TypeError (src/llm_wiki_cli/services…quire_validated_artifacts) | 153 | `TypeError('expected validator-issued knowledge artifacts')` |
| require_validated_artifacts | isinstance (src/llm_wiki_cli/services…quire_validated_artifacts) | 156 | `isinstance(validation, _ArtifactValidation)` |
| require_validated_artifacts | TypeError (src/llm_wiki_cli/services…quire_validated_artifacts) | 167 | `TypeError('knowledge artifacts were not issued by the validator or were replaced')` |
| evaluate_knowledge_freshness | isinstance (src/llm_wiki_cli/services…luate_knowledge_freshness) | 237 | `isinstance(knowledge, KnowledgeIndex)` |
| evaluate_knowledge_freshness | parse_knowledge_index | 236 | `parse_knowledge_index(_knowledge_index_to_payload_unchecked(...))` |
| parse_knowledge_index | _record | 526 | `_record(payload, '', {...}, required={...})` |
| _record | _object (src/llm_wiki_cli/services/knowledge_model.py) | 1581 | `_object(value, ...)` |
| _object (src/llm_wiki_cli/services/knowledge_model.py) | dict (src/llm_wiki_cli/services…nowledge_model.py:_object) | 1667 | `dict(require_mapping(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `evaluate_knowledge_freshness` | `isinstance` | 235 |
| external_call | `require_validated_artifacts` | `isinstance` | 152 |
| external_call | `require_validated_artifacts` | `TypeError` | 153 |
| external_call | `require_validated_artifacts` | `isinstance` | 156 |
| external_call | `require_validated_artifacts` | `TypeError` | 167 |
| external_call | `evaluate_knowledge_freshness` | `isinstance` | 237 |
| step_limit | `evaluate_knowledge_freshness` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_knowledge_freshness` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_knowledge_freshness` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
