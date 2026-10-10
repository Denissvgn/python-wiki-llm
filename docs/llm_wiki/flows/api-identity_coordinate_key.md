# identity_coordinate_key

**Entry point:** `identity_coordinate_key` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as identity_coordinate_key
    participant p1 as validate_alias_type
    participant p2 as validate_alias_value
    participant p3 as normalized.startswith
    participant p4 as iter_page_kinds
    participant p5 as canonical_path
    participant p6 as mcp_uri
    participant p7 as normalized.endswith
    participant p8 as len (src/llm_wiki_cli/services…y:identity_coordinate_key)
    participant p9 as AssertionError
    participant p10 as isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)
    participant p11 as AliasType
    participant p12 as validate_locator
    participant p13 as ConceptIdentityError
    participant p14 as validate_natural_key
    participant p15 as _machine_text
    participant p16 as _contains_uri_userinfo
    participant p17 as text.partition
    participant p18 as _looks_absolute_path
    participant p19 as _NATURAL_KEY_PREFIX_RE.fullmatch
    participant p20 as _NATURAL_KEY_PAYLOAD_RE.fullmatch
    participant p21 as validate_exact_page_coordinate
    participant p22 as _INVALID_PERCENT_RE.search
    p0->>p1: validate_alias_type
    p0->>p2: validate_alias_value
    p0-->>p3: normalized.startswith('llm-wiki://')
    p0->>p4: iter_page_kinds
    p0->>p5: canonical_path
    p0->>p6: mcp_uri
    p0-->>p3: normalized.startswith(prefix)
    p0-->>p7: normalized.endswith('.md')
    p0-->>p8: len (src/llm_wiki_cli/services…y:identity_coordinate_key)(prefix)
    p0-->>p8: len (src/llm_wiki_cli/services…y:identity_coordinate_key)('.md')
    p0->>p6: mcp_uri
    p0-->>p9: AssertionError('validated locator was absent from the surface registry')
    p1-->>p10: isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)(value, AliasType)
    p2->>p1: validate_alias_type
    p1->>p11: AliasType
    p2->>p12: validate_locator
    p1->>p13: ConceptIdentityError
    p2->>p14: validate_natural_key
    p12->>p15: _machine_text
    p14->>p15: _machine_text
    p12->>p16: _contains_uri_userinfo
    p14-->>p17: text.partition(':')
    p12->>p18: _looks_absolute_path
    p14-->>p19: _NATURAL_KEY_PREFIX_RE.fullmatch(prefix)
    p12->>p13: ConceptIdentityError
    p14-->>p20: _NATURAL_KEY_PAYLOAD_RE.fullmatch(payload)
    p12->>p21: validate_exact_page_coordinate
    p14->>p13: ConceptIdentityError
    p12->>p13: ConceptIdentityError
    p14-->>p22: _INVALID_PERCENT_RE.search(payload)
```

> Call sequence diagram shows 30 of 125 interactions; 95 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 33 (29 omitted); unresolved 7 of 33 (26 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 9 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 9 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 9 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 24 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 26 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 30 | - | external | 4 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 30 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 30 | [src/llm_wiki_cli/services/wiki_surface.py](../modules/wiki_surface.md) | internal | 7 |
> Omission summary shows 8 of 30 groups; 22 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_alias_type` | `isinstance` | 475 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `identity_coordinate_key` | `first 12 steps` | 0 |
| truncated_flow | `identity_coordinate_key` | `depth limit` | 0 |

## Behavior

This flow starts at `identity_coordinate_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
