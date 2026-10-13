# review_scope_hash

**Entry point:** `review_scope_hash` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), and 2 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as review_scope_hash
    participant p1 as _section_locator
    participant p2 as _section_records_by_locator
    participant p3 as GovernanceError
    participant p4 as is_valid_sha256
    participant p5 as validate_locator
    participant p6 as require_no_control_characters
    participant p7 as contains_uri_authority_userinfo
    participant p8 as _machine_text
    participant p9 as validate_exact_page_coordinate
    participant p10 as _matches_directory_path
    participant p11 as _matches_directory_uri
    participant p12 as is_safe_page_id
    participant p13 as canonical_path
    participant p14 as mcp_uri
    participant p15 as _contains_uri_userinfo
    participant p16 as contains_control_character
    participant p17 as _looks_absolute_path
    participant p18 as ConceptIdentityError
    participant p19 as _uri_candidate_contains_authority_userinfo
    participant p20 as WikiSurfaceError
    participant p21 as _entry_for
    participant p22 as _validate_page_id
    participant p23 as is_portable_path_component
    participant p24 as isinstance (src/llm_wiki_cli/services…ance.py:review_scope_hash)
    participant p25 as sections.get
    participant p26 as section.get (src/llm_wiki_cli/services…ance.py:review_scope_hash)
    participant p27 as isinstance (src/llm_wiki_cli/services…nance.py:_section_locator)
    participant p28 as knowledge.extensions.get
    participant p29 as isinstance (src/llm_wiki_cli/services…idence.py:is_valid_sha256)
    participant p30 as value.startswith (src/llm_wiki_cli/services…nance.py:_section_locator)
    p0->>p1: _section_locator
    p0->>p2: _section_records_by_locator
    p0->>p3: GovernanceError
    p0->>p4: is_valid_sha256
    p1->>p5: validate_locator
    p1->>p6: require_no_control_characters
    p1->>p7: contains_uri_authority_userinfo
    p5->>p8: _machine_text
    p5->>p9: validate_exact_page_coordinate
    p9->>p10: _matches_directory_path
    p9->>p11: _matches_directory_uri
    p10->>p12: is_safe_page_id
    p10->>p13: canonical_path
    p11->>p14: mcp_uri
    p5->>p15: _contains_uri_userinfo
    p6->>p16: contains_control_character
    p5->>p17: _looks_absolute_path
    p5->>p18: ConceptIdentityError
    p7->>p19: _uri_candidate_contains_authority_userinfo
    p9->>p20: WikiSurfaceError
    p13->>p21: _entry_for
    p13->>p22: _validate_page_id
    p12->>p23: is_portable_path_component
    p0-->>p24: isinstance (src/llm_wiki_cli/services…ance.py:review_scope_hash)(semantic_hash, str)
    p0-->>p25: sections.get(selected)
    p0-->>p26: section.get (src/llm_wiki_cli/services…ance.py:review_scope_hash)('semantic_hash')
    p1-->>p27: isinstance (src/llm_wiki_cli/services…nance.py:_section_locator)(value, str)
    p2-->>p28: knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    p4-->>p29: isinstance (src/llm_wiki_cli/services…idence.py:is_valid_sha256)(value, str)
    p1-->>p30: value.startswith (src/llm_wiki_cli/services…nance.py:_section_locator)('llm-wiki://')
```

> Call sequence diagram shows 30 of 121 interactions; 91 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 35 (32 omitted); unresolved 4 of 39 (35 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:_section_locator` | 2 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_section_locator` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 10 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 10 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 10 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 25 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 27 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/wiki_surface.py:validate_exact_page_coordinate` | 31 | - | external | 4 |
> Omission summary shows 8 of 33 groups; 25 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. review_scope_hash"]
    s2["2. _section_locator"]
    s3["3. isinstance (src/llm_wiki_cli/services…nance.py:_section_locator)"]
    s4["4. value.startswith (src/llm_wiki_cli/services…nance.py:_section_locator)"]
    s5["5. value.strip (src/llm_wiki_cli/services…nance.py:_section_locator)"]
    s6["6. GovernanceError"]
    s7["7. value.partition"]
    s8["8. GovernanceError"]
    s9["9. validate_locator"]
    s10["10. _machine_text"]
    s11["11. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -->|"_section_locator(section_locator, 'section_locator')"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…nance.py:_section_locator)(value, str)" .-> s3
    s2 -. "value.startswith (src/llm_wiki_cli/services…nance.py:_section_locator)('llm-wiki://')" .-> s4
    s2 -. "value.strip (src/llm_wiki_cli/services…nance.py:_section_locator)(data not statically known)" .-> s5
    s2 -->|"GovernanceError(path, 'must be an exact llm-wiki section locator')"| s6
    s2 -. "value.partition('#35;section/')" .-> s7
    s2 -->|"GovernanceError(path, 'must contain a section coordinate')"| s8
    s2 -->|"validate_locator(page_locator)"| s9
    s9 -->|"_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s11
    s10 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s8 "../modules/knowledge_governance.md"
    click s9 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `review_scope_hash` | `knowledge: KnowledgeIndex`, `section_locator: str` | - | - | `semantic_hash` |
| `_section_locator` | `value: object`, `path: str` | `ConceptIdentityError` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…nance.py:_section_locator)` | - | - | - | - |
| `value.startswith (src/llm_wiki_cli/services…nance.py:_section_locator)` | - | - | - | - |
| `value.strip (src/llm_wiki_cli/services…nance.py:_section_locator)` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `value.partition` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `validate_locator` | `value: object` | `_MAX_NATURAL_KEY_LENGTH`, `WikiSurfaceError` | - | `normalized` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| review_scope_hash | _section_locator | 1549 | `_section_locator(section_locator, 'section_locator')` |
| _section_locator | isinstance (src/llm_wiki_cli/services…nance.py:_section_locator) | 3318 | `isinstance(value, str)` |
| _section_locator | value.startswith (src/llm_wiki_cli/services…nance.py:_section_locator) | 3319 | `value.startswith('llm-wiki://')` |
| _section_locator | value.strip (src/llm_wiki_cli/services…nance.py:_section_locator) | 3322 | `value.strip(data not statically known)` |
| _section_locator | GovernanceError | 3324 | `GovernanceError(path, 'must be an exact llm-wiki section locator')` |
| _section_locator | value.partition | 3328 | `value.partition('#section/')` |
| _section_locator | GovernanceError | 3330 | `GovernanceError(path, 'must contain a section coordinate')` |
| _section_locator | validate_locator | 3332 | `validate_locator(page_locator)` |
| validate_locator | _machine_text | 438 | `_machine_text(value, 'locator', maximum=_MAX_NATURAL_KEY_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_section_locator` | `isinstance` | 3318 |
| unresolved_call | `_section_locator` | `value.startswith` | 3319 |
| unresolved_call | `_section_locator` | `value.strip` | 3322 |
| unresolved_call | `_section_locator` | `value.partition` | 3328 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `review_scope_hash` | `first 12 steps` | 0 |
| truncated_flow | `review_scope_hash` | `depth limit` | 0 |

## Behavior

This flow starts at `review_scope_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
