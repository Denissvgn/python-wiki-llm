# validate_natural_key

**Entry point:** `validate_natural_key` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_natural_key
    participant p1 as _machine_text
    participant p2 as text.partition
    participant p3 as _NATURAL_KEY_PREFIX_RE.fullmatch
    participant p4 as _NATURAL_KEY_PAYLOAD_RE.fullmatch
    participant p5 as ConceptIdentityError
    participant p6 as _INVALID_PERCENT_RE.search
    participant p7 as _PERCENT_ESCAPE_RE.finditer
    participant p8 as match.group
    participant p9 as match.group(…).upper
    participant p10 as unquote
    participant p11 as _safe_decoded_coordinate
    participant p12 as quote
    participant p13 as _URI_SCHEME_RE.match
    participant p14 as _contains_uri_userinfo
    participant p15 as _contains_coordinate_userinfo
    participant p16 as _looks_absolute_path
    participant p17 as decoded.split
    participant p18 as path_part.split (src/llm_wiki_cli/services…ty.py:validate_natural_key)
    participant p19 as any (src/llm_wiki_cli/services…ty.py:validate_natural_key)
    participant p20 as path_part.endswith
    p0->>p1: _machine_text
    p0-->>p2: text.partition(':')
    p0-->>p3: _NATURAL_KEY_PREFIX_RE.fullmatch(prefix)
    p0-->>p4: _NATURAL_KEY_PAYLOAD_RE.fullmatch(payload)
    p0->>p5: ConceptIdentityError
    p0-->>p6: _INVALID_PERCENT_RE.search(payload)
    p0->>p5: ConceptIdentityError
    p0-->>p7: _PERCENT_ESCAPE_RE.finditer(payload)
    p0-->>p8: match.group(1)
    p0-->>p9: match.group(…).upper
    p0-->>p8: match.group(1)
    p0->>p5: ConceptIdentityError
    p0-->>p10: unquote(payload, encoding='utf-8', errors='strict')
    p0->>p5: ConceptIdentityError
    p0->>p11: _safe_decoded_coordinate
    p0-->>p12: quote(decoded, safe=_NATURAL_KEY_QUOTE_SAFE)
    p0->>p5: ConceptIdentityError
    p0-->>p13: _URI_SCHEME_RE.match(decoded)
    p0->>p14: _contains_uri_userinfo
    p0->>p15: _contains_coordinate_userinfo
    p0->>p5: ConceptIdentityError
    p0->>p16: _looks_absolute_path
    p0->>p5: ConceptIdentityError
    p0->>p5: ConceptIdentityError
    p0-->>p17: decoded.split(' ', 1)
    p0-->>p18: path_part.split (src/llm_wiki_cli/services…ty.py:validate_natural_key)('/')
    p0-->>p19: any (src/llm_wiki_cli/services…ty.py:validate_natural_key)(...)
    p0-->>p20: path_part.endswith('/')
    p0->>p5: ConceptIdentityError
    p0->>p5: ConceptIdentityError
```

> Call sequence diagram shows 30 of 59 interactions; 29 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 14 (11 omitted); unresolved 12 of 22 (10 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 2 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 2 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 2 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_safe_decoded_coordinate` | 30 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_safe_decoded_coordinate` | 30 | - | external | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_safe_decoded_coordinate` | 30 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 42 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_coordinate_userinfo` | 44 | - | unresolved | 3 |
> Omission summary shows 8 of 10 groups; 2 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_natural_key"]
    s2["2. _machine_text"]
    s3["3. isinstance"]
    s4["4. ConceptIdentityError"]
    s5["5. len"]
    s6["6. ConceptIdentityError"]
    s7["7. value.strip"]
    s8["8. any (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s9["9. character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s10["10. ConceptIdentityError"]
    s11["11. unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -->|"_machine_text(value, 'natural_key', maximum=_MAX_NATURAL_KEY_LENGTH)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s4
    s2 -. "len(value)" .-> s5
    s2 -->|"ConceptIdentityError(field, ...)"| s6
    s2 -. "value.strip(data not statically known)" .-> s7
    s2 -. "any (src/llm_wiki_cli/services…_identity.py:_machine_text)(...)" .-> s8
    s2 -. "character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)(data not statically known)" .-> s9
    s2 -->|"ConceptIdentityError(field, 'must not contain whitespace')"| s10
    s2 -. "unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)('NFC', value)" .-> s11
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
| `validate_natural_key` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `_NATURAL_KEY_QUOTE_SAFE` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any (src/llm_wiki_cli/services…_identity.py:_machine_text)` | - | - | - | - |
| `character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_natural_key | _machine_text | 358 | `_machine_text(value, 'natural_key', maximum=_MAX_NATURAL_KEY_LENGTH)` |
| _machine_text | isinstance | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip | 946 | `value.strip(data not statically known)` |
| _machine_text | any (src/llm_wiki_cli/services…_identity.py:_machine_text) | 946 | `any(...)` |
| _machine_text | character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text) | 946 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 947 | `ConceptIdentityError(field, 'must not contain whitespace')` |
| _machine_text | unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text) | 948 | `unicodedata.normalize('NFC', value)` |
| _machine_text | ConceptIdentityError | 949 | `ConceptIdentityError(field, 'must use Unicode NFC normalization')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_machine_text` | `isinstance` | 942 |
| unresolved_call | `_machine_text` | `value.strip` | 946 |
| external_call | `_machine_text` | `any` | 946 |
| unresolved_call | `_machine_text` | `character.isspace` | 946 |
| external_call | `_machine_text` | `unicodedata.normalize` | 948 |
| step_limit | `validate_natural_key` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_natural_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
