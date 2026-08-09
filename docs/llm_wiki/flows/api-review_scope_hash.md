# review_scope_hash

**Entry point:** `review_scope_hash` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as review_scope_hash
    participant p1 as _section_locator
    participant p2 as isinstance
    participant p3 as startswith
    participant p4 as strip
    participant p5 as GovernanceError
    participant p6 as _safe_text
    participant p7 as require_no_control_characters
    participant p8 as contains_control_character
    participant p9 as any
    participant p10 as ord
    participant p11 as search
    participant p12 as contains_uri_authority_userinfo
    participant p13 as index
    participant p14 as split
    participant p15 as len
    participant p16 as endswith
    participant p17 as _uri_candidate_contains_authority_userinfo
    participant p18 as match
    participant p19 as urlsplit
    participant p20 as bool
    p0->>p1: _section_locator
    p1-->>p2: isinstance
    p1-->>p3: startswith
    p1-->>p4: strip
    p1->>p5: GovernanceError
    p1->>p6: _safe_text
    p6->>p7: require_no_control_characters
    p7-->>p2: isinstance
    p7->>p8: contains_control_character
    p8-->>p9: any
    p8-->>p10: ord
    p8-->>p10: ord
    p6->>p5: GovernanceError
    p6-->>p11: search
    p6->>p5: GovernanceError
    p6->>p12: contains_uri_authority_userinfo
    p12-->>p4: strip
    p12-->>p3: startswith
    p12-->>p13: index
    p12-->>p4: strip
    p12-->>p14: split
    p12-->>p15: len
    p12-->>p3: startswith
    p12-->>p16: endswith
    p12-->>p4: strip
    p12->>p17: _uri_candidate_contains_authority_userinfo
    p17-->>p18: match
    p17-->>p19: urlsplit
    p17-->>p20: bool
    p12-->>p14: split
```

> Call sequence diagram shows 30 of 60 interactions; 30 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. review_scope_hash"]
    s2["2. _section_locator"]
    s3["3. isinstance"]
    s4["4. startswith"]
    s5["5. strip"]
    s6["6. GovernanceError"]
    s7["7. _safe_text"]
    s8["8. require_no_control_characters"]
    s9["9. isinstance"]
    s10["10. contains_control_character"]
    s11["11. any"]
    s12["12. ord"]
    s1 -->|"_section_locator(section_locator, 'section_locator')"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "value.startswith('llm-wiki://')" .-> s4
    s2 -. "value.strip(data not statically known)" .-> s5
    s2 -->|"GovernanceError(path, 'must be an exact llm-wiki section locator')"| s6
    s2 -->|"_safe_text(value, path)"| s7
    s7 -->|"require_no_control_characters(value, error=GovernanceError(...), reject_delete_character=True)"| s8
    s8 -. "isinstance(value, str)" .-> s9
    s8 -->|"contains_control_character(value, reject_delete_character=reject_delete_character)"| s10
    s10 -. "any(...)" .-> s11
    s10 -. "ord(character)" .-> s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s7 "../modules/knowledge_governance.md"
    click s8 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `review_scope_hash` | `knowledge: KnowledgeIndex`, `section_locator: str` | - | - | `semantic_hash` |
| `_section_locator` | `value: object`, `path: str` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `startswith` | - | - | - | - |
| `strip` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_safe_text` | `value: str`, `path: str` | - | - | - |
| `require_no_control_characters` | `value: object`, `error: Exception`, `reject_delete_character: bool` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | - | - | `any(...)` |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| review_scope_hash | _section_locator | 1536 | `_section_locator(section_locator, 'section_locator')` |
| _section_locator | isinstance | 3323 | `isinstance(value, str)` |
| _section_locator | startswith | 3324 | `value.startswith('llm-wiki://')` |
| _section_locator | strip | 3327 | `value.strip(data not statically known)` |
| _section_locator | GovernanceError | 3329 | `GovernanceError(path, 'must be an exact llm-wiki section locator')` |
| _section_locator | _safe_text | 3333 | `_safe_text(value, path)` |
| _safe_text | require_no_control_characters | 3241 | `require_no_control_characters(value, error=GovernanceError(...), reject_delete_character=True)` |
| require_no_control_characters | isinstance | 628 | `isinstance(value, str)` |
| require_no_control_characters | contains_control_character | 628 | `contains_control_character(value, reject_delete_character=reject_delete_character)` |
| contains_control_character | any | 643 | `any(...)` |
| contains_control_character | ord | 644 | `ord(character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_section_locator` | `isinstance` | 3323 |
| unresolved_call | `_section_locator` | `value.startswith` | 3324 |
| unresolved_call | `_section_locator` | `value.strip` | 3327 |
| unresolved_call | `require_no_control_characters` | `isinstance` | 628 |
| unresolved_call | `contains_control_character` | `any` | 643 |
| unresolved_call | `contains_control_character` | `ord` | 644 |
| step_limit | `review_scope_hash` | `first 12 steps` | 0 |

## Behavior

This flow starts at `review_scope_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
