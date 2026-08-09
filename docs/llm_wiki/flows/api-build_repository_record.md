# build_repository_record

**Entry point:** `build_repository_record` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_model](../modules/knowledge_model.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_repository_record
    participant p1 as RepositoryEvidence
    participant p2 as isinstance
    participant p3 as KnowledgeEnvelopeError
    participant p4 as select_repository_identity
    participant p5 as validate_configured_public_identity
    participant p6 as strip
    participant p7 as fullmatch
    participant p8 as endswith
    participant p9 as casefold
    participant p10 as _remote_mapping
    participant p11 as items
    participant p12 as len
    participant p13 as next
    participant p14 as iter
    participant p15 as get
    participant p16 as normalize_vcs_remote
    p0->>p1: RepositoryEvidence
    p0-->>p2: isinstance
    p0->>p3: KnowledgeEnvelopeError
    p0-->>p2: isinstance
    p0->>p3: KnowledgeEnvelopeError
    p0->>p4: select_repository_identity
    p4->>p5: validate_configured_public_identity
    p5-->>p2: isinstance
    p5->>p3: KnowledgeEnvelopeError
    p5-->>p6: strip
    p5-->>p7: fullmatch
    p5-->>p8: endswith
    p5-->>p9: casefold
    p5->>p3: KnowledgeEnvelopeError
    p4->>p10: _remote_mapping
    p10-->>p2: isinstance
    p10->>p3: KnowledgeEnvelopeError
    p10-->>p11: items
    p10-->>p2: isinstance
    p10->>p3: KnowledgeEnvelopeError
    p10-->>p2: isinstance
    p10->>p3: KnowledgeEnvelopeError
    p4-->>p12: len
    p4-->>p13: next
    p4-->>p14: iter
    p4-->>p15: get
    p4-->>p2: isinstance
    p4->>p16: normalize_vcs_remote
    p16-->>p2: isinstance
    p16-->>p6: strip
```

> Call sequence diagram shows 30 of 71 interactions; 41 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_repository_record"]
    s2["2. RepositoryEvidence"]
    s3["3. isinstance"]
    s4["4. KnowledgeEnvelopeError"]
    s5["5. isinstance"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. select_repository_identity"]
    s8["8. validate_configured_public_identity"]
    s9["9. isinstance"]
    s10["10. KnowledgeEnvelopeError"]
    s11["11. strip"]
    s12["12. fullmatch"]
    s1 -->|"RepositoryEvidence(data not statically known)"| s2
    s1 -. "isinstance(current.remotes_evaluated, bool)" .-> s3
    s1 -->|"KnowledgeEnvelopeError('remotes_evaluated', 'must be a boolean')"| s4
    s1 -. "isinstance(current.upstream_remote_evaluated, bool)" .-> s5
    s1 -->|"KnowledgeEnvelopeError('upstream_remote_evaluated', 'must be a boolean')"| s6
    s1 -->|"select_repository_identity(configured_public_identity=configured_public_identity, vcs_remotes=current.remotes, upstream_remote=current.upstream_remote)"| s7
    s7 -->|"validate_configured_public_identity(configured_public_identity)"| s8
    s8 -. "isinstance(value, str)" .-> s9
    s8 -->|"KnowledgeEnvelopeError('configured_public_identity', 'must be a qualified public namespace path')"| s10
    s8 -. "value.strip(data not statically known)" .-> s11
    s8 -. "_REPOSITORY_IDENTITY_RE.fullmatch(value)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s2 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_repository_record` | `configured_public_identity: str \| None`, `evidence: RepositoryEvidence \| None` | `RepositoryIdentitySource`, `RepositoryIdentitySource` | `extensions[...]` | `RepositoryRecord(...)` |
| `RepositoryEvidence` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `select_repository_identity` | `configured_public_identity: str \| None`, `vcs_remotes: Mapping[str, str \| None]`, `upstream_remote: str \| None` | `RepositoryIdentitySource`, `RepositoryIdentitySource`, `RepositoryIdentitySource`, `RepositoryIdentitySource` | - | `(...)`, `(...)`, `(...)`, `(...)` |
| `validate_configured_public_identity` | `value: object` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `strip` | - | - | - | - |
| `fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_repository_record | RepositoryEvidence | 606 | `RepositoryEvidence(data not statically known)` |
| build_repository_record | isinstance | 607 | `isinstance(current.remotes_evaluated, bool)` |
| build_repository_record | KnowledgeEnvelopeError | 608 | `KnowledgeEnvelopeError('remotes_evaluated', 'must be a boolean')` |
| build_repository_record | isinstance | 612 | `isinstance(current.upstream_remote_evaluated, bool)` |
| build_repository_record | KnowledgeEnvelopeError | 613 | `KnowledgeEnvelopeError('upstream_remote_evaluated', 'must be a boolean')` |
| build_repository_record | select_repository_identity | 622 | `select_repository_identity(configured_public_identity=configured_public_identity, vcs_remotes=current.remotes, upstream_remote=current.upstream_remote)` |
| select_repository_identity | validate_configured_public_identity | 649 | `validate_configured_public_identity(configured_public_identity)` |
| validate_configured_public_identity | isinstance | 678 | `isinstance(value, str)` |
| validate_configured_public_identity | KnowledgeEnvelopeError | 679 | `KnowledgeEnvelopeError('configured_public_identity', 'must be a qualified public namespace path')` |
| validate_configured_public_identity | strip | 684 | `value.strip(data not statically known)` |
| validate_configured_public_identity | fullmatch | 685 | `_REPOSITORY_IDENTITY_RE.fullmatch(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_repository_record` | `isinstance` | 607 |
| unresolved_call | `build_repository_record` | `isinstance` | 612 |
| unresolved_call | `validate_configured_public_identity` | `isinstance` | 678 |
| unresolved_call | `validate_configured_public_identity` | `value.strip` | 684 |
| unresolved_call | `validate_configured_public_identity` | `_REPOSITORY_IDENTITY_RE.fullmatch` | 685 |
| step_limit | `build_repository_record` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_repository_record` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
