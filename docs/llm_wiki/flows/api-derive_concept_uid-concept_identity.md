# derive_concept_uid

**Entry point:** `derive_concept_uid` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as derive_concept_uid
    participant p1 as validate_bundle_id
    participant p2 as validate_concept_kind
    participant p3 as validate_natural_key
    participant p4 as _uid_tag
    participant p5 as _machine_text
    participant p6 as _safe_decoded_coordinate
    participant p7 as ConceptIdentityError
    participant p8 as _looks_absolute_path
    participant p9 as _contains_uri_userinfo
    participant p10 as _contains_coordinate_userinfo
    participant p11 as json.dumps
    participant p12 as json.dumps(…).encode
    participant p13 as hashlib.sha256(…).hexdigest
    participant p14 as hashlib.sha256
    participant p15 as _UID_TAG_BY_KIND.get
    participant p16 as _BUNDLE_ID_RE.fullmatch
    participant p17 as _QUALIFIED_KIND_RE.fullmatch
    participant p18 as text.partition
    participant p19 as text.casefold
    participant p20 as _NATURAL_KEY_PREFIX_RE.fullmatch
    participant p21 as _NATURAL_KEY_PAYLOAD_RE.fullmatch
    participant p22 as _INVALID_PERCENT_RE.search
    participant p23 as _PERCENT_ESCAPE_RE.finditer
    participant p24 as match.group
    participant p25 as match.group(…).upper
    participant p26 as unquote
    participant p27 as quote
    participant p28 as _URI_SCHEME_RE.match
    participant p29 as decoded.split
    p0->>p1: validate_bundle_id
    p0->>p2: validate_concept_kind
    p0->>p3: validate_natural_key
    p0->>p4: _uid_tag
    p1->>p5: _machine_text
    p3->>p6: _safe_decoded_coordinate
    p2->>p7: ConceptIdentityError
    p1->>p8: _looks_absolute_path
    p1->>p9: _contains_uri_userinfo
    p3->>p10: _contains_coordinate_userinfo
    p0-->>p11: json.dumps({...}, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)
    p0-->>p12: json.dumps(…).encode('utf-8')
    p0-->>p13: hashlib.sha256(…).hexdigest
    p0-->>p14: hashlib.sha256(encoded)
    p4-->>p15: _UID_TAG_BY_KIND.get(concept_kind, 'concept')
    p1-->>p16: _BUNDLE_ID_RE.fullmatch(text)
    p2-->>p17: _QUALIFIED_KIND_RE.fullmatch(text)
    p3-->>p18: text.partition(':')
    p1-->>p19: text.casefold
    p3-->>p20: _NATURAL_KEY_PREFIX_RE.fullmatch(prefix)
    p3-->>p21: _NATURAL_KEY_PAYLOAD_RE.fullmatch(payload)
    p3-->>p22: _INVALID_PERCENT_RE.search(payload)
    p3-->>p23: _PERCENT_ESCAPE_RE.finditer(payload)
    p3-->>p24: match.group(1)
    p3-->>p25: match.group(…).upper
    p3-->>p24: match.group(1)
    p3-->>p26: unquote(payload, encoding='utf-8', errors='strict')
    p3-->>p27: quote(decoded, safe=_NATURAL_KEY_QUOTE_SAFE)
    p3-->>p28: _URI_SCHEME_RE.match(decoded)
    p3-->>p29: decoded.split(' ', 1)
```

> Call sequence diagram shows 30 of 77 interactions; 47 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 16 (12 omitted); unresolved 16 of 28 (12 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 3 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 3 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 20 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 23 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 2 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_concept_kind` | 26 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_natural_key` | 30 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 13 |
> Omission summary shows 8 of 15 groups; 7 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. derive_concept_uid"]
    s2["2. validate_bundle_id"]
    s3["3. _machine_text"]
    s4["4. isinstance"]
    s5["5. ConceptIdentityError"]
    s6["6. len"]
    s7["7. ConceptIdentityError"]
    s8["8. value.strip"]
    s9["9. any (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s10["10. character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s11["11. ConceptIdentityError"]
    s12["12. unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s1 -->|"validate_bundle_id(bundle_id)"| s2
    s2 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s5
    s3 -. "len(value)" .-> s6
    s3 -->|"ConceptIdentityError(field, ...)"| s7
    s3 -. "value.strip(data not statically known)" .-> s8
    s3 -. "any (src/llm_wiki_cli/services…_identity.py:_machine_text)(...)" .-> s9
    s3 -. "character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)(data not statically known)" .-> s10
    s3 -->|"ConceptIdentityError(field, 'must not contain whitespace')"| s11
    s3 -. "unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)('NFC', value)" .-> s12
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s3 "../modules/concept_identity.md"
    click s5 "../modules/concept_identity.md"
    click s7 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `derive_concept_uid` | `bundle_id: object`, `concept_kind: object`, `natural_key: object` | `CONCEPT_UID_HEX_LENGTH` | - | `...` |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| derive_concept_uid | validate_bundle_id | 534 | `validate_bundle_id(bundle_id)` |
| validate_bundle_id | _machine_text | 289 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip | 946 | `value.strip(data not statically known)` |
| _machine_text | any (src/llm_wiki_cli/services…_identity.py:_machine_text) | 946 | `any(...)` |
| _machine_text | character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text) | 946 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 947 | `ConceptIdentityError(field, 'must not contain whitespace')` |
| _machine_text | unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text) | 948 | `unicodedata.normalize('NFC', value)` |

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
| step_limit | `derive_concept_uid` | `first 12 steps` | 0 |

## Behavior

This flow starts at `derive_concept_uid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
