# build_artifact_verification_context

**Entry point:** `build_artifact_verification_context` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 8 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_artifact_verification_context
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _sha256
    participant p4 as require_sha256
    participant p5 as require_trimmed_text
    participant p6 as require_nonempty_text
    participant p7 as strip
    participant p8 as any
    participant p9 as ord
    participant p10 as fullmatch
    participant p11 as VerificationContractError
    participant p12 as knowledge_index_to_payload
    participant p13 as _emit_extensions
    participant p14 as _parse_extensions
    participant p15 as _object
    participant p16 as dict
    participant p17 as require_mapping
    participant p18 as encode
    participant p19 as KnowledgeModelError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: _sha256
    p3->>p4: require_sha256
    p4-->>p1: isinstance
    p4->>p5: require_trimmed_text
    p5->>p6: require_nonempty_text
    p6-->>p1: isinstance
    p6-->>p7: strip
    p6-->>p8: any
    p6-->>p9: ord
    p6-->>p9: ord
    p4-->>p10: fullmatch
    p3->>p11: VerificationContractError
    p0->>p3: _sha256
    p0->>p3: _sha256
    p0->>p3: _sha256
    p0->>p12: knowledge_index_to_payload
    p12-->>p1: isinstance
    p12-->>p2: TypeError
    p12->>p13: _emit_extensions
    p13->>p14: _parse_extensions
    p14->>p15: _object
    p15-->>p16: dict
    p15->>p17: require_mapping
    p17-->>p1: isinstance
    p17-->>p1: isinstance
    p17-->>p18: encode
    p15->>p19: KnowledgeModelError
    p15->>p19: KnowledgeModelError
```

> Call sequence diagram shows 30 of 1089 interactions; 1059 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_artifact_verification_context"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _sha256"]
    s5["5. require_sha256"]
    s6["6. isinstance"]
    s7["7. require_trimmed_text"]
    s8["8. require_nonempty_text"]
    s9["9. isinstance"]
    s10["10. strip"]
    s11["11. any"]
    s12["12. ord"]
    s1 -. "isinstance(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -->|"_sha256(knowledge_hash, 'knowledge_hash')"| s4
    s4 -->|"require_sha256(value, digest_error=VerificationContractError(...))"| s5
    s5 -. "isinstance(value, str)" .-> s6
    s5 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s7
    s7 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s8
    s8 -. "isinstance(value, str)" .-> s9
    s8 -. "value.strip(data not statically known)" .-> s10
    s8 -. "any(...)" .-> s11
    s8 -. "ord(character)" .-> s12
    click s1 "../modules/verification_contracts.md"
    click s4 "../modules/verification_contracts.md"
    click s5 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_artifact_verification_context` | `knowledge: KnowledgeIndex`, `knowledge_hash: str`, `surface_index_hash: str`, `evaluated_envelope_hash: str`, `governance_hash: str \| None`, `scope_locator: str \| None`, `artifact_integrity: bool`, `artifact_diagnostics: Sequence[VerificationDiagnostic]` | `KnowledgeIndex`, `Mapping`, `Mapping` | `evidence[...]`, `evaluated_snapshot[...]` | `VerificationContext(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_sha256` | `value: object`, `field_name: str` | - | - | `require_sha256(...)` |
| `require_sha256` | `value: object`, `digest_error: Exception`, `text_error: Exception \| None`, `reject_control_characters: bool`, `allow_empty: bool` | - | - | `parsed`, `parsed` |
| `isinstance` | - | - | - | - |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_artifact_verification_context | isinstance | 339 | `isinstance(knowledge, KnowledgeIndex)` |
| build_artifact_verification_context | TypeError | 340 | `TypeError('knowledge must be a KnowledgeIndex')` |
| build_artifact_verification_context | _sha256 | 341 | `_sha256(knowledge_hash, 'knowledge_hash')` |
| _sha256 | require_sha256 | 1425 | `require_sha256(value, digest_error=VerificationContractError(...))` |
| require_sha256 | isinstance | 1100 | `isinstance(value, str)` |
| require_sha256 | require_trimmed_text | 1104 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 658 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 574 | `isinstance(value, str)` |
| require_nonempty_text | strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any | 582 | `any(...)` |
| require_nonempty_text | ord | 583 | `ord(character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_artifact_verification_context` | `isinstance` | 339 |
| unresolved_call | `build_artifact_verification_context` | `TypeError` | 340 |
| unresolved_call | `require_sha256` | `isinstance` | 1100 |
| unresolved_call | `require_nonempty_text` | `isinstance` | 574 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 576 |
| unresolved_call | `require_nonempty_text` | `any` | 582 |
| unresolved_call | `require_nonempty_text` | `ord` | 583 |
| step_limit | `build_artifact_verification_context` | `first 12 steps` | 0 |
| truncated_flow | `build_artifact_verification_context` | `depth limit` | 0 |

## Behavior

This flow starts at `build_artifact_verification_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
