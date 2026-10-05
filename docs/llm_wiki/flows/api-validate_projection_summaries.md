# validate_projection_summaries

**Entry point:** `validate_projection_summaries` (`api`)
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
    participant p0 as validate_projection_summaries
    participant p1 as isinstance (src/llm_wiki_cli/services…date_projection_summaries)
    participant p2 as KnowledgeProjectionError
    participant p3 as re.fullmatch (src/llm_wiki_cli/services…date_projection_summaries)
    participant p4 as _validate_projection_structure
    participant p5 as any (src/llm_wiki_cli/services…date_projection_summaries)
    participant p6 as set (src/llm_wiki_cli/services…date_projection_summaries)
    participant p7 as len (src/llm_wiki_cli/services…date_projection_summaries)
    participant p8 as sorted (src/llm_wiki_cli/services…date_projection_summaries)
    participant p9 as details.append
    participant p10 as ','.join
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection, KnowledgeProjection)
    p0->>p2: KnowledgeProjectionError
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.bundle, Mapping)
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.concepts, Mapping)
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.profile, KnowledgeProjectionProfile)
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.source_knowledge_hash, str)
    p0-->>p3: re.fullmatch (src/llm_wiki_cli/services…date_projection_summaries)('sha256:[0-9a-f]{64}', projection.source_knowledge_hash)
    p0->>p2: KnowledgeProjectionError
    p0->>p4: _validate_projection_structure
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(canonical_paths, (...))
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(canonical_paths, Sequence)
    p0-->>p5: any (src/llm_wiki_cli/services…date_projection_summaries)(...)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…date_projection_summaries)(path, str)
    p0->>p2: KnowledgeProjectionError
    p0-->>p6: set (src/llm_wiki_cli/services…date_projection_summaries)(canonical_paths)
    p0-->>p7: len (src/llm_wiki_cli/services…date_projection_summaries)(expected_paths)
    p0-->>p7: len (src/llm_wiki_cli/services…date_projection_summaries)(canonical_paths)
    p0->>p2: KnowledgeProjectionError
    p0-->>p6: set (src/llm_wiki_cli/services…date_projection_summaries)(projection.concepts)
    p0-->>p8: sorted (src/llm_wiki_cli/services…date_projection_summaries)(...)
    p0-->>p8: sorted (src/llm_wiki_cli/services…date_projection_summaries)(...)
    p0-->>p9: details.append(...)
    p0-->>p10: ','.join(missing)
    p0-->>p9: details.append(...)
    p0-->>p10: ','.join(stale)
    p0->>p2: KnowledgeProjectionError
```

> Call sequence diagram shows 30 of 700 interactions; 670 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 183 (167 omitted); unresolved 4 of 137 (133 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_projection.py:_validate_projection_structure` | 14 | - | external | 6 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_validate_projection_structure` | 14 | [src/llm_wiki_cli/services/knowledge_projection.py](../modules/knowledge_projection.md) | internal | 20 |
| `src/llm_wiki_cli/services/knowledge_projection.py:_require_sha256` | 20 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 21 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 21 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_trimmed_text` | 23 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 24 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 24 | - | unresolved | 1 |
> Omission summary shows 8 of 132 groups; 124 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_projection_summaries"]
    s2["2. isinstance (src/llm_wiki_cli/services…date_projection_summaries)"]
    s3["3. KnowledgeProjectionError"]
    s4["4. KnowledgeProjectionError"]
    s5["5. isinstance (src/llm_wiki_cli/services…date_projection_summaries)"]
    s6["6. KnowledgeProjectionError"]
    s7["7. isinstance (src/llm_wiki_cli/services…date_projection_summaries)"]
    s8["8. KnowledgeProjectionError"]
    s9["9. isinstance (src/llm_wiki_cli/services…date_projection_summaries)"]
    s10["10. KnowledgeProjectionError"]
    s11["11. isinstance (src/llm_wiki_cli/services…date_projection_summaries)"]
    s12["12. re.fullmatch (src/llm_wiki_cli/services…date_projection_summaries)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection, KnowledgeProjection)" .-> s2
    s1 -->|"KnowledgeProjectionError('projection-type-invalid', 'projection', 'must be a KnowledgeProjection')"| s3
    s1 -->|"KnowledgeProjectionError('projection-schema-invalid', 'schema_version', ...)"| s4
    s1 -. "isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.bundle, Mapping)" .-> s5
    s1 -->|"KnowledgeProjectionError('projection-bundle-invalid', 'bundle', 'must be a mapping')"| s6
    s1 -. "isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.concepts, Mapping)" .-> s7
    s1 -->|"KnowledgeProjectionError('projection-concepts-invalid', 'concepts', 'must be a canonical-path mapping')"| s8
    s1 -. "isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.profile, KnowledgeProjectionProfile)" .-> s9
    s1 -->|"KnowledgeProjectionError('projection-profile-invalid', 'profile', #34;must be 'internal' or 'public-portable'#34;)"| s10
    s1 -. "isinstance (src/llm_wiki_cli/services…date_projection_summaries)(projection.source_knowledge_hash, str)" .-> s11
    s1 -. "re.fullmatch (src/llm_wiki_cli/services…date_projection_summaries)('sha256:[0-9a-f]{64}', projection.source_knowledge_hash)" .-> s12
    b0["mutation details.append"]
    s1 -. "mutation details.append" .-> b0
    b1["mutation details.append"]
    s1 -. "mutation details.append" .-> b1
    b2["mutation allowed_identity_sources.add"]
    s1 -. "mutation allowed_identity_sources.add" .-> b2
    click s1 "../modules/knowledge_projection.md"
    click s3 "../modules/knowledge_projection.md"
    click s4 "../modules/knowledge_projection.md"
    click s6 "../modules/knowledge_projection.md"
    click s8 "../modules/knowledge_projection.md"
    click s10 "../modules/knowledge_projection.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_projection_summaries` | `projection: KnowledgeProjection`, `canonical_paths: Sequence[str]` | `KnowledgeProjection`, `PROJECTION_SCHEMA_VERSION`, `PROJECTION_SCHEMA_VERSION`, `Mapping`, `Mapping`, `KnowledgeProjectionProfile`, `Sequence`, `UNKNOWN_VALUE` | `seen_uids[...]`, `summaries[...]` | `summaries` |
| `isinstance (src/llm_wiki_cli/services…date_projection_summaries)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_projection_summaries)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_projection_summaries)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_projection_summaries)` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…date_projection_summaries)` | - | - | - | - |
| `re.fullmatch (src/llm_wiki_cli/services…date_projection_summaries)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_projection_summaries | isinstance (src/llm_wiki_cli/services…date_projection_summaries) | 528 | `isinstance(projection, KnowledgeProjection)` |
| validate_projection_summaries | KnowledgeProjectionError | 529 | `KnowledgeProjectionError('projection-type-invalid', 'projection', 'must be a KnowledgeProjection')` |
| validate_projection_summaries | KnowledgeProjectionError | 535 | `KnowledgeProjectionError('projection-schema-invalid', 'schema_version', ...)` |
| validate_projection_summaries | isinstance (src/llm_wiki_cli/services…date_projection_summaries) | 540 | `isinstance(projection.bundle, Mapping)` |
| validate_projection_summaries | KnowledgeProjectionError | 541 | `KnowledgeProjectionError('projection-bundle-invalid', 'bundle', 'must be a mapping')` |
| validate_projection_summaries | isinstance (src/llm_wiki_cli/services…date_projection_summaries) | 546 | `isinstance(projection.concepts, Mapping)` |
| validate_projection_summaries | KnowledgeProjectionError | 547 | `KnowledgeProjectionError('projection-concepts-invalid', 'concepts', 'must be a canonical-path mapping')` |
| validate_projection_summaries | isinstance (src/llm_wiki_cli/services…date_projection_summaries) | 552 | `isinstance(projection.profile, KnowledgeProjectionProfile)` |
| validate_projection_summaries | KnowledgeProjectionError | 553 | `KnowledgeProjectionError('projection-profile-invalid', 'profile', "must be 'internal' or 'public-portable'")` |
| validate_projection_summaries | isinstance (src/llm_wiki_cli/services…date_projection_summaries) | 559 | `isinstance(projection.source_knowledge_hash, str)` |
| validate_projection_summaries | re.fullmatch (src/llm_wiki_cli/services…date_projection_summaries) | 560 | `re.fullmatch('sha256:[0-9a-f]{64}', projection.source_knowledge_hash)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `details.append` | `validate_projection_summaries` | 596 |
| mutation | `details.append` | `validate_projection_summaries` | 598 |
| mutation | `allowed_identity_sources.add` | `validate_projection_summaries` | 627 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_projection_summaries` | `isinstance` | 528 |
| external_call | `validate_projection_summaries` | `isinstance` | 540 |
| external_call | `validate_projection_summaries` | `isinstance` | 546 |
| external_call | `validate_projection_summaries` | `isinstance` | 552 |
| external_call | `validate_projection_summaries` | `isinstance` | 559 |
| external_call | `validate_projection_summaries` | `re.fullmatch` | 560 |
| step_limit | `validate_projection_summaries` | `first 12 steps` | 0 |
| truncated_flow | `validate_projection_summaries` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_projection_summaries` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
