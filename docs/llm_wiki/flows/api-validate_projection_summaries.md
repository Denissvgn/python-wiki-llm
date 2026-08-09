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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_projection_summaries
    participant p1 as isinstance
    participant p2 as KnowledgeProjectionError
    participant p3 as fullmatch
    participant p4 as _validate_projection_structure
    participant p5 as _require_sha256
    participant p6 as require_sha256
    participant p7 as require_trimmed_text
    participant p8 as require_nonempty_text
    participant p9 as strip
    participant p10 as any
    participant p11 as ord
    p0-->>p1: isinstance
    p0->>p2: KnowledgeProjectionError
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance
    p0->>p2: KnowledgeProjectionError
    p0-->>p1: isinstance
    p0-->>p3: fullmatch
    p0->>p2: KnowledgeProjectionError
    p0->>p4: _validate_projection_structure
    p4-->>p1: isinstance
    p4->>p2: KnowledgeProjectionError
    p4->>p2: KnowledgeProjectionError
    p4-->>p1: isinstance
    p4->>p2: KnowledgeProjectionError
    p4->>p5: _require_sha256
    p5->>p6: require_sha256
    p6-->>p1: isinstance
    p6->>p7: require_trimmed_text
    p7->>p8: require_nonempty_text
    p8-->>p1: isinstance
    p8-->>p9: strip
    p8-->>p10: any
    p8-->>p11: ord
    p8-->>p11: ord
    p6-->>p3: fullmatch
    p5->>p2: KnowledgeProjectionError
```

> Call sequence diagram shows 30 of 688 interactions; 658 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_projection_summaries"]
    s2["2. isinstance"]
    s3["3. KnowledgeProjectionError"]
    s4["4. KnowledgeProjectionError"]
    s5["5. isinstance"]
    s6["6. KnowledgeProjectionError"]
    s7["7. isinstance"]
    s8["8. KnowledgeProjectionError"]
    s9["9. isinstance"]
    s10["10. KnowledgeProjectionError"]
    s11["11. isinstance"]
    s12["12. fullmatch"]
    s1 -. "isinstance(projection, KnowledgeProjection)" .-> s2
    s1 -->|"KnowledgeProjectionError('projection-type-invalid', 'projection', 'must be a KnowledgeProjection')"| s3
    s1 -->|"KnowledgeProjectionError('projection-schema-invalid', 'schema_version', ...)"| s4
    s1 -. "isinstance(projection.bundle, Mapping)" .-> s5
    s1 -->|"KnowledgeProjectionError('projection-bundle-invalid', 'bundle', 'must be a mapping')"| s6
    s1 -. "isinstance(projection.concepts, Mapping)" .-> s7
    s1 -->|"KnowledgeProjectionError('projection-concepts-invalid', 'concepts', 'must be a canonical-path mapping')"| s8
    s1 -. "isinstance(projection.profile, KnowledgeProjectionProfile)" .-> s9
    s1 -->|"KnowledgeProjectionError('projection-profile-invalid', 'profile', #34;must be 'internal' or 'public-portable'#34;)"| s10
    s1 -. "isinstance(projection.source_knowledge_hash, str)" .-> s11
    s1 -. "re.fullmatch('sha256:[0-9a-f]{64}', projection.source_knowledge_hash)" .-> s12
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
| `validate_projection_summaries` | `projection: KnowledgeProjection`, `canonical_paths: Sequence[str]` | `KnowledgeProjection`, `PROJECTION_SCHEMA_VERSION`, `PROJECTION_SCHEMA_VERSION`, `Mapping`, `Mapping`, `KnowledgeProjectionProfile`, `Sequence`, `ConceptIdentityError` | `seen_uids[...]`, `summaries[...]` | `summaries` |
| `isinstance` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeProjectionError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_projection_summaries | isinstance | 528 | `isinstance(projection, KnowledgeProjection)` |
| validate_projection_summaries | KnowledgeProjectionError | 529 | `KnowledgeProjectionError('projection-type-invalid', 'projection', 'must be a KnowledgeProjection')` |
| validate_projection_summaries | KnowledgeProjectionError | 535 | `KnowledgeProjectionError('projection-schema-invalid', 'schema_version', ...)` |
| validate_projection_summaries | isinstance | 540 | `isinstance(projection.bundle, Mapping)` |
| validate_projection_summaries | KnowledgeProjectionError | 541 | `KnowledgeProjectionError('projection-bundle-invalid', 'bundle', 'must be a mapping')` |
| validate_projection_summaries | isinstance | 546 | `isinstance(projection.concepts, Mapping)` |
| validate_projection_summaries | KnowledgeProjectionError | 547 | `KnowledgeProjectionError('projection-concepts-invalid', 'concepts', 'must be a canonical-path mapping')` |
| validate_projection_summaries | isinstance | 552 | `isinstance(projection.profile, KnowledgeProjectionProfile)` |
| validate_projection_summaries | KnowledgeProjectionError | 553 | `KnowledgeProjectionError('projection-profile-invalid', 'profile', "must be 'internal' or 'public-portable'")` |
| validate_projection_summaries | isinstance | 559 | `isinstance(projection.source_knowledge_hash, str)` |
| validate_projection_summaries | fullmatch | 560 | `re.fullmatch('sha256:[0-9a-f]{64}', projection.source_knowledge_hash)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `details.append` | `validate_projection_summaries` | 596 |
| mutation | `details.append` | `validate_projection_summaries` | 598 |
| mutation | `allowed_identity_sources.add` | `validate_projection_summaries` | 622 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_projection_summaries` | `isinstance` | 528 |
| unresolved_call | `validate_projection_summaries` | `isinstance` | 540 |
| unresolved_call | `validate_projection_summaries` | `isinstance` | 546 |
| unresolved_call | `validate_projection_summaries` | `isinstance` | 552 |
| unresolved_call | `validate_projection_summaries` | `isinstance` | 559 |
| external_call | `validate_projection_summaries` | `re.fullmatch` | 560 |
| step_limit | `validate_projection_summaries` | `first 12 steps` | 0 |
| truncated_flow | `validate_projection_summaries` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_projection_summaries` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
