# natural_key_for

**Entry point:** `natural_key_for` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p1 as natural_key_for (src/llm_wiki_cli/services/concept_identity.py)
    participant p2 as GovernanceError
    participant p3 as validate_concept_kind
    participant p4 as require_repository_relative_path
    participant p5 as validate_natural_key
    participant p6 as _machine_text
    participant p7 as require_portable_relative_path
    participant p8 as _safe_decoded_coordinate
    participant p9 as _default_path_error
    participant p10 as _check_path_collision
    participant p11 as require_portable_path_component
    participant p12 as ConceptIdentityError
    participant p13 as _syntax_key
    participant p14 as _known_syntax
    participant p15 as _remember_syntax
    participant p16 as _contains_uri_userinfo
    participant p17 as _contains_coordinate_userinfo
    participant p18 as _looks_absolute_path
    participant p19 as SharedValidationError
    participant p20 as portable_path_key
    participant p21 as isinstance (src/llm_wiki_cli/services…_repository_relative_path)
    participant p22 as _QUALIFIED_KIND_RE.fullmatch
    participant p23 as text.partition
    participant p24 as _NATURAL_KEY_PREFIX_RE.fullmatch
    participant p25 as value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    participant p26 as _NATURAL_KEY_PAYLOAD_RE.fullmatch
    participant p27 as any (src/llm_wiki_cli/services…_repository_relative_path)
    participant p28 as ord (src/llm_wiki_cli/services…_repository_relative_path)
    participant p29 as _INVALID_PERCENT_RE.search
    p0->>p1: natural_key_for (src/llm_wiki_cli/services/concept_identity.py)
    p0->>p2: GovernanceError
    p1->>p3: validate_concept_kind
    p1->>p4: require_repository_relative_path
    p1->>p5: validate_natural_key
    p3->>p6: _machine_text
    p4->>p7: require_portable_relative_path
    p5->>p8: _safe_decoded_coordinate
    p7->>p9: _default_path_error
    p7->>p10: _check_path_collision
    p7->>p11: require_portable_path_component
    p1->>p12: ConceptIdentityError
    p4->>p13: _syntax_key
    p4->>p14: _known_syntax
    p4->>p15: _remember_syntax
    p5->>p16: _contains_uri_userinfo
    p5->>p17: _contains_coordinate_userinfo
    p5->>p18: _looks_absolute_path
    p9->>p19: SharedValidationError
    p10->>p20: portable_path_key
    p4-->>p21: isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)
    p3-->>p22: _QUALIFIED_KIND_RE.fullmatch(text)
    p5-->>p23: text.partition(':')
    p5-->>p24: _NATURAL_KEY_PREFIX_RE.fullmatch(prefix)
    p4-->>p25: value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    p5-->>p26: _NATURAL_KEY_PAYLOAD_RE.fullmatch(payload)
    p4-->>p27: any (src/llm_wiki_cli/services…_repository_relative_path)(...)
    p4-->>p28: ord (src/llm_wiki_cli/services…_repository_relative_path)(character)
    p5-->>p29: _INVALID_PERCENT_RE.search(payload)
    p4-->>p28: ord (src/llm_wiki_cli/services…_repository_relative_path)(character)
```

> Call sequence diagram shows 30 of 145 interactions; 115 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 38 (34 omitted); unresolved 6 of 48 (42 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 4 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 4 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 4 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_concept_kind` | 3 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 23 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 30 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 21 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 21 | - | external | 3 |
> Omission summary shows 8 of 31 groups; 23 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 60; effect analysis evaluated: 26, partial: 3, unavailable: 31. Counts include steps omitted from the displayed trace.

Collector observations for 29 source steps with known totals: observed: 135, emitted: 120, omitted: 15. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `natural_key_for (src/llm_wiki_cli/services/concept_identity.py)` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `validate_concept_kind` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_machine_text` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)"]
    s2["2. natural_key_for (src/llm_wiki_cli/services/concept_identity.py)"]
    s3["3. validate_concept_kind"]
    s4["4. _machine_text"]
    s5["5. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s6["6. ConceptIdentityError"]
    s7["7. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s8["8. ConceptIdentityError"]
    s9["9. value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s10["10. any (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s11["11. character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -->|"natural_key_for (src/llm_wiki_cli/services/concept_identity.py)(concept_kind, canonical_path)"| s2
    s2 -->|"validate_concept_kind(concept_kind)"| s3
    s3 -->|"_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s5
    s4 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s6
    s4 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s7
    s4 -->|"ConceptIdentityError(field, ...)"| s8
    s4 -. "value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)(data not statically known)" .-> s9
    s4 -. "any (src/llm_wiki_cli/services…identity.py:_machine_text)(...)" .-> s10
    s4 -. "character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)(data not statically known)" .-> s11
    s4 -->|"ConceptIdentityError(field, 'must not contain whitespace')"| s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/concept_identity.md"
    click s3 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
    click s6 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)` | `concept_kind: str`, `canonical_path: str` | `ConceptIdentityError` | - | `_identity_natural_key_for(...)` |
| `natural_key_for (src/llm_wiki_cli/services/concept_identity.py)` | `concept_kind: str`, `canonical_path: str` | - | - | `validate_natural_key(...)` |
| `validate_concept_kind` | `value: object` | `_MAX_CONCEPT_KIND_LENGTH`, `_UID_TAG_BY_KIND` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `any (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py) | natural_key_for (src/llm_wiki_cli/services/concept_identity.py) | 397 | `_identity_natural_key_for(concept_kind, canonical_path)` |
| natural_key_for (src/llm_wiki_cli/services/concept_identity.py) | validate_concept_kind | 327 | `validate_concept_kind(concept_kind)` |
| validate_concept_kind | _machine_text | 306 | `_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip (src/llm_wiki_cli/services…identity.py:_machine_text) | 946 | `value.strip(data not statically known)` |
| _machine_text | any (src/llm_wiki_cli/services…identity.py:_machine_text) | 946 | `any(...)` |
| _machine_text | character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text) | 946 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 947 | `ConceptIdentityError(field, 'must not contain whitespace')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_machine_text` | `isinstance` | 942 |
| unresolved_call | `_machine_text` | `value.strip` | 946 |
| external_call | `_machine_text` | `any` | 946 |
| unresolved_call | `_machine_text` | `character.isspace` | 946 |
| step_limit | `natural_key_for` | `first 12 steps` | 0 |

## Behavior

This flow starts at `natural_key_for` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
