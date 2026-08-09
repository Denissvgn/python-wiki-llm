# natural_key_for

**Entry point:** `natural_key_for` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as natural_key_for
    participant p1 as _concept_kind
    participant p2 as validate_concept_kind
    participant p3 as _machine_text
    participant p4 as isinstance
    participant p5 as ConceptIdentityError
    participant p6 as len
    participant p7 as strip
    participant p8 as any
    participant p9 as isspace
    participant p10 as normalize
    participant p11 as startswith
    participant p12 as category
    participant p13 as fullmatch
    participant p14 as GovernanceError
    participant p15 as _relative_path
    participant p16 as require_repository_relative_path
    participant p17 as ord
    participant p18 as match
    p0->>p1: _concept_kind
    p1->>p2: validate_concept_kind
    p2->>p3: _machine_text
    p3-->>p4: isinstance
    p3->>p5: ConceptIdentityError
    p3-->>p6: len
    p3->>p5: ConceptIdentityError
    p3-->>p7: strip
    p3-->>p8: any
    p3-->>p9: isspace
    p3->>p5: ConceptIdentityError
    p3-->>p10: normalize
    p3->>p5: ConceptIdentityError
    p3-->>p8: any
    p3-->>p11: startswith
    p3-->>p12: category
    p3->>p5: ConceptIdentityError
    p2-->>p13: fullmatch
    p2->>p5: ConceptIdentityError
    p1->>p14: GovernanceError
    p0->>p15: _relative_path
    p15->>p16: require_repository_relative_path
    p16-->>p4: isinstance
    p16-->>p7: strip
    p16-->>p8: any
    p16-->>p17: ord
    p16-->>p17: ord
    p16-->>p11: startswith
    p16-->>p11: startswith
    p16-->>p18: match
```

> Call sequence diagram shows 30 of 165 interactions; 135 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. natural_key_for"]
    s2["2. _concept_kind"]
    s3["3. validate_concept_kind"]
    s4["4. _machine_text"]
    s5["5. isinstance"]
    s6["6. ConceptIdentityError"]
    s7["7. len"]
    s8["8. ConceptIdentityError"]
    s9["9. strip"]
    s10["10. any"]
    s11["11. isspace"]
    s12["12. ConceptIdentityError"]
    s1 -->|"_concept_kind(concept_kind, 'concept_kind')"| s2
    s2 -->|"validate_concept_kind(value)"| s3
    s3 -->|"_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)"| s4
    s4 -. "isinstance(value, str)" .-> s5
    s4 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s6
    s4 -. "len(value)" .-> s7
    s4 -->|"ConceptIdentityError(field, ...)"| s8
    s4 -. "value.strip(data not statically known)" .-> s9
    s4 -. "any(...)" .-> s10
    s4 -. "character.isspace(data not statically known)" .-> s11
    s4 -->|"ConceptIdentityError(field, 'must not contain whitespace')"| s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s3 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
    click s6 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `natural_key_for` | `concept_kind: str`, `canonical_path: str` | - | - | `_natural_key(...)` |
| `_concept_kind` | `value: object`, `path: str` | `ConceptIdentityError` | - | `validate_concept_kind(...)` |
| `validate_concept_kind` | `value: object` | `_MAX_CONCEPT_KIND_LENGTH`, `_UID_TAG_BY_KIND` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `isspace` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| natural_key_for | _concept_kind | 394 | `_concept_kind(concept_kind, 'concept_kind')` |
| _concept_kind | validate_concept_kind | 3364 | `validate_concept_kind(value)` |
| validate_concept_kind | _machine_text | 305 | `_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |
| _machine_text | strip | 916 | `value.strip(data not statically known)` |
| _machine_text | any | 916 | `any(...)` |
| _machine_text | isspace | 916 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 917 | `ConceptIdentityError(field, 'must not contain whitespace')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| unresolved_call | `_machine_text` | `any` | 916 |
| unresolved_call | `_machine_text` | `character.isspace` | 916 |
| step_limit | `natural_key_for` | `first 12 steps` | 0 |

## Behavior

This flow starts at `natural_key_for` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
