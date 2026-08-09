# select_repository_identity

**Entry point:** `select_repository_identity` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as select_repository_identity
    participant p1 as validate_configured_public_identity
    participant p2 as isinstance
    participant p3 as KnowledgeEnvelopeError
    participant p4 as strip
    participant p5 as fullmatch
    participant p6 as endswith
    participant p7 as casefold
    participant p8 as _remote_mapping
    participant p9 as items
    participant p10 as len
    participant p11 as next
    participant p12 as iter
    participant p13 as get
    participant p14 as normalize_vcs_remote
    participant p15 as any
    participant p16 as ord
    participant p17 as startswith
    participant p18 as match
    participant p19 as search
    participant p20 as _normalize_scheme_remote
    p0->>p1: validate_configured_public_identity
    p1-->>p2: isinstance
    p1->>p3: KnowledgeEnvelopeError
    p1-->>p4: strip
    p1-->>p5: fullmatch
    p1-->>p6: endswith
    p1-->>p7: casefold
    p1->>p3: KnowledgeEnvelopeError
    p0->>p8: _remote_mapping
    p8-->>p2: isinstance
    p8->>p3: KnowledgeEnvelopeError
    p8-->>p9: items
    p8-->>p2: isinstance
    p8->>p3: KnowledgeEnvelopeError
    p8-->>p2: isinstance
    p8->>p3: KnowledgeEnvelopeError
    p0-->>p10: len
    p0-->>p11: next
    p0-->>p12: iter
    p0-->>p13: get
    p0-->>p2: isinstance
    p0->>p14: normalize_vcs_remote
    p14-->>p2: isinstance
    p14-->>p4: strip
    p14-->>p15: any
    p14-->>p16: ord
    p14-->>p17: startswith
    p14-->>p18: match
    p14-->>p19: search
    p14->>p20: _normalize_scheme_remote
```

> Call sequence diagram shows 30 of 54 interactions; 24 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. select_repository_identity"]
    s2["2. validate_configured_public_identity"]
    s3["3. isinstance"]
    s4["4. KnowledgeEnvelopeError"]
    s5["5. strip"]
    s6["6. fullmatch"]
    s7["7. endswith"]
    s8["8. casefold"]
    s9["9. KnowledgeEnvelopeError"]
    s10["10. _remote_mapping"]
    s11["11. isinstance"]
    s12["12. KnowledgeEnvelopeError"]
    s1 -->|"validate_configured_public_identity(configured_public_identity)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -->|"KnowledgeEnvelopeError('configured_public_identity', 'must be a qualified public namespace path')"| s4
    s2 -. "value.strip(data not statically known)" .-> s5
    s2 -. "_REPOSITORY_IDENTITY_RE.fullmatch(value)" .-> s6
    s2 -. "value.casefold().endswith('.git')" .-> s7
    s2 -. "value.casefold(data not statically known)" .-> s8
    s2 -->|"KnowledgeEnvelopeError('configured_public_identity', #34;must be a normalized public namespace path without scheme, credentials, port, query, fragment, dot segmen…"| s9
    s1 -->|"_remote_mapping(vcs_remotes)"| s10
    s10 -. "isinstance(value, Mapping)" .-> s11
    s10 -->|"KnowledgeEnvelopeError('vcs_remotes', 'must be an object')"| s12
    click s1 "../modules/knowledge_envelope.md"
    click s2 "../modules/knowledge_envelope.md"
    click s4 "../modules/knowledge_envelope.md"
    click s9 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `select_repository_identity` | `configured_public_identity: str \| None`, `vcs_remotes: Mapping[str, str \| None]`, `upstream_remote: str \| None` | `RepositoryIdentitySource`, `RepositoryIdentitySource`, `RepositoryIdentitySource`, `RepositoryIdentitySource` | - | `(...)`, `(...)`, `(...)`, `(...)` |
| `validate_configured_public_identity` | `value: object` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `strip` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `endswith` | - | - | - | - |
| `casefold` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_remote_mapping` | `value: Mapping[str, str \| None]` | `Mapping` | `result[...]` | `result` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| select_repository_identity | validate_configured_public_identity | 656 | `validate_configured_public_identity(configured_public_identity)` |
| validate_configured_public_identity | isinstance | 685 | `isinstance(value, str)` |
| validate_configured_public_identity | KnowledgeEnvelopeError | 686 | `KnowledgeEnvelopeError('configured_public_identity', 'must be a qualified public namespace path')` |
| validate_configured_public_identity | strip | 691 | `value.strip(data not statically known)` |
| validate_configured_public_identity | fullmatch | 692 | `_REPOSITORY_IDENTITY_RE.fullmatch(value)` |
| validate_configured_public_identity | endswith | 693 | `value.casefold().endswith('.git')` |
| validate_configured_public_identity | casefold | 693 | `value.casefold(data not statically known)` |
| validate_configured_public_identity | KnowledgeEnvelopeError | 695 | `KnowledgeEnvelopeError('configured_public_identity', "must be a normalized public namespace path without scheme, credentials, port, query, fragment, dot segment, or '.git' suffix")` |
| select_repository_identity | _remote_mapping | 661 | `_remote_mapping(vcs_remotes)` |
| _remote_mapping | isinstance | 1414 | `isinstance(value, Mapping)` |
| _remote_mapping | KnowledgeEnvelopeError | 1415 | `KnowledgeEnvelopeError('vcs_remotes', 'must be an object')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_configured_public_identity` | `isinstance` | 685 |
| unresolved_call | `validate_configured_public_identity` | `value.strip` | 691 |
| unresolved_call | `validate_configured_public_identity` | `_REPOSITORY_IDENTITY_RE.fullmatch` | 692 |
| unresolved_call | `validate_configured_public_identity` | `value.casefold().endswith` | 693 |
| unresolved_call | `validate_configured_public_identity` | `value.casefold` | 693 |
| unresolved_call | `_remote_mapping` | `isinstance` | 1414 |
| step_limit | `select_repository_identity` | `first 12 steps` | 0 |

## Behavior

This flow starts at `select_repository_identity` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
