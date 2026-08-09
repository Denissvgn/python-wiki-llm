# allocate_concept

**Entry point:** `allocate_concept` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as allocate_concept
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as validate_bundle_id
    participant p4 as _machine_text
    participant p5 as ConceptIdentityError
    participant p6 as len
    participant p7 as strip
    participant p8 as any
    participant p9 as isspace
    participant p10 as normalize
    participant p11 as startswith
    participant p12 as category
    participant p13 as fullmatch
    participant p14 as casefold
    participant p15 as _looks_absolute_path
    participant p16 as match
    participant p17 as _contains_uri_userinfo
    participant p18 as urlsplit
    participant p19 as validate_identity_registry
    participant p20 as _typed_tuple
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: validate_bundle_id
    p3->>p4: _machine_text
    p4-->>p1: isinstance
    p4->>p5: ConceptIdentityError
    p4-->>p6: len
    p4->>p5: ConceptIdentityError
    p4-->>p7: strip
    p4-->>p8: any
    p4-->>p9: isspace
    p4->>p5: ConceptIdentityError
    p4-->>p10: normalize
    p4->>p5: ConceptIdentityError
    p4-->>p8: any
    p4-->>p11: startswith
    p4-->>p12: category
    p4->>p5: ConceptIdentityError
    p3-->>p13: fullmatch
    p3-->>p14: casefold
    p3->>p15: _looks_absolute_path
    p15-->>p11: startswith
    p15-->>p16: match
    p3->>p17: _contains_uri_userinfo
    p17-->>p18: urlsplit
    p3->>p5: ConceptIdentityError
    p0->>p19: validate_identity_registry
    p19->>p20: _typed_tuple
    p20-->>p1: isinstance
    p20-->>p2: TypeError
```

> Call sequence diagram shows 30 of 193 interactions; 163 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. allocate_concept"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. validate_bundle_id"]
    s5["5. _machine_text"]
    s6["6. isinstance"]
    s7["7. ConceptIdentityError"]
    s8["8. len"]
    s9["9. ConceptIdentityError"]
    s10["10. strip"]
    s11["11. any"]
    s12["12. isspace"]
    s1 -. "isinstance(reference, ConceptReference)" .-> s2
    s1 -. "TypeError('reference must be a ConceptReference')" .-> s3
    s1 -->|"validate_bundle_id(bundle_id)"| s4
    s4 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s5
    s5 -. "isinstance(value, str)" .-> s6
    s5 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s7
    s5 -. "len(value)" .-> s8
    s5 -->|"ConceptIdentityError(field, ...)"| s9
    s5 -. "value.strip(data not statically known)" .-> s10
    s5 -. "any(...)" .-> s11
    s5 -. "character.isspace(data not statically known)" .-> s12
    b0["mutation candidates.add"]
    s1 -. "mutation candidates.add" .-> b0
    b1["mutation candidates.add"]
    s1 -. "mutation candidates.add" .-> b1
    click s1 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
    click s5 "../modules/concept_identity.md"
    click s7 "../modules/concept_identity.md"
    click s9 "../modules/concept_identity.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `allocate_concept` | `bundle_id: object`, `reference: ConceptReference`, `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptReference`, `AliasType`, `AliasType`, `AliasType`, `AliasType` | - | `allocation`, `ConceptAllocation(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `isspace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| allocate_concept | isinstance | 537 | `isinstance(reference, ConceptReference)` |
| allocate_concept | TypeError | 538 | `TypeError('reference must be a ConceptReference')` |
| allocate_concept | validate_bundle_id | 539 | `validate_bundle_id(bundle_id)` |
| validate_bundle_id | _machine_text | 288 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |
| _machine_text | strip | 916 | `value.strip(data not statically known)` |
| _machine_text | any | 916 | `any(...)` |
| _machine_text | isspace | 916 | `character.isspace(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `candidates.add` | `allocate_concept` | 556 |
| mutation | `candidates.add` | `allocate_concept` | 566 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `allocate_concept` | `isinstance` | 537 |
| unresolved_call | `allocate_concept` | `TypeError` | 538 |
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| unresolved_call | `_machine_text` | `any` | 916 |
| unresolved_call | `_machine_text` | `character.isspace` | 916 |
| step_limit | `allocate_concept` | `first 12 steps` | 0 |
| truncated_flow | `allocate_concept` | `depth limit` | 0 |

## Behavior

This flow starts at `allocate_concept` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
