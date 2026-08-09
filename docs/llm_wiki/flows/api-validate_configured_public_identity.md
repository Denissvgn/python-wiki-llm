# validate_configured_public_identity

**Entry point:** `validate_configured_public_identity` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_configured_public_identity
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as strip
    participant p4 as fullmatch
    participant p5 as endswith
    participant p6 as casefold
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: strip
    p0-->>p4: fullmatch
    p0-->>p5: endswith
    p0-->>p6: casefold
    p0->>p2: KnowledgeEnvelopeError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_configured_public_identity"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. strip"]
    s5["5. fullmatch"]
    s6["6. endswith"]
    s7["7. casefold"]
    s8["8. KnowledgeEnvelopeError"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('configured_public_identity', 'must be a qualified public namespace path')"| s3
    s1 -. "value.strip(data not statically known)" .-> s4
    s1 -. "_REPOSITORY_IDENTITY_RE.fullmatch(value)" .-> s5
    s1 -. "value.casefold().endswith('.git')" .-> s6
    s1 -. "value.casefold(data not statically known)" .-> s7
    s1 -->|"KnowledgeEnvelopeError('configured_public_identity', #34;must be a normalized public namespace path without scheme, credentials, port, query, fragment, dot segmen…"| s8
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_configured_public_identity` | `value: object` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `strip` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `endswith` | - | - | - | - |
| `casefold` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_configured_public_identity | isinstance | 685 | `isinstance(value, str)` |
| validate_configured_public_identity | KnowledgeEnvelopeError | 686 | `KnowledgeEnvelopeError('configured_public_identity', 'must be a qualified public namespace path')` |
| validate_configured_public_identity | strip | 691 | `value.strip(data not statically known)` |
| validate_configured_public_identity | fullmatch | 692 | `_REPOSITORY_IDENTITY_RE.fullmatch(value)` |
| validate_configured_public_identity | endswith | 693 | `value.casefold().endswith('.git')` |
| validate_configured_public_identity | casefold | 693 | `value.casefold(data not statically known)` |
| validate_configured_public_identity | KnowledgeEnvelopeError | 695 | `KnowledgeEnvelopeError('configured_public_identity', "must be a normalized public namespace path without scheme, credentials, port, query, fragment, dot segment, or '.git' suffix")` |

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

## Behavior

This flow starts at `validate_configured_public_identity` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
