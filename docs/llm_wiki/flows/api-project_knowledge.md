# project_knowledge

**Entry point:** `project_knowledge` (`api`)
**Source:** [knowledge_projection](../modules/knowledge_projection.md)
**Modules touched:** [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [filesystem_guard](../modules/filesystem_guard.md), [immutable](../modules/immutable.md), and 24 more

**Complete modules touched:**

- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [progress](../modules/progress.md)
- [section_ownership](../modules/section_ownership.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as project_knowledge
    participant p1 as _projection_profile
    participant p2 as _relationship_limit
    participant p3 as _validated_source
    participant p4 as _approved_public_repository_identity
    participant p5 as validate_governance_projection
    participant p6 as str (src/llm_wiki_cli/services…tion.py:project_knowledge)
    participant p7 as _initial_omitted_counts
    participant p8 as _governance_summary
    participant p9 as governance_by_locator.items
    participant p10 as isinstance (src/llm_wiki_cli/services…tion.py:project_knowledge)
    participant p11 as summary.get (src/llm_wiki_cli/services…tion.py:project_knowledge)
    participant p12 as _project_relationships
    participant p13 as sorted (src/llm_wiki_cli/services…tion.py:project_knowledge)
    participant p14 as _project_concept
    participant p15 as relation_sets.get
    participant p16 as _empty_relationships
    participant p17 as KnowledgeProjectionError
    participant p18 as MappingProxyType (src/llm_wiki_cli/services…tion.py:project_knowledge)
    participant p19 as _project_bundle
    participant p20 as _projection_warnings
    participant p21 as KnowledgeProjection
    participant p22 as omitted.items (src/llm_wiki_cli/services…tion.py:project_knowledge)
    participant p23 as knowledge_freshness_disclosure
    p0->>p1: _projection_profile
    p0->>p2: _relationship_limit
    p0->>p3: _validated_source
    p0->>p4: _approved_public_repository_identity
    p0->>p5: validate_governance_projection
    p0-->>p6: str (src/llm_wiki_cli/services…tion.py:project_knowledge)(governance[...])
    p0->>p7: _initial_omitted_counts
    p0->>p8: _governance_summary
    p0-->>p6: str (src/llm_wiki_cli/services…tion.py:project_knowledge)(summary[...])
    p0-->>p9: governance_by_locator.items
    p0-->>p10: isinstance (src/llm_wiki_cli/services…tion.py:project_knowledge)(summary, Mapping)
    p0-->>p10: isinstance (src/llm_wiki_cli/services…tion.py:project_knowledge)(summary.get(...), str)
    p0-->>p11: summary.get (src/llm_wiki_cli/services…tion.py:project_knowledge)('uid')
    p0->>p12: _project_relationships
    p0-->>p13: sorted (src/llm_wiki_cli/services…tion.py:project_knowledge)(knowledge.concepts, key=...)
    p0->>p14: _project_concept
    p0-->>p15: relation_sets.get(concept.locator, _empty_relationships(...))
    p0->>p16: _empty_relationships
    p0->>p17: KnowledgeProjectionError
    p0-->>p18: MappingProxyType (src/llm_wiki_cli/services…tion.py:project_knowledge)(projected)
    p0->>p19: _project_bundle
    p0->>p20: _projection_warnings
    p0->>p21: KnowledgeProjection
    p0-->>p18: MappingProxyType (src/llm_wiki_cli/services…tion.py:project_knowledge)(bundle)
    p0-->>p18: MappingProxyType (src/llm_wiki_cli/services…tion.py:project_knowledge)(...)
    p0-->>p13: sorted (src/llm_wiki_cli/services…tion.py:project_knowledge)(projected_concepts)
    p0-->>p18: MappingProxyType (src/llm_wiki_cli/services…tion.py:project_knowledge)(...)
    p0-->>p13: sorted (src/llm_wiki_cli/services…tion.py:project_knowledge)(omitted.items(...))
    p0-->>p22: omitted.items (src/llm_wiki_cli/services…tion.py:project_knowledge)
    p0->>p23: knowledge_freshness_disclosure
```

> Call sequence diagram shows 30 of 1995 interactions; 1965 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 550 (539 omitted); unresolved 4 of 365 (361 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_projection.py:_projection_profile` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_projection_profile` | 2 | [src/llm_wiki_cli/services/knowledge_model.py](../modules/knowledge_model.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_projection_profile` | 2 | [src/llm_wiki_cli/services/knowledge_projection.py](../modules/knowledge_projection.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_relationship_limit` | 6 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_relationship_limit` | 6 | [src/llm_wiki_cli/services/knowledge_projection.py](../modules/knowledge_projection.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_validated_source` | 10 | - | external | 5 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_validated_source` | 10 | [src/llm_wiki_cli/services/knowledge_projection.py](../modules/knowledge_projection.md) | internal | 6 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_validated_source` | 10 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 2 |
> Omission summary shows 8 of 458 groups; 450 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. project_knowledge"]
    s2["2. _projection_profile"]
    s3["3. isinstance (src/llm_wiki_cli/services…on.py:_projection_profile)"]
    s4["4. KnowledgeProjectionProfile"]
    s5["5. KnowledgeProjectionError"]
    s6["6. _relationship_limit"]
    s7["7. isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit)"]
    s8["8. isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit)"]
    s9["9. KnowledgeProjectionError"]
    s10["10. _validated_source"]
    s11["11. isinstance (src/llm_wiki_cli/services…tion.py:_validated_source)"]
    s12["12. TypeError (src/llm_wiki_cli/services…tion.py:_validated_source)"]
    s1 -->|"_projection_profile(profile)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…on.py:_projection_profile)(value, KnowledgeProjectionProfile)" .-> s3
    s2 -->|"KnowledgeProjectionProfile(value)"| s4
    s2 -->|"KnowledgeProjectionError('projection-profile-invalid', 'profile', #34;must be 'internal' or 'public-portable'#34;)"| s5
    s1 -->|"_relationship_limit(relationship_limit)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit)(value, bool)" .-> s7
    s6 -. "isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit)(value, int)" .-> s8
    s6 -->|"KnowledgeProjectionError('projection-limit-invalid', 'relationship_limit', ...)"| s9
    s1 -->|"_validated_source(view)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…tion.py:_validated_source)(view, KnowledgeReadView)" .-> s11
    s10 -. "TypeError (src/llm_wiki_cli/services…tion.py:_validated_source)('view must be a KnowledgeReadView')" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…on.py:_projection_profile)` | - | - | - | - |
| `KnowledgeProjectionProfile` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `_relationship_limit` | `value: object` | `MAX_RELATIONSHIP_LIMIT`, `MAX_RELATIONSHIP_LIMIT` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `_validated_source` | `view: KnowledgeReadView` | `KnowledgeReadView`, `KnowledgeAvailability` | - | `(...)`, `(...)` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validated_source)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…tion.py:_validated_source)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| project_knowledge | _projection_profile | 288 | `_projection_profile(profile)` |
| _projection_profile | isinstance (src/llm_wiki_cli/services…on.py:_projection_profile) | 3501 | `isinstance(value, KnowledgeProjectionProfile)` |
| _projection_profile | KnowledgeProjectionProfile | 3502 | `KnowledgeProjectionProfile(value)` |
| _projection_profile | KnowledgeProjectionError | 3505 | `KnowledgeProjectionError('projection-profile-invalid', 'profile', "must be 'internal' or 'public-portable'")` |
| project_knowledge | _relationship_limit | 289 | `_relationship_limit(relationship_limit)` |
| _relationship_limit | isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit) | 3514 | `isinstance(value, bool)` |
| _relationship_limit | isinstance (src/llm_wiki_cli/services…on.py:_relationship_limit) | 3515 | `isinstance(value, int)` |
| _relationship_limit | KnowledgeProjectionError | 3518 | `KnowledgeProjectionError('projection-limit-invalid', 'relationship_limit', ...)` |
| project_knowledge | _validated_source | 290 | `_validated_source(view)` |
| _validated_source | isinstance (src/llm_wiki_cli/services…tion.py:_validated_source) | 2268 | `isinstance(view, KnowledgeReadView)` |
| _validated_source | TypeError (src/llm_wiki_cli/services…tion.py:_validated_source) | 2269 | `TypeError('view must be a KnowledgeReadView')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_projection_profile` | `isinstance` | 3501 |
| external_call | `_relationship_limit` | `isinstance` | 3514 |
| external_call | `_relationship_limit` | `isinstance` | 3515 |
| external_call | `_validated_source` | `isinstance` | 2268 |
| external_call | `_validated_source` | `TypeError` | 2269 |
| step_limit | `project_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `project_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `project_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
