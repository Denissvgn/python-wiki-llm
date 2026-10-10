# projection_concept_summary

**Entry point:** `projection_concept_summary` (`api`)
**Source:** [knowledge_projection](../modules/knowledge_projection.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_observability](../modules/knowledge_observability.md), and 2 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as projection_concept_summary
    participant p1 as isinstance (src/llm_wiki_cli/services…rojection_concept_summary)
    participant p2 as TypeError
    participant p3 as _validate_projection_structure
    participant p4 as _projection_concept_summary_unchecked
    participant p5 as isinstance (src/llm_wiki_cli/services…date_projection_structure)
    participant p6 as projection.concept_for_path
    participant p7 as KnowledgeProjectionError
    participant p8 as _mapping
    participant p9 as concept.get
    participant p10 as _require_sha256
    participant p11 as _require_mapping
    participant p12 as _validate_projection_diagnostics
    participant p13 as _validate_projection_bundle
    participant p14 as concepts.items
    participant p15 as _shape_error
    p0-->>p1: isinstance (src/llm_wiki_cli/services…rojection_concept_summary)(projection, KnowledgeProjection)
    p0-->>p2: TypeError('projection must be a KnowledgeProjection')
    p0->>p3: _validate_projection_structure
    p0->>p4: _projection_concept_summary_unchecked
    p3-->>p5: isinstance (src/llm_wiki_cli/services…date_projection_structure)(projection, KnowledgeProjection)
    p4-->>p6: projection.concept_for_path(canonical_path)
    p3->>p7: KnowledgeProjectionError
    p4->>p7: KnowledgeProjectionError
    p3->>p7: KnowledgeProjectionError
    p4->>p8: _mapping
    p3-->>p5: isinstance (src/llm_wiki_cli/services…date_projection_structure)(projection.profile, KnowledgeProjectionProfile)
    p4-->>p9: concept.get('identity')
    p3->>p7: KnowledgeProjectionError
    p4->>p8: _mapping
    p3->>p10: _require_sha256
    p4-->>p9: concept.get('lifecycle')
    p3->>p11: _require_mapping
    p4->>p8: _mapping
    p3->>p11: _require_mapping
    p4-->>p9: concept.get('evidence')
    p3->>p12: _validate_projection_diagnostics
    p4->>p8: _mapping
    p3->>p13: _validate_projection_bundle
    p4-->>p9: concept.get('freshness')
    p3-->>p14: concepts.items
    p4->>p8: _mapping
    p3-->>p5: isinstance (src/llm_wiki_cli/services…date_projection_structure)(raw_path, str)
    p4-->>p9: concept.get('review')
    p3->>p15: _shape_error
    p4->>p8: _mapping
```

> Call sequence diagram shows 30 of 626 interactions; 596 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 161 (156 omitted); unresolved 7 of 117 (110 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_projection.py:_require_sha256` | 10 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 11 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_trimmed_text` | 13 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 14 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 14 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 11 | - | unresolved | 1 |
> Omission summary shows 8 of 127 groups; 119 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. projection_concept_summary"]
    s2["2. isinstance (src/llm_wiki_cli/services…rojection_concept_summary)"]
    s3["3. TypeError"]
    s4["4. _validate_projection_structure"]
    s5["5. isinstance (src/llm_wiki_cli/services…date_projection_structure)"]
    s6["6. KnowledgeProjectionError"]
    s7["7. KnowledgeProjectionError"]
    s8["8. isinstance (src/llm_wiki_cli/services…date_projection_structure)"]
    s9["9. KnowledgeProjectionError"]
    s10["10. _require_sha256"]
    s11["11. require_sha256"]
    s12["12. isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…rojection_concept_summary)(projection, KnowledgeProjection)" .-> s2
    s1 -. "TypeError('projection must be a KnowledgeProjection')" .-> s3
    s1 -->|"_validate_projection_structure(projection)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…date_projection_structure)(projection, KnowledgeProjection)" .-> s5
    s4 -->|"KnowledgeProjectionError('projection-type-invalid', 'projection', 'must be a KnowledgeProjection')"| s6
    s4 -->|"KnowledgeProjectionError('projection-schema-invalid', 'schema_version', ...)"| s7
    s4 -. "isinstance (src/llm_wiki_cli/services…date_projection_structure)(projection.profile, KnowledgeProjectionProfile)" .-> s8
    s4 -->|"KnowledgeProjectionError('projection-profile-invalid', 'profile', #34;must be 'internal' or 'public-portable'#34;)"| s9
    s4 -->|"_require_sha256(projection.source_knowledge_hash, 'source_knowledge_hash', code='projection-source-hash-invalid')"| s10
    s10 -->|"require_sha256(value, digest_error=KnowledgeProjectionError(...))"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)(value, str)" .-> s12
    click s1 "../modules/knowledge_projection.md"
    click s4 "../modules/knowledge_projection.md"
    click s6 "../modules/knowledge_projection.md"
    click s7 "../modules/knowledge_projection.md"
    click s9 "../modules/knowledge_projection.md"
    click s10 "../modules/knowledge_projection.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `projection_concept_summary` | `projection: KnowledgeProjection`, `canonical_path: str` | `KnowledgeProjection` | - | `_projection_concept_summary_unchecked(...)` |
| `isinstance (src/llm_wiki_cli/services…rojection_concept_summary)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_validate_projection_structure` | `projection: KnowledgeProjection` | `KnowledgeProjection`, `PROJECTION_SCHEMA_VERSION`, `PROJECTION_SCHEMA_VERSION`, `KnowledgeProjectionProfile`, `UNEVALUATED_FRESHNESS_DISCLOSURE`, `UNEVALUATED_FRESHNESS_DISCLOSURE` | `concept_by_path[...]` | - |
| `isinstance (src/llm_wiki_cli/services…date_projection_structure)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_projection_structure)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `_require_sha256` | `value: object`, `path: str`, `code: str` | - | - | `require_shared_sha256(...)` |
| `require_sha256` | `value: object`, `digest_error: Exception`, `text_error: Exception \| None`, `reject_control_characters: bool`, `allow_empty: bool` | - | - | `parsed`, `parsed` |
| `isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| projection_concept_summary | isinstance (src/llm_wiki_cli/services…rojection_concept_summary) | 414 | `isinstance(projection, KnowledgeProjection)` |
| projection_concept_summary | TypeError | 415 | `TypeError('projection must be a KnowledgeProjection')` |
| projection_concept_summary | _validate_projection_structure | 416 | `_validate_projection_structure(projection)` |
| _validate_projection_structure | isinstance (src/llm_wiki_cli/services…date_projection_structure) | 808 | `isinstance(projection, KnowledgeProjection)` |
| _validate_projection_structure | KnowledgeProjectionError | 809 | `KnowledgeProjectionError('projection-type-invalid', 'projection', 'must be a KnowledgeProjection')` |
| _validate_projection_structure | KnowledgeProjectionError | 815 | `KnowledgeProjectionError('projection-schema-invalid', 'schema_version', ...)` |
| _validate_projection_structure | isinstance (src/llm_wiki_cli/services…date_projection_structure) | 820 | `isinstance(projection.profile, KnowledgeProjectionProfile)` |
| _validate_projection_structure | KnowledgeProjectionError | 821 | `KnowledgeProjectionError('projection-profile-invalid', 'profile', "must be 'internal' or 'public-portable'")` |
| _validate_projection_structure | _require_sha256 | 826 | `_require_sha256(projection.source_knowledge_hash, 'source_knowledge_hash', code='projection-source-hash-invalid')` |
| _require_sha256 | require_sha256 | 2240 | `require_shared_sha256(value, digest_error=KnowledgeProjectionError(...))` |
| require_sha256 | isinstance (src/llm_wiki_cli/services…idation.py:require_sha256) | 1138 | `isinstance(value, str)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `projection_concept_summary` | `isinstance` | 414 |
| external_call | `projection_concept_summary` | `TypeError` | 415 |
| external_call | `_validate_projection_structure` | `isinstance` | 808 |
| external_call | `_validate_projection_structure` | `isinstance` | 820 |
| external_call | `require_sha256` | `isinstance` | 1138 |
| step_limit | `projection_concept_summary` | `first 12 steps` | 0 |
| truncated_flow | `projection_concept_summary` | `depth limit` | 0 |

## Behavior

This flow starts at `projection_concept_summary` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
