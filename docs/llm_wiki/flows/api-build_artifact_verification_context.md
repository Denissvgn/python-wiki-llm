# build_artifact_verification_context

**Entry point:** `build_artifact_verification_context` (`api`)
**Source:** [verification_contracts](../modules/verification_contracts.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [concept_identity](../modules/concept_identity.md), [implementation_evidence](../modules/implementation_evidence.md), and 17 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [concept_identity](../modules/concept_identity.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [markdown_sections](../modules/markdown_sections.md)
- [python_implementation](../modules/python_implementation.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_artifact_verification_context
    participant p1 as _sha256
    participant p2 as knowledge_index_to_payload
    participant p3 as VerificationContractError
    participant p4 as hash_json
    participant p5 as VerificationContext
    participant p6 as require_sha256
    participant p7 as _emit_extensions
    participant p8 as _bundle_to_payload
    participant p9 as _concept_to_payload
    participant p10 as _relationship_to_payload
    participant p11 as parse_knowledge_index
    participant p12 as _knowledge_index_to_payload_unchecked
    participant p13 as _record
    participant p14 as require_trimmed_text
    participant p15 as _parse_extensions
    participant p16 as _basis_to_payload
    participant p17 as _relationship_target_to_payload
    participant p18 as _parse_bundle
    participant p19 as _component_to_payload
    participant p20 as _relationship_evidence_to_payload
    participant p21 as _actor_to_payload
    participant p22 as _parse_concept
    participant p23 as _parse_relationship
    participant p24 as _document_to_payload
    participant p25 as _validated_reserved_extensions
    participant p26 as _validate_index_references
    participant p27 as validate_implementation_collection
    participant p28 as validate_maintenance_projection
    participant p29 as isinstance (src/llm_wiki_cli/services…fact_verification_context)
    participant p30 as knowledge.extensions.get (src/llm_wiki_cli/services…fact_verification_context)
    p0->>p1: _sha256
    p0->>p2: knowledge_index_to_payload
    p0->>p3: VerificationContractError
    p0->>p4: hash_json
    p0->>p5: VerificationContext
    p1->>p6: require_sha256
    p2->>p7: _emit_extensions
    p2->>p8: _bundle_to_payload
    p2->>p9: _concept_to_payload
    p2->>p10: _relationship_to_payload
    p2->>p11: parse_knowledge_index
    p2->>p12: _knowledge_index_to_payload_unchecked
    p11->>p13: _record
    p6->>p14: require_trimmed_text
    p7->>p15: _parse_extensions
    p9->>p16: _basis_to_payload
    p10->>p17: _relationship_target_to_payload
    p11->>p18: _parse_bundle
    p8->>p19: _component_to_payload
    p10->>p20: _relationship_evidence_to_payload
    p9->>p21: _actor_to_payload
    p11->>p22: _parse_concept
    p11->>p23: _parse_relationship
    p9->>p24: _document_to_payload
    p11->>p25: _validated_reserved_extensions
    p11->>p26: _validate_index_references
    p11->>p27: validate_implementation_collection
    p11->>p28: validate_maintenance_projection
    p0-->>p29: isinstance (src/llm_wiki_cli/services…fact_verification_context)(knowledge, KnowledgeIndex)
    p0-->>p30: knowledge.extensions.get (src/llm_wiki_cli/services…fact_verification_context)(governance_key)
```

> Call sequence diagram shows 30 of 1310 interactions; 1280 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 345 (344 omitted); unresolved 1 of 209 (208 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:build_artifact_verification_context` | 1 | - | external | 8 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 5 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_trimmed_text` | 7 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 8 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 8 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:contains_control_character` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_sha256` | 5 | - | unresolved | 1 |
> Omission summary shows 8 of 299 groups; 291 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
    s11["11. contains_control_character"]
    s12["12. pattern.search"]
    s1 -. "isinstance (src/llm_wiki_cli/services…fact_verification_context)(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…fact_verification_context)('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -->|"_sha256(knowledge_hash, 'knowledge_hash')"| s4
    s4 -->|"require_sha256(value, digest_error=VerificationContractError(...))"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)(value, str)" .-> s6
    s5 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s7
    s7 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)(value, str)" .-> s9
    s8 -. "value.strip(data not statically known)" .-> s10
    s8 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s11
    s11 -. "pattern.search(value)" .-> s12
    click s1 "../modules/verification_contracts.md"
    click s4 "../modules/verification_contracts.md"
    click s5 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s11 "../modules/validation.md"
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
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_artifact_verification_context | isinstance (src/llm_wiki_cli/services…fact_verification_context) | 339 | `isinstance(knowledge, KnowledgeIndex)` |
| build_artifact_verification_context | TypeError (src/llm_wiki_cli/services…fact_verification_context) | 340 | `TypeError('knowledge must be a KnowledgeIndex')` |
| build_artifact_verification_context | _sha256 | 341 | `_sha256(knowledge_hash, 'knowledge_hash')` |
| _sha256 | require_sha256 | 1425 | `require_sha256(value, digest_error=VerificationContractError(...))` |
| require_sha256 | isinstance (src/llm_wiki_cli/services…idation.py:require_sha256) | 1138 | `isinstance(value, str)` |
| require_sha256 | require_trimmed_text | 1142 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 696 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services….py:require_nonempty_text) | 623 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 625 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 631 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_artifact_verification_context` | `isinstance` | 339 |
| external_call | `build_artifact_verification_context` | `TypeError` | 340 |
| external_call | `require_sha256` | `isinstance` | 1138 |
| external_call | `require_nonempty_text` | `isinstance` | 623 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 625 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| step_limit | `build_artifact_verification_context` | `first 12 steps` | 0 |
| truncated_flow | `build_artifact_verification_context` | `depth limit` | 0 |

## Behavior

This flow starts at `build_artifact_verification_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
