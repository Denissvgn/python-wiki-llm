# validate_concept_kind

**Entry point:** `validate_concept_kind` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_concept_kind
    participant p1 as _machine_text
    participant p2 as _QUALIFIED_KIND_RE.fullmatch
    participant p3 as ConceptIdentityError
    participant p4 as isinstance
    participant p5 as len
    participant p6 as value.strip
    participant p7 as any
    participant p8 as character.isspace
    participant p9 as unicodedata.normalize
    participant p10 as unicodedata.category(…).startswith
    participant p11 as unicodedata.category
    p0->>p1: _machine_text
    p0-->>p2: _QUALIFIED_KIND_RE.fullmatch(text)
    p0->>p3: ConceptIdentityError
    p1-->>p4: isinstance(value, str)
    p1->>p3: ConceptIdentityError
    p1-->>p5: len(value)
    p1->>p3: ConceptIdentityError
    p1-->>p6: value.strip
    p1-->>p7: any(...)
    p1-->>p8: character.isspace
    p1->>p3: ConceptIdentityError
    p1-->>p9: unicodedata.normalize('NFC', value)
    p1->>p3: ConceptIdentityError
    p1-->>p7: any(...)
    p1-->>p10: unicodedata.category(…).startswith('C')
    p1-->>p11: unicodedata.category(character)
    p1->>p3: ConceptIdentityError
```

> Call sequence diagram shows 17 of 17 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 6 (0 omitted); unresolved 4 of 4 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 8; effect analysis evaluated: 2, partial: 0, unavailable: 6. Counts include steps omitted from the displayed trace.

Collector observations for 2 source steps with known totals: observed: 8, emitted: 8, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_concept_kind` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_machine_text` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `len` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.strip` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `character.isspace` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `unicodedata.normalize` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. validate_concept_kind"]
    s2["2. _machine_text"]
    s3["3. isinstance"]
    s4["4. ConceptIdentityError"]
    s5["5. len"]
    s6["6. ConceptIdentityError"]
    s7["7. value.strip"]
    s8["8. any"]
    s9["9. character.isspace"]
    s10["10. ConceptIdentityError"]
    s11["11. unicodedata.normalize"]
    s12["12. ConceptIdentityError"]
    s1 -->|"_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s4
    s2 -. "len(value)" .-> s5
    s2 -->|"ConceptIdentityError(field, ...)"| s6
    s2 -. "value.strip(data not statically known)" .-> s7
    s2 -. "any(...)" .-> s8
    s2 -. "character.isspace(data not statically known)" .-> s9
    s2 -->|"ConceptIdentityError(field, 'must not contain whitespace')"| s10
    s2 -. "unicodedata.normalize('NFC', value)" .-> s11
    s2 -->|"ConceptIdentityError(field, 'must use Unicode NFC normalization')"| s12
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
    click s6 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_concept_kind` | `value: object` | `_MAX_CONCEPT_KIND_LENGTH`, `_UID_TAG_BY_KIND` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any` | - | - | - | - |
| `character.isspace` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `unicodedata.normalize` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_concept_kind | _machine_text | 306 | `_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)` |
| _machine_text | isinstance | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip | 946 | `value.strip(data not statically known)` |
| _machine_text | any | 946 | `any(...)` |
| _machine_text | character.isspace | 946 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 947 | `ConceptIdentityError(field, 'must not contain whitespace')` |
| _machine_text | unicodedata.normalize | 948 | `unicodedata.normalize('NFC', value)` |
| _machine_text | ConceptIdentityError | 949 | `ConceptIdentityError(field, 'must use Unicode NFC normalization')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_machine_text` | `isinstance` | 942 |
| unresolved_call | `_machine_text` | `value.strip` | 946 |
| external_call | `_machine_text` | `any` | 946 |
| unresolved_call | `_machine_text` | `character.isspace` | 946 |
| external_call | `_machine_text` | `unicodedata.normalize` | 948 |
| step_limit | `validate_concept_kind` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_concept_kind` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
