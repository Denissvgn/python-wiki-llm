# derive_concept_uid

**Entry point:** `derive_concept_uid` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as derive_concept_uid
    participant p1 as validate_bundle_id
    participant p2 as _machine_text
    participant p3 as isinstance
    participant p4 as ConceptIdentityError
    participant p5 as len
    participant p6 as strip
    participant p7 as any
    participant p8 as isspace
    participant p9 as normalize
    participant p10 as startswith
    participant p11 as category
    participant p12 as fullmatch
    participant p13 as casefold
    participant p14 as _looks_absolute_path
    participant p15 as match
    participant p16 as _contains_uri_userinfo
    participant p17 as urlsplit
    participant p18 as validate_concept_kind
    participant p19 as validate_natural_key
    p0->>p1: validate_bundle_id
    p1->>p2: _machine_text
    p2-->>p3: isinstance
    p2->>p4: ConceptIdentityError
    p2-->>p5: len
    p2->>p4: ConceptIdentityError
    p2-->>p6: strip
    p2-->>p7: any
    p2-->>p8: isspace
    p2->>p4: ConceptIdentityError
    p2-->>p9: normalize
    p2->>p4: ConceptIdentityError
    p2-->>p7: any
    p2-->>p10: startswith
    p2-->>p11: category
    p2->>p4: ConceptIdentityError
    p1-->>p12: fullmatch
    p1-->>p13: casefold
    p1->>p14: _looks_absolute_path
    p14-->>p10: startswith
    p14-->>p15: match
    p1->>p16: _contains_uri_userinfo
    p16-->>p17: urlsplit
    p1->>p4: ConceptIdentityError
    p0->>p18: validate_concept_kind
    p18->>p2: _machine_text
    p18-->>p12: fullmatch
    p18->>p4: ConceptIdentityError
    p0->>p19: validate_natural_key
    p19->>p2: _machine_text
```

> Call sequence diagram shows 30 of 77 interactions; 47 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. derive_concept_uid"]
    s2["2. validate_bundle_id"]
    s3["3. _machine_text"]
    s4["4. isinstance"]
    s5["5. ConceptIdentityError"]
    s6["6. len"]
    s7["7. ConceptIdentityError"]
    s8["8. strip"]
    s9["9. any"]
    s10["10. isspace"]
    s11["11. ConceptIdentityError"]
    s12["12. normalize"]
    s1 -->|"validate_bundle_id(bundle_id)"| s2
    s2 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s5
    s3 -. "len(value)" .-> s6
    s3 -->|"ConceptIdentityError(field, ...)"| s7
    s3 -. "value.strip(data not statically known)" .-> s8
    s3 -. "any(...)" .-> s9
    s3 -. "character.isspace(data not statically known)" .-> s10
    s3 -->|"ConceptIdentityError(field, 'must not contain whitespace')"| s11
    s3 -. "unicodedata.normalize('NFC', value)" .-> s12
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s3 "../modules/concept_identity.md"
    click s5 "../modules/concept_identity.md"
    click s7 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `derive_concept_uid` | `bundle_id: object`, `concept_kind: object`, `natural_key: object` | `CONCEPT_UID_HEX_LENGTH` | - | `...` |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `isspace` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `normalize` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| derive_concept_uid | validate_bundle_id | 504 | `validate_bundle_id(bundle_id)` |
| validate_bundle_id | _machine_text | 288 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |
| _machine_text | strip | 916 | `value.strip(data not statically known)` |
| _machine_text | any | 916 | `any(...)` |
| _machine_text | isspace | 916 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 917 | `ConceptIdentityError(field, 'must not contain whitespace')` |
| _machine_text | normalize | 918 | `unicodedata.normalize('NFC', value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| unresolved_call | `_machine_text` | `any` | 916 |
| unresolved_call | `_machine_text` | `character.isspace` | 916 |
| external_call | `_machine_text` | `unicodedata.normalize` | 918 |
| step_limit | `derive_concept_uid` | `first 12 steps` | 0 |

## Behavior

This flow starts at `derive_concept_uid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
