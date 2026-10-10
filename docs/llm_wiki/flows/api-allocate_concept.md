# allocate_concept

**Entry point:** `allocate_concept` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as allocate_concept
    participant p1 as isinstance (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    participant p2 as TypeError (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    participant p3 as validate_bundle_id
    participant p4 as validate_identity_registry
    participant p5 as set (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    participant p6 as identity_coordinate_key
    participant p7 as candidates.add
    participant p8 as len (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    participant p9 as IdentityCollision
    participant p10 as tuple (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    participant p11 as sorted (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    participant p12 as IdentityCollisionError
    participant p13 as next
    participant p14 as iter
    participant p15 as ConceptIdentityError
    participant p16 as derive_concept_uid
    participant p17 as ConceptAllocation
    participant p18 as _machine_text
    participant p19 as _typed_tuple
    participant p20 as _BUNDLE_ID_RE.fullmatch
    participant p21 as validate_concept_kind
    participant p22 as text.casefold
    participant p23 as find_identity_collisions
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ntity.py:allocate_concept)(reference, ConceptReference)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ntity.py:allocate_concept)('reference must be a ConceptReference')
    p0->>p3: validate_bundle_id
    p0->>p4: validate_identity_registry
    p0-->>p5: set (src/llm_wiki_cli/services…ntity.py:allocate_concept)
    p0->>p6: identity_coordinate_key
    p0->>p6: identity_coordinate_key
    p0-->>p7: candidates.add(allocation.uid)
    p0->>p6: identity_coordinate_key
    p0-->>p7: candidates.add(alias.uid)
    p0-->>p8: len (src/llm_wiki_cli/services…ntity.py:allocate_concept)(candidates)
    p0->>p9: IdentityCollision
    p0-->>p10: tuple (src/llm_wiki_cli/services…ntity.py:allocate_concept)(sorted(...))
    p0-->>p11: sorted (src/llm_wiki_cli/services…ntity.py:allocate_concept)(candidates)
    p0->>p12: IdentityCollisionError
    p0-->>p13: next(iter(...))
    p0-->>p14: iter(candidates)
    p0->>p15: ConceptIdentityError
    p0->>p16: derive_concept_uid
    p0->>p12: IdentityCollisionError
    p0->>p9: IdentityCollision
    p0->>p17: ConceptAllocation
    p3->>p18: _machine_text
    p4->>p19: _typed_tuple
    p16->>p3: validate_bundle_id
    p3-->>p20: _BUNDLE_ID_RE.fullmatch(text)
    p4->>p19: _typed_tuple
    p16->>p21: validate_concept_kind
    p3-->>p22: text.casefold
    p4->>p23: find_identity_collisions
```

> Call sequence diagram shows 30 of 193 interactions; 163 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 62 (54 omitted); unresolved 4 of 44 (40 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 5 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 5 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 5 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 4 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 25 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_typed_tuple` | 29 | - | external | 7 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 38 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 10 |
> Omission summary shows 8 of 38 groups; 30 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. allocate_concept"]
    s2["2. isinstance (src/llm_wiki_cli/services…ntity.py:allocate_concept)"]
    s3["3. TypeError (src/llm_wiki_cli/services…ntity.py:allocate_concept)"]
    s4["4. validate_bundle_id"]
    s5["5. _machine_text"]
    s6["6. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s7["7. ConceptIdentityError"]
    s8["8. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s9["9. ConceptIdentityError"]
    s10["10. value.strip"]
    s11["11. any (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s12["12. character.isspace"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ntity.py:allocate_concept)(reference, ConceptReference)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…ntity.py:allocate_concept)('reference must be a ConceptReference')" .-> s3
    s1 -->|"validate_bundle_id(bundle_id)"| s4
    s4 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s6
    s5 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s7
    s5 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s8
    s5 -->|"ConceptIdentityError(field, ...)"| s9
    s5 -. "value.strip(data not statically known)" .-> s10
    s5 -. "any (src/llm_wiki_cli/services…identity.py:_machine_text)(...)" .-> s11
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
| `isinstance (src/llm_wiki_cli/services…ntity.py:allocate_concept)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ntity.py:allocate_concept)` | - | - | - | - |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `character.isspace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| allocate_concept | isinstance (src/llm_wiki_cli/services…ntity.py:allocate_concept) | 567 | `isinstance(reference, ConceptReference)` |
| allocate_concept | TypeError (src/llm_wiki_cli/services…ntity.py:allocate_concept) | 568 | `TypeError('reference must be a ConceptReference')` |
| allocate_concept | validate_bundle_id | 569 | `validate_bundle_id(bundle_id)` |
| validate_bundle_id | _machine_text | 289 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip | 946 | `value.strip(data not statically known)` |
| _machine_text | any (src/llm_wiki_cli/services…identity.py:_machine_text) | 946 | `any(...)` |
| _machine_text | character.isspace | 946 | `character.isspace(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `candidates.add` | `allocate_concept` | 586 |
| mutation | `candidates.add` | `allocate_concept` | 596 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `allocate_concept` | `isinstance` | 567 |
| external_call | `allocate_concept` | `TypeError` | 568 |
| external_call | `_machine_text` | `isinstance` | 942 |
| unresolved_call | `_machine_text` | `value.strip` | 946 |
| external_call | `_machine_text` | `any` | 946 |
| unresolved_call | `_machine_text` | `character.isspace` | 946 |
| step_limit | `allocate_concept` | `first 12 steps` | 0 |
| truncated_flow | `allocate_concept` | `depth limit` | 0 |

## Behavior

This flow starts at `allocate_concept` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
