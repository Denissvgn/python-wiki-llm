# identity_coordinate_key

**Entry point:** `identity_coordinate_key` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as identity_coordinate_key
    participant p1 as validate_alias_type
    participant p2 as isinstance
    participant p3 as AliasType
    participant p4 as ConceptIdentityError
    participant p5 as validate_alias_value
    participant p6 as validate_locator
    participant p7 as _machine_text
    participant p8 as len
    participant p9 as strip
    participant p10 as any
    participant p11 as isspace
    participant p12 as normalize
    participant p13 as startswith
    participant p14 as category
    participant p15 as _contains_uri_userinfo
    participant p16 as urlsplit
    participant p17 as _looks_absolute_path
    participant p18 as match
    participant p19 as validate_exact_page_coordinate
    p0->>p1: validate_alias_type
    p1-->>p2: isinstance
    p1->>p3: AliasType
    p1->>p4: ConceptIdentityError
    p0->>p5: validate_alias_value
    p5->>p1: validate_alias_type
    p5->>p6: validate_locator
    p6->>p7: _machine_text
    p7-->>p2: isinstance
    p7->>p4: ConceptIdentityError
    p7-->>p8: len
    p7->>p4: ConceptIdentityError
    p7-->>p9: strip
    p7-->>p10: any
    p7-->>p11: isspace
    p7->>p4: ConceptIdentityError
    p7-->>p12: normalize
    p7->>p4: ConceptIdentityError
    p7-->>p10: any
    p7-->>p13: startswith
    p7-->>p14: category
    p7->>p4: ConceptIdentityError
    p6->>p15: _contains_uri_userinfo
    p15-->>p16: urlsplit
    p6->>p17: _looks_absolute_path
    p17-->>p13: startswith
    p17-->>p18: match
    p6->>p4: ConceptIdentityError
    p6->>p19: validate_exact_page_coordinate
    p19-->>p2: isinstance
```

> Call sequence diagram shows 30 of 125 interactions; 95 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. identity_coordinate_key"]
    s2["2. validate_alias_type"]
    s3["3. isinstance"]
    s4["4. AliasType"]
    s5["5. ConceptIdentityError"]
    s6["6. validate_alias_value"]
    s7["7. validate_alias_type"]
    s8["8. validate_locator"]
    s9["9. _machine_text"]
    s10["10. isinstance"]
    s11["11. ConceptIdentityError"]
    s12["12. len"]
    s1 -->|"validate_alias_type(alias_type)"| s2
    s2 -. "isinstance(value, AliasType)" .-> s3
    s2 -->|"AliasType(value)"| s4
    s2 -->|"ConceptIdentityError('alias_type', #34;must be 'locator' or 'natural-key'#34;)"| s5
    s1 -->|"validate_alias_value(selected, value)"| s6
    s6 -->|"validate_alias_type(alias_type)"| s7
    s6 -->|"validate_locator(value)"| s8
    s8 -->|"_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)"| s9
    s9 -. "isinstance(value, str)" .-> s10
    s9 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s11
    s9 -. "len(value)" .-> s12
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
    click s5 "../modules/concept_identity.md"
    click s6 "../modules/concept_identity.md"
    click s7 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s9 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `identity_coordinate_key` | `alias_type: AliasType \| str`, `value: object` | `AliasType` | - | `normalized`, `mcp_uri(...)`, `mcp_uri(...)` |
| `validate_alias_type` | `value: AliasType \| str` | `AliasType` | - | `...` |
| `isinstance` | - | - | - | - |
| `AliasType` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `validate_alias_value` | `alias_type: AliasType \| str`, `value: object` | `AliasType` | - | `validate_locator(...)`, `validate_natural_key(...)` |
| `validate_alias_type` | `value: AliasType \| str` | `AliasType` | - | `...` |
| `validate_locator` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `WikiSurfaceError` | - | `normalized` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| identity_coordinate_key | validate_alias_type | 474 | `validate_alias_type(alias_type)` |
| validate_alias_type | isinstance | 445 | `isinstance(value, AliasType)` |
| validate_alias_type | AliasType | 445 | `AliasType(value)` |
| validate_alias_type | ConceptIdentityError | 447 | `ConceptIdentityError('alias_type', "must be 'locator' or 'natural-key'")` |
| identity_coordinate_key | validate_alias_value | 475 | `validate_alias_value(selected, value)` |
| validate_alias_value | validate_alias_type | 456 | `validate_alias_type(alias_type)` |
| validate_alias_value | validate_locator | 458 | `validate_locator(value)` |
| validate_locator | _machine_text | 408 | `_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_alias_type` | `isinstance` | 445 |
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| step_limit | `identity_coordinate_key` | `first 12 steps` | 0 |
| truncated_flow | `identity_coordinate_key` | `depth limit` | 0 |

## Behavior

This flow starts at `identity_coordinate_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
