# identity_coordinate_key

**Entry point:** `identity_coordinate_key` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as identity_coordinate_key
    participant p1 as validate_alias_type
    participant p2 as validate_alias_value
    participant p3 as iter_page_kinds
    participant p4 as canonical_path
    participant p5 as mcp_uri
    participant p6 as validate_locator
    participant p7 as validate_natural_key
    participant p8 as _machine_text
    participant p9 as validate_exact_page_coordinate
    participant p10 as _safe_decoded_coordinate
    participant p11 as _matches_directory_path
    participant p12 as _matches_directory_uri
    participant p13 as is_safe_page_id
    participant p14 as AliasType
    participant p15 as ConceptIdentityError
    participant p16 as _contains_uri_userinfo
    participant p17 as _looks_absolute_path
    participant p18 as _contains_coordinate_userinfo
    participant p19 as WikiSurfaceError
    participant p20 as _entry_for
    participant p21 as _validate_page_id
    participant p22 as is_portable_path_component
    participant p23 as len (src/llm_wiki_cli/services…y:identity_coordinate_key)
    participant p24 as normalized.startswith
    participant p25 as normalized.endswith
    participant p26 as AssertionError
    participant p27 as isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)
    participant p28 as text.partition
    p0->>p1: validate_alias_type
    p0->>p2: validate_alias_value
    p0->>p3: iter_page_kinds
    p0->>p4: canonical_path
    p0->>p5: mcp_uri
    p2->>p6: validate_locator
    p2->>p7: validate_natural_key
    p6->>p8: _machine_text
    p6->>p9: validate_exact_page_coordinate
    p7->>p10: _safe_decoded_coordinate
    p9->>p11: _matches_directory_path
    p9->>p12: _matches_directory_uri
    p11->>p13: is_safe_page_id
    p1->>p14: AliasType
    p1->>p15: ConceptIdentityError
    p6->>p16: _contains_uri_userinfo
    p6->>p17: _looks_absolute_path
    p7->>p18: _contains_coordinate_userinfo
    p9->>p19: WikiSurfaceError
    p4->>p20: _entry_for
    p4->>p21: _validate_page_id
    p13->>p22: is_portable_path_component
    p0-->>p23: len (src/llm_wiki_cli/services…y:identity_coordinate_key)(prefix)
    p0-->>p24: normalized.startswith('llm-wiki://')
    p0-->>p24: normalized.startswith(prefix)
    p0-->>p25: normalized.endswith('.md')
    p0-->>p23: len (src/llm_wiki_cli/services…y:identity_coordinate_key)('.md')
    p0-->>p26: AssertionError('validated locator was absent from the surface registry')
    p1-->>p27: isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)(value, AliasType)
    p7-->>p28: text.partition(':')
```

> Call sequence diagram shows 30 of 125 interactions; 95 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 33 (29 omitted); unresolved 4 of 33 (29 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_value` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 9 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 9 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 9 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 24 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 26 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_locator` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 3 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 30 | - | external | 4 |
> Omission summary shows 8 of 31 groups; 23 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 60; effect analysis evaluated: 32, partial: 0, unavailable: 28. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `identity_coordinate_key` | `available` | `evaluated` | `available` |
| `validate_alias_type` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `AliasType` | `unavailable` | `unavailable` | `unavailable` |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` |
| `validate_alias_value` | `available` | `evaluated` | `available` |
| `validate_alias_type` | `available` | `evaluated` | `available` |
| `validate_locator` | `available` | `evaluated` | `available` |
| `_machine_text` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. identity_coordinate_key"]
    s2["2. validate_alias_type"]
    s3["3. isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)"]
    s4["4. AliasType"]
    s5["5. ConceptIdentityError"]
    s6["6. validate_alias_value"]
    s7["7. validate_alias_type"]
    s8["8. validate_locator"]
    s9["9. _machine_text"]
    s10["10. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s11["11. ConceptIdentityError"]
    s12["12. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s1 -->|"validate_alias_type(alias_type)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)(value, AliasType)" .-> s3
    s2 -->|"AliasType(value)"| s4
    s2 -->|"ConceptIdentityError('alias_type', #34;must be 'locator' or 'natural-key'#34;)"| s5
    s1 -->|"validate_alias_value(selected, value)"| s6
    s6 -->|"validate_alias_type(alias_type)"| s7
    s6 -->|"validate_locator(value)"| s8
    s8 -->|"_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s10
    s9 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s11
    s9 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)` | - | - | - | - |
| `AliasType` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `validate_alias_value` | `alias_type: AliasType \| str`, `value: object` | `AliasType` | - | `validate_locator(...)`, `validate_natural_key(...)` |
| `validate_alias_type` | `value: AliasType \| str` | `AliasType` | - | `...` |
| `validate_locator` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `WikiSurfaceError` | - | `normalized` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| identity_coordinate_key | validate_alias_type | 504 | `validate_alias_type(alias_type)` |
| validate_alias_type | isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type) | 475 | `isinstance(value, AliasType)` |
| validate_alias_type | AliasType | 475 | `AliasType(value)` |
| validate_alias_type | ConceptIdentityError | 477 | `ConceptIdentityError('alias_type', "must be 'locator' or 'natural-key'")` |
| identity_coordinate_key | validate_alias_value | 505 | `validate_alias_value(selected, value)` |
| validate_alias_value | validate_alias_type | 486 | `validate_alias_type(alias_type)` |
| validate_alias_value | validate_locator | 488 | `validate_locator(value)` |
| validate_locator | _machine_text | 438 | `_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_alias_type` | `isinstance` | 475 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `identity_coordinate_key` | `first 12 steps` | 0 |
| truncated_flow | `identity_coordinate_key` | `depth limit` | 0 |

## Behavior

This flow starts at `identity_coordinate_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
