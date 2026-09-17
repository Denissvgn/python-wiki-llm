# qualify_claim_evidence

**Entry point:** `qualify_claim_evidence` (`api`)
**Source:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md)
**Modules touched:** [documentation_claim_evidence](../modules/documentation_claim_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as qualify_claim_evidence
    participant p1 as _identifier
    participant p2 as _text
    participant p3 as require_trimmed_text
    participant p4 as require_nonempty_text
    participant p5 as isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    participant p6 as value.strip
    participant p7 as contains_control_character
    participant p8 as pattern.search
    participant p9 as DocumentationClaimEvidenceError
    participant p10 as _SAFE_ID_RE.fullmatch
    participant p11 as _portable_path
    participant p12 as require_portable_relative_path
    participant p13 as isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    participant p14 as _default_path_error
    participant p15 as SharedValidationError
    participant p16 as os.fspath
    participant p17 as _syntax_key
    participant p18 as type
    participant p19 as len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p20 as any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p21 as _known_syntax
    participant p22 as _PATH_SYNTAX.get
    p0->>p1: _identifier
    p1->>p2: _text
    p2->>p3: require_trimmed_text
    p3->>p4: require_nonempty_text
    p4-->>p5: isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    p4-->>p6: value.strip
    p4->>p7: contains_control_character
    p7-->>p8: pattern.search
    p2->>p9: DocumentationClaimEvidenceError
    p1-->>p10: _SAFE_ID_RE.fullmatch
    p1->>p9: DocumentationClaimEvidenceError
    p0->>p11: _portable_path
    p11->>p2: _text
    p11->>p9: DocumentationClaimEvidenceError
    p11->>p12: require_portable_relative_path
    p12-->>p13: isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    p12->>p14: _default_path_error
    p14->>p15: SharedValidationError
    p12-->>p16: os.fspath
    p12-->>p13: isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    p12->>p14: _default_path_error
    p12->>p17: _syntax_key
    p17-->>p18: type
    p17-->>p19: len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p17-->>p20: any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p17-->>p18: type
    p17-->>p18: type
    p17-->>p19: len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p12->>p21: _known_syntax
    p21-->>p22: _PATH_SYNTAX.get
```

> Call sequence diagram shows 30 of 273 interactions; 243 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. qualify_claim_evidence"]
    s2["2. _identifier"]
    s3["3. _text"]
    s4["4. require_trimmed_text"]
    s5["5. require_nonempty_text"]
    s6["6. isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)"]
    s7["7. value.strip"]
    s8["8. contains_control_character"]
    s9["9. pattern.search"]
    s10["10. DocumentationClaimEvidenceError"]
    s11["11. _SAFE_ID_RE.fullmatch"]
    s12["12. DocumentationClaimEvidenceError"]
    s1 -->|"_identifier(claim_id, 'claim_id')"| s2
    s2 -->|"_text(value, field_name)"| s3
    s3 -->|"require_trimmed_text(value, error=DocumentationClaimEvidenceError(...))"| s4
    s4 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)(value, str)" .-> s6
    s5 -. "value.strip(data not statically known)" .-> s7
    s5 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s8
    s8 -. "pattern.search(value)" .-> s9
    s3 -->|"DocumentationClaimEvidenceError(...)"| s10
    s2 -. "_SAFE_ID_RE.fullmatch(text)" .-> s11
    s2 -->|"DocumentationClaimEvidenceError(...)"| s12
    click s1 "../modules/documentation_claim_evidence.md"
    click s2 "../modules/documentation_claim_evidence.md"
    click s3 "../modules/documentation_claim_evidence.md"
    click s4 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s10 "../modules/documentation_claim_evidence.md"
    click s12 "../modules/documentation_claim_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `qualify_claim_evidence` | `service: DocumentationGraphQueryService`, `claim_id: str`, `canonical_page: str`, `concept_query: str`, `section_locator: str \| None`, `graph_query: Mapping[str, Any] \| None`, `safe_evidence_link: str \| None`, `internal_evidence_ref: str \| None` | `DocumentationQueryError`, `Mapping`, `_UNEVALUATED_FRESHNESS_DISCLOSURE`, `DocumentationQueryError`, `DocumentationQueryError`, `CLAIM_EVIDENCE_SCHEMA_VERSION` | `bounds[...]`, `bounds[...]` | `record` |
| `_identifier` | `value: object`, `field_name: str` | - | - | `text` |
| `_text` | `value: object`, `field_name: str` | - | - | `require_trimmed_text(...)` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `_SAFE_ID_RE.fullmatch` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| qualify_claim_evidence | _identifier | 238 | `_identifier(claim_id, 'claim_id')` |
| _identifier | _text | 1362 | `_text(value, field_name)` |
| _text | require_trimmed_text | 1390 | `require_trimmed_text(value, error=DocumentationClaimEvidenceError(...))` |
| require_trimmed_text | require_nonempty_text | 696 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services….py:require_nonempty_text) | 623 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 625 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 631 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |
| _text | DocumentationClaimEvidenceError | 1392 | `DocumentationClaimEvidenceError(...)` |
| _identifier | _SAFE_ID_RE.fullmatch | 1363 | `_SAFE_ID_RE.fullmatch(text)` |
| _identifier | DocumentationClaimEvidenceError | 1364 | `DocumentationClaimEvidenceError(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_nonempty_text` | `isinstance` | 623 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 625 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| unresolved_call | `_identifier` | `_SAFE_ID_RE.fullmatch` | 1363 |
| step_limit | `qualify_claim_evidence` | `first 12 steps` | 0 |
| truncated_flow | `qualify_claim_evidence` | `depth limit` | 0 |

## Behavior

This flow starts at `qualify_claim_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
