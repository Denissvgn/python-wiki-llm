# build_artifact_verification_context

**Entry point:** `build_artifact_verification_context` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 9 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
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
    participant p1 as isinstance (src/llm_wiki_cli/services…fact_verification_context)
    participant p2 as TypeError (src/llm_wiki_cli/services…fact_verification_context)
    participant p3 as _sha256
    participant p4 as require_sha256
    participant p5 as isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)
    participant p6 as require_trimmed_text
    participant p7 as require_nonempty_text
    participant p8 as isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    participant p9 as value.strip
    participant p10 as any (src/llm_wiki_cli/services….py:require_nonempty_text)
    participant p11 as ord (src/llm_wiki_cli/services….py:require_nonempty_text)
    participant p12 as _SHA256_RE.fullmatch (src/llm_wiki_cli/services…idation.py:require_sha256)
    participant p13 as VerificationContractError
    participant p14 as knowledge_index_to_payload
    participant p15 as isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload)
    participant p16 as TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload)
    participant p17 as _emit_extensions
    participant p18 as isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions)
    participant p19 as _parse_extensions
    participant p20 as _object (src/llm_wiki_cli/services/knowledge_model.py)
    participant p21 as dict (src/llm_wiki_cli/services…nowledge_model.py:_object)
    participant p22 as require_mapping
    participant p23 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p24 as key.encode
    participant p25 as KnowledgeModelError
    p0-->>p1: isinstance (src/llm_wiki_cli/services…fact_verification_context)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…fact_verification_context)
    p0->>p3: _sha256
    p3->>p4: require_sha256
    p4-->>p5: isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)
    p4->>p6: require_trimmed_text
    p6->>p7: require_nonempty_text
    p7-->>p8: isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    p7-->>p9: value.strip
    p7-->>p10: any (src/llm_wiki_cli/services….py:require_nonempty_text)
    p7-->>p11: ord (src/llm_wiki_cli/services….py:require_nonempty_text)
    p7-->>p11: ord (src/llm_wiki_cli/services….py:require_nonempty_text)
    p4-->>p12: _SHA256_RE.fullmatch (src/llm_wiki_cli/services…idation.py:require_sha256)
    p3->>p13: VerificationContractError
    p0->>p3: _sha256
    p0->>p3: _sha256
    p0->>p3: _sha256
    p0->>p14: knowledge_index_to_payload
    p14-->>p15: isinstance (src/llm_wiki_cli/services…nowledge_index_to_payload)
    p14-->>p16: TypeError (src/llm_wiki_cli/services…nowledge_index_to_payload)
    p14->>p17: _emit_extensions
    p17-->>p18: isinstance (src/llm_wiki_cli/services…model.py:_emit_extensions)
    p17->>p19: _parse_extensions
    p19->>p20: _object (src/llm_wiki_cli/services/knowledge_model.py)
    p20-->>p21: dict (src/llm_wiki_cli/services…nowledge_model.py:_object)
    p20->>p22: require_mapping
    p22-->>p23: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p22-->>p23: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p22-->>p24: key.encode
    p20->>p25: KnowledgeModelError
```

> Call sequence diagram shows 30 of 1111 interactions; 1081 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_artifact_verification_context"]
    s2["2. isinstance (src/llm_wiki_cli/services…fact_verification_context)"]
    s3["3. TypeError (src/llm_wiki_cli/services…fact_verification_context)"]
    s4["4. _sha256"]
    s5["5. require_sha256"]
    s6["6. isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)"]
    s7["7. require_trimmed_text"]
    s8["8. require_nonempty_text"]
    s9["9. isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)"]
    s10["10. value.strip"]
    s11["11. any (src/llm_wiki_cli/services….py:require_nonempty_text)"]
    s12["12. ord (src/llm_wiki_cli/services….py:require_nonempty_text)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…fact_verification_context)(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…fact_verification_context)('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -->|"_sha256(knowledge_hash, 'knowledge_hash')"| s4
    s4 -->|"require_sha256(value, digest_error=VerificationContractError(...))"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)(value, str)" .-> s6
    s5 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s7
    s7 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)(value, str)" .-> s9
    s8 -. "value.strip(data not statically known)" .-> s10
    s8 -. "any (src/llm_wiki_cli/services….py:require_nonempty_text)(...)" .-> s11
    s8 -. "ord (src/llm_wiki_cli/services….py:require_nonempty_text)(character)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…fact_verification_context)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…fact_verification_context)` | - | - | - | - |
| `_sha256` | `value: object`, `field_name: str` | - | - | `require_sha256(...)` |
| `require_sha256` | `value: object`, `digest_error: Exception`, `text_error: Exception \| None`, `reject_control_characters: bool`, `allow_empty: bool` | - | - | `parsed`, `parsed` |
| `isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)` | - | - | - | - |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any (src/llm_wiki_cli/services….py:require_nonempty_text)` | - | - | - | - |
| `ord (src/llm_wiki_cli/services….py:require_nonempty_text)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_artifact_verification_context | isinstance (src/llm_wiki_cli/services…fact_verification_context) | 339 | `isinstance(knowledge, KnowledgeIndex)` |
| build_artifact_verification_context | TypeError (src/llm_wiki_cli/services…fact_verification_context) | 340 | `TypeError('knowledge must be a KnowledgeIndex')` |
| build_artifact_verification_context | _sha256 | 341 | `_sha256(knowledge_hash, 'knowledge_hash')` |
| _sha256 | require_sha256 | 1425 | `require_sha256(value, digest_error=VerificationContractError(...))` |
| require_sha256 | isinstance (src/llm_wiki_cli/services…idation.py:require_sha256) | 1100 | `isinstance(value, str)` |
| require_sha256 | require_trimmed_text | 1104 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 658 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services….py:require_nonempty_text) | 574 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any (src/llm_wiki_cli/services….py:require_nonempty_text) | 582 | `any(...)` |
| require_nonempty_text | ord (src/llm_wiki_cli/services….py:require_nonempty_text) | 583 | `ord(character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_artifact_verification_context` | `isinstance` | 339 |
| external_call | `build_artifact_verification_context` | `TypeError` | 340 |
| external_call | `require_sha256` | `isinstance` | 1100 |
| external_call | `require_nonempty_text` | `isinstance` | 574 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 576 |
| external_call | `require_nonempty_text` | `any` | 582 |
| external_call | `require_nonempty_text` | `ord` | 583 |
| step_limit | `build_artifact_verification_context` | `first 12 steps` | 0 |
| truncated_flow | `build_artifact_verification_context` | `depth limit` | 0 |

## Behavior

This flow starts at `build_artifact_verification_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
