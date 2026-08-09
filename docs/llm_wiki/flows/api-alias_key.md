# alias_key

**Entry point:** `alias_key` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as alias_key
    participant p1 as _alias_type
    participant p2 as isinstance
    participant p3 as GovernanceError
    participant p4 as _identity_value
    participant p5 as validate_alias_value
    participant p6 as validate_alias_type
    participant p7 as AliasType
    participant p8 as ConceptIdentityError
    participant p9 as validate_locator
    participant p10 as _machine_text
    participant p11 as len
    participant p12 as strip
    participant p13 as any
    participant p14 as isspace
    participant p15 as normalize
    participant p16 as startswith
    participant p17 as category
    participant p18 as _contains_uri_userinfo
    participant p19 as urlsplit
    participant p20 as _looks_absolute_path
    p0->>p1: _alias_type
    p1-->>p2: isinstance
    p1->>p3: GovernanceError
    p0->>p4: _identity_value
    p4->>p1: _alias_type
    p4->>p5: validate_alias_value
    p5->>p6: validate_alias_type
    p6-->>p2: isinstance
    p6->>p7: AliasType
    p6->>p8: ConceptIdentityError
    p5->>p9: validate_locator
    p9->>p10: _machine_text
    p10-->>p2: isinstance
    p10->>p8: ConceptIdentityError
    p10-->>p11: len
    p10->>p8: ConceptIdentityError
    p10-->>p12: strip
    p10-->>p13: any
    p10-->>p14: isspace
    p10->>p8: ConceptIdentityError
    p10-->>p15: normalize
    p10->>p8: ConceptIdentityError
    p10-->>p13: any
    p10-->>p16: startswith
    p10-->>p17: category
    p10->>p8: ConceptIdentityError
    p9->>p18: _contains_uri_userinfo
    p18-->>p19: urlsplit
    p9->>p20: _looks_absolute_path
    p20-->>p16: startswith
```

> Call sequence diagram shows 30 of 106 interactions; 76 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. alias_key"]
    s2["2. _alias_type"]
    s3["3. isinstance"]
    s4["4. GovernanceError"]
    s5["5. _identity_value"]
    s6["6. _alias_type"]
    s7["7. validate_alias_value"]
    s8["8. validate_alias_type"]
    s9["9. isinstance"]
    s10["10. AliasType"]
    s11["11. ConceptIdentityError"]
    s12["12. validate_locator"]
    s1 -->|"_alias_type(alias_type, 'alias.type')"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -->|"GovernanceError(path, #34;must be 'locator' or 'natural-key'#34;)"| s4
    s1 -->|"_identity_value(value, selected_type, 'alias.value')"| s5
    s5 -->|"_alias_type(alias_type, ...)"| s6
    s5 -->|"validate_alias_value(..., value)"| s7
    s7 -->|"validate_alias_type(alias_type)"| s8
    s8 -. "isinstance(value, AliasType)" .-> s9
    s8 -->|"AliasType(value)"| s10
    s8 -->|"ConceptIdentityError('alias_type', #34;must be 'locator' or 'natural-key'#34;)"| s11
    s7 -->|"validate_locator(value)"| s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s4 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s7 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `alias_key` | `alias_type: str`, `value: str` | - | - | `...` |
| `_alias_type` | `value: object`, `path: str` | `ALIAS_TYPES` | - | `value` |
| `isinstance` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_identity_value` | `value: object`, `alias_type: str`, `path: str` | `ALIAS_LOCATOR`, `AliasType`, `AliasType`, `ConceptIdentityError` | - | `validate_alias_value(...)` |
| `_alias_type` | `value: object`, `path: str` | `ALIAS_TYPES` | - | `value` |
| `validate_alias_value` | `alias_type: AliasType \| str`, `value: object` | `AliasType` | - | `validate_locator(...)`, `validate_natural_key(...)` |
| `validate_alias_type` | `value: AliasType \| str` | `AliasType` | - | `...` |
| `isinstance` | - | - | - | - |
| `AliasType` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `validate_locator` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `WikiSurfaceError` | - | `normalized` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| alias_key | _alias_type | 379 | `_alias_type(alias_type, 'alias.type')` |
| _alias_type | isinstance | 3264 | `isinstance(value, str)` |
| _alias_type | GovernanceError | 3265 | `GovernanceError(path, "must be 'locator' or 'natural-key'")` |
| alias_key | _identity_value | 380 | `_identity_value(value, selected_type, 'alias.value')` |
| _identity_value | _alias_type | 3273 | `_alias_type(alias_type, ...)` |
| _identity_value | validate_alias_value | 3275 | `validate_alias_value(..., value)` |
| validate_alias_value | validate_alias_type | 456 | `validate_alias_type(alias_type)` |
| validate_alias_type | isinstance | 445 | `isinstance(value, AliasType)` |
| validate_alias_type | AliasType | 445 | `AliasType(value)` |
| validate_alias_type | ConceptIdentityError | 447 | `ConceptIdentityError('alias_type', "must be 'locator' or 'natural-key'")` |
| validate_alias_value | validate_locator | 458 | `validate_locator(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_alias_type` | `isinstance` | 3264 |
| unresolved_call | `validate_alias_type` | `isinstance` | 445 |
| step_limit | `alias_key` | `first 12 steps` | 0 |
| truncated_flow | `alias_key` | `depth limit` | 0 |

## Behavior

This flow starts at `alias_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
