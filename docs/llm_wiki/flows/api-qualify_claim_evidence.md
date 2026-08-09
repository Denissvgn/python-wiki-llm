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
    participant p5 as isinstance
    participant p6 as strip
    participant p7 as any
    participant p8 as ord
    participant p9 as DocumentationClaimEvidenceError
    participant p10 as fullmatch
    participant p11 as _portable_path
    participant p12 as require_portable_relative_path
    participant p13 as _default_path_error
    participant p14 as SharedValidationError
    participant p15 as fspath
    participant p16 as encode
    participant p17 as replace
    participant p18 as PurePosixPath
    participant p19 as is_absolute
    participant p20 as match
    p0->>p1: _identifier
    p1->>p2: _text
    p2->>p3: require_trimmed_text
    p3->>p4: require_nonempty_text
    p4-->>p5: isinstance
    p4-->>p6: strip
    p4-->>p7: any
    p4-->>p8: ord
    p4-->>p8: ord
    p2->>p9: DocumentationClaimEvidenceError
    p1-->>p10: fullmatch
    p1->>p9: DocumentationClaimEvidenceError
    p0->>p11: _portable_path
    p11->>p2: _text
    p11->>p9: DocumentationClaimEvidenceError
    p11->>p12: require_portable_relative_path
    p12-->>p5: isinstance
    p12->>p13: _default_path_error
    p13->>p14: SharedValidationError
    p12-->>p15: fspath
    p12-->>p5: isinstance
    p12->>p13: _default_path_error
    p12-->>p16: encode
    p12->>p13: _default_path_error
    p12->>p13: _default_path_error
    p12-->>p17: replace
    p12-->>p18: PurePosixPath
    p12-->>p19: is_absolute
    p12-->>p20: match
    p12->>p13: _default_path_error
```

> Call sequence diagram shows 30 of 258 interactions; 228 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
    s6["6. isinstance"]
    s7["7. strip"]
    s8["8. any"]
    s9["9. ord"]
    s10["10. ord"]
    s11["11. DocumentationClaimEvidenceError"]
    s12["12. fullmatch"]
    s1 -->|"_identifier(claim_id, 'claim_id')"| s2
    s2 -->|"_text(value, field_name)"| s3
    s3 -->|"require_trimmed_text(value, error=DocumentationClaimEvidenceError(...))"| s4
    s4 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s5
    s5 -. "isinstance(value, str)" .-> s6
    s5 -. "value.strip(data not statically known)" .-> s7
    s5 -. "any(...)" .-> s8
    s5 -. "ord(character)" .-> s9
    s5 -. "ord(character)" .-> s10
    s3 -->|"DocumentationClaimEvidenceError(...)"| s11
    s2 -. "_SAFE_ID_RE.fullmatch(text)" .-> s12
    click s1 "../modules/documentation_claim_evidence.md"
    click s2 "../modules/documentation_claim_evidence.md"
    click s3 "../modules/documentation_claim_evidence.md"
    click s4 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s11 "../modules/documentation_claim_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `qualify_claim_evidence` | `service: DocumentationGraphQueryService`, `claim_id: str`, `canonical_page: str`, `concept_query: str`, `section_locator: str \| None`, `graph_query: Mapping[str, Any] \| None`, `safe_evidence_link: str \| None`, `internal_evidence_ref: str \| None` | `DocumentationQueryError`, `Mapping`, `_UNEVALUATED_FRESHNESS_DISCLOSURE`, `DocumentationQueryError`, `DocumentationQueryError`, `CLAIM_EVIDENCE_SCHEMA_VERSION` | `bounds[...]`, `bounds[...]` | `record` |
| `_identifier` | `value: object`, `field_name: str` | - | - | `text` |
| `_text` | `value: object`, `field_name: str` | - | - | `require_trimmed_text(...)` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |
| `DocumentationClaimEvidenceError` | - | - | - | - |
| `fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| qualify_claim_evidence | _identifier | 238 | `_identifier(claim_id, 'claim_id')` |
| _identifier | _text | 1362 | `_text(value, field_name)` |
| _text | require_trimmed_text | 1390 | `require_trimmed_text(value, error=DocumentationClaimEvidenceError(...))` |
| require_trimmed_text | require_nonempty_text | 658 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 574 | `isinstance(value, str)` |
| require_nonempty_text | strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any | 582 | `any(...)` |
| require_nonempty_text | ord | 583 | `ord(character)` |
| require_nonempty_text | ord | 584 | `ord(character)` |
| _text | DocumentationClaimEvidenceError | 1392 | `DocumentationClaimEvidenceError(...)` |
| _identifier | fullmatch | 1363 | `_SAFE_ID_RE.fullmatch(text)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_nonempty_text` | `isinstance` | 574 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 576 |
| unresolved_call | `require_nonempty_text` | `any` | 582 |
| unresolved_call | `require_nonempty_text` | `ord` | 583 |
| unresolved_call | `require_nonempty_text` | `ord` | 584 |
| unresolved_call | `_identifier` | `_SAFE_ID_RE.fullmatch` | 1363 |
| step_limit | `qualify_claim_evidence` | `first 12 steps` | 0 |
| truncated_flow | `qualify_claim_evidence` | `depth limit` | 0 |

## Behavior

This flow starts at `qualify_claim_evidence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
