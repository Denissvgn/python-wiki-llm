# derive_concept_uid

**Entry point:** `derive_concept_uid` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as derive_concept_uid (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p1 as derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py)
    participant p2 as validate_bundle_id
    participant p3 as _machine_text
    participant p4 as isinstance
    participant p5 as ConceptIdentityError
    participant p6 as len
    participant p7 as value.strip
    participant p8 as any (src/llm_wiki_cli/services…_identity.py:_machine_text)
    participant p9 as character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)
    participant p10 as unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)
    participant p11 as unicodedata.category(…).startswith (src/llm_wiki_cli/services…_identity.py:_machine_text)
    participant p12 as unicodedata.category (src/llm_wiki_cli/services…_identity.py:_machine_text)
    participant p13 as _BUNDLE_ID_RE.fullmatch
    participant p14 as text.casefold
    participant p15 as _looks_absolute_path
    participant p16 as value.startswith
    participant p17 as _WINDOWS_ABSOLUTE_RE.match
    participant p18 as _contains_uri_userinfo
    participant p19 as urlsplit
    participant p20 as validate_concept_kind
    participant p21 as _QUALIFIED_KIND_RE.fullmatch
    participant p22 as validate_natural_key
    p0->>p1: derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py)
    p1->>p2: validate_bundle_id
    p2->>p3: _machine_text
    p3-->>p4: isinstance
    p3->>p5: ConceptIdentityError
    p3-->>p6: len
    p3->>p5: ConceptIdentityError
    p3-->>p7: value.strip
    p3-->>p8: any (src/llm_wiki_cli/services…_identity.py:_machine_text)
    p3-->>p9: character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)
    p3->>p5: ConceptIdentityError
    p3-->>p10: unicodedata.normalize (src/llm_wiki_cli/services…_identity.py:_machine_text)
    p3->>p5: ConceptIdentityError
    p3-->>p8: any (src/llm_wiki_cli/services…_identity.py:_machine_text)
    p3-->>p11: unicodedata.category(…).startswith (src/llm_wiki_cli/services…_identity.py:_machine_text)
    p3-->>p12: unicodedata.category (src/llm_wiki_cli/services…_identity.py:_machine_text)
    p3->>p5: ConceptIdentityError
    p2-->>p13: _BUNDLE_ID_RE.fullmatch
    p2-->>p14: text.casefold
    p2->>p15: _looks_absolute_path
    p15-->>p16: value.startswith
    p15-->>p17: _WINDOWS_ABSOLUTE_RE.match
    p2->>p18: _contains_uri_userinfo
    p18-->>p19: urlsplit
    p2->>p5: ConceptIdentityError
    p1->>p20: validate_concept_kind
    p20->>p3: _machine_text
    p20-->>p21: _QUALIFIED_KIND_RE.fullmatch
    p20->>p5: ConceptIdentityError
    p1->>p22: validate_natural_key
```

> Call sequence diagram shows 30 of 79 interactions; 49 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. derive_concept_uid (src/llm_wiki_cli/services/knowledge_governance.py)"]
    s2["2. derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py)"]
    s3["3. validate_bundle_id"]
    s4["4. _machine_text"]
    s5["5. isinstance"]
    s6["6. ConceptIdentityError"]
    s7["7. len"]
    s8["8. ConceptIdentityError"]
    s9["9. value.strip"]
    s10["10. any (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s11["11. character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -->|"derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py)(bundle_id, concept_kind, natural_key)"| s2
    s2 -->|"validate_bundle_id(bundle_id)"| s3
    s3 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s4
    s4 -. "isinstance(value, str)" .-> s5
    s4 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s6
    s4 -. "len(value)" .-> s7
    s4 -->|"ConceptIdentityError(field, ...)"| s8
    s4 -. "value.strip(data not statically known)" .-> s9
    s4 -. "any (src/llm_wiki_cli/services…_identity.py:_machine_text)(...)" .-> s10
    s4 -. "character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text)(data not statically known)" .-> s11
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
| `derive_concept_uid (src/llm_wiki_cli/services/knowledge_governance.py)` | `bundle_id: str`, `concept_kind: str`, `natural_key: str` | `ConceptIdentityError` | - | `_derive_identity_uid(...)` |
| `derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py)` | `bundle_id: object`, `concept_kind: object`, `natural_key: object` | `CONCEPT_UID_HEX_LENGTH` | - | `...` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| derive_concept_uid (src/llm_wiki_cli/services/knowledge_governance.py) | derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py) | 407 | `_derive_identity_uid(bundle_id, concept_kind, natural_key)` |
| derive_concept_uid (src/llm_wiki_cli/services/concept_identity.py) | validate_bundle_id | 504 | `validate_bundle_id(bundle_id)` |
| validate_bundle_id | _machine_text | 288 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |
| _machine_text | value.strip | 916 | `value.strip(data not statically known)` |
| _machine_text | any (src/llm_wiki_cli/services…_identity.py:_machine_text) | 916 | `any(...)` |
| _machine_text | character.isspace (src/llm_wiki_cli/services…_identity.py:_machine_text) | 916 | `character.isspace(data not statically known)` |
| _machine_text | ConceptIdentityError | 917 | `ConceptIdentityError(field, 'must not contain whitespace')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| external_call | `_machine_text` | `any` | 916 |
| unresolved_call | `_machine_text` | `character.isspace` | 916 |
| step_limit | `derive_concept_uid` | `first 12 steps` | 0 |

## Behavior

This flow starts at `derive_concept_uid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
