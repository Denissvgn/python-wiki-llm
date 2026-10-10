# validate_alias_value

**Entry point:** `validate_alias_value` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_alias_value
    participant p1 as validate_alias_type
    participant p2 as validate_locator
    participant p3 as validate_natural_key
    participant p4 as isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)
    participant p5 as _machine_text
    participant p6 as AliasType
    participant p7 as _contains_uri_userinfo
    participant p8 as text.partition
    participant p9 as ConceptIdentityError
    participant p10 as _looks_absolute_path
    participant p11 as _NATURAL_KEY_PREFIX_RE.fullmatch
    participant p12 as _NATURAL_KEY_PAYLOAD_RE.fullmatch
    participant p13 as validate_exact_page_coordinate
    participant p14 as _INVALID_PERCENT_RE.search
    participant p15 as _PERCENT_ESCAPE_RE.finditer
    participant p16 as match.group
    participant p17 as match.group(…).upper
    participant p18 as unquote (src/llm_wiki_cli/services…y.py:validate_natural_key)
    participant p19 as _safe_decoded_coordinate
    participant p20 as quote (src/llm_wiki_cli/services…y.py:validate_natural_key)
    p0->>p1: validate_alias_type
    p0->>p2: validate_locator
    p0->>p3: validate_natural_key
    p1-->>p4: isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)(value, AliasType)
    p2->>p5: _machine_text
    p3->>p5: _machine_text
    p1->>p6: AliasType
    p2->>p7: _contains_uri_userinfo
    p3-->>p8: text.partition(':')
    p1->>p9: ConceptIdentityError
    p2->>p10: _looks_absolute_path
    p3-->>p11: _NATURAL_KEY_PREFIX_RE.fullmatch(prefix)
    p2->>p9: ConceptIdentityError
    p3-->>p12: _NATURAL_KEY_PAYLOAD_RE.fullmatch(payload)
    p2->>p13: validate_exact_page_coordinate
    p3->>p9: ConceptIdentityError
    p2->>p9: ConceptIdentityError
    p3-->>p14: _INVALID_PERCENT_RE.search(payload)
    p2->>p9: ConceptIdentityError
    p3->>p9: ConceptIdentityError
    p3-->>p15: _PERCENT_ESCAPE_RE.finditer(payload)
    p3-->>p16: match.group(1)
    p3-->>p17: match.group(…).upper
    p3-->>p16: match.group(1)
    p3->>p9: ConceptIdentityError
    p3-->>p18: unquote (src/llm_wiki_cli/services…y.py:validate_natural_key)(payload, encoding='utf-8', errors='strict')
    p3->>p9: ConceptIdentityError
    p3->>p19: _safe_decoded_coordinate
    p3-->>p20: quote (src/llm_wiki_cli/services…y.py:validate_natural_key)(decoded, safe=_NATURAL_KEY_QUOTE_SAFE)
    p3->>p9: ConceptIdentityError
```

> Call sequence diagram shows 30 of 121 interactions; 91 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 31 (28 omitted); unresolved 8 of 30 (22 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 7 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 7 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 22 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 24 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 28 | - | external | 4 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 28 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 28 | [src/llm_wiki_cli/services/wiki_surface.py](../modules/wiki_surface.md) | internal | 7 |
> Omission summary shows 8 of 33 groups; 25 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_alias_value"]
    s2["2. validate_alias_type"]
    s3["3. isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)"]
    s4["4. AliasType"]
    s5["5. ConceptIdentityError"]
    s6["6. validate_locator"]
    s7["7. _machine_text"]
    s8["8. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s9["9. ConceptIdentityError"]
    s10["10. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s11["11. ConceptIdentityError"]
    s12["12. value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s1 -->|"validate_alias_type(alias_type)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)(value, AliasType)" .-> s3
    s2 -->|"AliasType(value)"| s4
    s2 -->|"ConceptIdentityError('alias_type', #34;must be 'locator' or 'natural-key'#34;)"| s5
    s1 -->|"validate_locator(value)"| s6
    s6 -->|"_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s8
    s7 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s9
    s7 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s10
    s7 -->|"ConceptIdentityError(field, ...)"| s11
    s7 -. "value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)(data not statically known)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)` | - | - | - | - |
| `AliasType` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `validate_locator` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `WikiSurfaceError` | - | `normalized` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_alias_value | validate_alias_type | 486 | `validate_alias_type(alias_type)` |
| validate_alias_type | isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type) | 475 | `isinstance(value, AliasType)` |
| validate_alias_type | AliasType | 475 | `AliasType(value)` |
| validate_alias_type | ConceptIdentityError | 477 | `ConceptIdentityError('alias_type', "must be 'locator' or 'natural-key'")` |
| validate_alias_value | validate_locator | 488 | `validate_locator(value)` |
| validate_locator | _machine_text | 438 | `_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip (src/llm_wiki_cli/services…identity.py:_machine_text) | 946 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_alias_type` | `isinstance` | 475 |
| external_call | `_machine_text` | `isinstance` | 942 |
| unresolved_call | `_machine_text` | `value.strip` | 946 |
| step_limit | `validate_alias_value` | `first 12 steps` | 0 |
| truncated_flow | `validate_alias_value` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_alias_value` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
