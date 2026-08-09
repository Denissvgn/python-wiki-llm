# project_knowledge

**Entry point:** `project_knowledge` (`api`)
**Source:** [knowledge_projection](../modules/knowledge_projection.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 13 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as project_knowledge
    participant p1 as _projection_profile
    participant p2 as isinstance
    participant p3 as KnowledgeProjectionProfile
    participant p4 as KnowledgeProjectionError
    participant p5 as _relationship_limit
    participant p6 as _validated_source
    participant p7 as TypeError
    participant p8 as encode
    participant p9 as dumps
    participant p10 as dict
    participant p11 as serialize_knowledge_index
    participant p12 as knowledge_index_to_payload
    participant p13 as _emit_extensions
    participant p14 as _parse_extensions
    participant p15 as _object
    participant p16 as sorted
    participant p17 as fullmatch
    participant p18 as KnowledgeModelError
    participant p19 as _child
    participant p20 as _normalize_json_value
    p0->>p1: _projection_profile
    p1-->>p2: isinstance
    p1->>p3: KnowledgeProjectionProfile
    p1->>p4: KnowledgeProjectionError
    p0->>p5: _relationship_limit
    p5-->>p2: isinstance
    p5-->>p2: isinstance
    p5->>p4: KnowledgeProjectionError
    p0->>p6: _validated_source
    p6-->>p2: isinstance
    p6-->>p7: TypeError
    p6->>p4: KnowledgeProjectionError
    p6->>p4: KnowledgeProjectionError
    p6-->>p8: encode
    p6-->>p9: dumps
    p6-->>p10: dict
    p6-->>p8: encode
    p6->>p11: serialize_knowledge_index
    p11-->>p9: dumps
    p11->>p12: knowledge_index_to_payload
    p12-->>p2: isinstance
    p12-->>p7: TypeError
    p12->>p13: _emit_extensions
    p13->>p14: _parse_extensions
    p14->>p15: _object
    p14-->>p16: sorted
    p14-->>p17: fullmatch
    p14->>p18: KnowledgeModelError
    p14->>p19: _child
    p14->>p20: _normalize_json_value
```

> Call sequence diagram shows 30 of 1633 interactions; 1603 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. project_knowledge"]
    s2["2. _projection_profile"]
    s3["3. isinstance"]
    s4["4. KnowledgeProjectionProfile"]
    s5["5. KnowledgeProjectionError"]
    s6["6. _relationship_limit"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. KnowledgeProjectionError"]
    s10["10. _validated_source"]
    s11["11. isinstance"]
    s12["12. TypeError"]
    s1 -->|"_projection_profile(profile)"| s2
    s2 -. "isinstance(value, KnowledgeProjectionProfile)" .-> s3
    s2 -->|"KnowledgeProjectionProfile(value)"| s4
    s2 -->|"KnowledgeProjectionError('projection-profile-invalid', 'profile', #34;must be 'internal' or 'public-portable'#34;)"| s5
    s1 -->|"_relationship_limit(relationship_limit)"| s6
    s6 -. "isinstance(value, bool)" .-> s7
    s6 -. "isinstance(value, int)" .-> s8
    s6 -->|"KnowledgeProjectionError('projection-limit-invalid', 'relationship_limit', ...)"| s9
    s1 -->|"_validated_source(view)"| s10
    s10 -. "isinstance(view, KnowledgeReadView)" .-> s11
    s10 -. "TypeError('view must be a KnowledgeReadView')" .-> s12
    click s1 "../modules/knowledge_projection.md"
    click s2 "../modules/knowledge_projection.md"
    click s4 "../modules/knowledge_model.md"
    click s5 "../modules/knowledge_projection.md"
    click s6 "../modules/knowledge_projection.md"
    click s9 "../modules/knowledge_projection.md"
    click s10 "../modules/knowledge_projection.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `project_knowledge` | `view: KnowledgeReadView`, `profile: KnowledgeProjectionProfile \| str`, `relationship_limit: int`, `public_repository_identity: str \| None` | `UNKNOWN_VALUE`, `Mapping`, `PROJECTION_SCHEMA_VERSION` | `projected_concepts[...]` | `projection` |
| `_projection_profile` | `value: KnowledgeProjectionProfile \| str` | `KnowledgeProjectionProfile` | - | `...` |
| `isinstance` | - | - | - | - |
| `KnowledgeProjectionProfile` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `_relationship_limit` | `value: object` | `MAX_RELATIONSHIP_LIMIT`, `MAX_RELATIONSHIP_LIMIT` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `_validated_source` | `view: KnowledgeReadView` | `KnowledgeReadView`, `KnowledgeAvailability` | - | `(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| project_knowledge | _projection_profile | 288 | `_projection_profile(profile)` |
| _projection_profile | isinstance | 3477 | `isinstance(value, KnowledgeProjectionProfile)` |
| _projection_profile | KnowledgeProjectionProfile | 3478 | `KnowledgeProjectionProfile(value)` |
| _projection_profile | KnowledgeProjectionError | 3481 | `KnowledgeProjectionError('projection-profile-invalid', 'profile', "must be 'internal' or 'public-portable'")` |
| project_knowledge | _relationship_limit | 289 | `_relationship_limit(relationship_limit)` |
| _relationship_limit | isinstance | 3490 | `isinstance(value, bool)` |
| _relationship_limit | isinstance | 3491 | `isinstance(value, int)` |
| _relationship_limit | KnowledgeProjectionError | 3494 | `KnowledgeProjectionError('projection-limit-invalid', 'relationship_limit', ...)` |
| project_knowledge | _validated_source | 290 | `_validated_source(view)` |
| _validated_source | isinstance | 2257 | `isinstance(view, KnowledgeReadView)` |
| _validated_source | TypeError | 2258 | `TypeError('view must be a KnowledgeReadView')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_projection_profile` | `isinstance` | 3477 |
| unresolved_call | `_relationship_limit` | `isinstance` | 3490 |
| unresolved_call | `_relationship_limit` | `isinstance` | 3491 |
| unresolved_call | `_validated_source` | `isinstance` | 2257 |
| unresolved_call | `_validated_source` | `TypeError` | 2258 |
| step_limit | `project_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `project_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `project_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
