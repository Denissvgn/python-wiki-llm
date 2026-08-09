# validate_alias_value

**Entry point:** `validate_alias_value` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_alias_value
    participant p1 as validate_alias_type
    participant p2 as isinstance
    participant p3 as AliasType
    participant p4 as ConceptIdentityError
    participant p5 as validate_locator
    participant p6 as _machine_text
    participant p7 as len
    participant p8 as strip
    participant p9 as any
    participant p10 as isspace
    participant p11 as normalize
    participant p12 as startswith
    participant p13 as category
    participant p14 as _contains_uri_userinfo
    participant p15 as urlsplit
    participant p16 as _looks_absolute_path
    participant p17 as match
    participant p18 as validate_exact_page_coordinate
    participant p19 as WikiSurfaceError
    p0->>p1: validate_alias_type
    p1-->>p2: isinstance
    p1->>p3: AliasType
    p1->>p4: ConceptIdentityError
    p0->>p5: validate_locator
    p5->>p6: _machine_text
    p6-->>p2: isinstance
    p6->>p4: ConceptIdentityError
    p6-->>p7: len
    p6->>p4: ConceptIdentityError
    p6-->>p8: strip
    p6-->>p9: any
    p6-->>p10: isspace
    p6->>p4: ConceptIdentityError
    p6-->>p11: normalize
    p6->>p4: ConceptIdentityError
    p6-->>p9: any
    p6-->>p12: startswith
    p6-->>p13: category
    p6->>p4: ConceptIdentityError
    p5->>p14: _contains_uri_userinfo
    p14-->>p15: urlsplit
    p5->>p16: _looks_absolute_path
    p16-->>p12: startswith
    p16-->>p17: match
    p5->>p4: ConceptIdentityError
    p5->>p18: validate_exact_page_coordinate
    p18-->>p2: isinstance
    p18-->>p8: strip
    p18->>p19: WikiSurfaceError
```

> Call sequence diagram shows 30 of 121 interactions; 91 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_alias_value"]
    s2["2. validate_alias_type"]
    s3["3. isinstance"]
    s4["4. AliasType"]
    s5["5. ConceptIdentityError"]
    s6["6. validate_locator"]
    s7["7. _machine_text"]
    s8["8. isinstance"]
    s9["9. ConceptIdentityError"]
    s10["10. len"]
    s11["11. ConceptIdentityError"]
    s12["12. strip"]
    s1 -->|"validate_alias_type(alias_type)"| s2
    s2 -. "isinstance(value, AliasType)" .-> s3
    s2 -->|"AliasType(value)"| s4
    s2 -->|"ConceptIdentityError('alias_type', #34;must be 'locator' or 'natural-key'#34;)"| s5
    s1 -->|"validate_locator(value)"| s6
    s6 -->|"_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)"| s7
    s7 -. "isinstance(value, str)" .-> s8
    s7 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s9
    s7 -. "len(value)" .-> s10
    s7 -->|"ConceptIdentityError(field, ...)"| s11
    s7 -. "value.strip(data not statically known)" .-> s12
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
    click s5 "../modules/concept_identity.md"
    click s6 "../modules/concept_identity.md"
    click s7 "../modules/concept_identity.md"
    click s9 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_alias_value` | `alias_type: AliasType \| str`, `value: object` | `AliasType` | - | `validate_locator(...)`, `validate_natural_key(...)` |
| `validate_alias_type` | `value: AliasType \| str` | `AliasType` | - | `...` |
| `isinstance` | - | - | - | - |
| `AliasType` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `validate_locator` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `WikiSurfaceError` | - | `normalized` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_alias_value | validate_alias_type | 456 | `validate_alias_type(alias_type)` |
| validate_alias_type | isinstance | 445 | `isinstance(value, AliasType)` |
| validate_alias_type | AliasType | 445 | `AliasType(value)` |
| validate_alias_type | ConceptIdentityError | 447 | `ConceptIdentityError('alias_type', "must be 'locator' or 'natural-key'")` |
| validate_alias_value | validate_locator | 458 | `validate_locator(value)` |
| validate_locator | _machine_text | 408 | `_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |
| _machine_text | strip | 916 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_alias_type` | `isinstance` | 445 |
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| step_limit | `validate_alias_value` | `first 12 steps` | 0 |
| truncated_flow | `validate_alias_value` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_alias_value` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
