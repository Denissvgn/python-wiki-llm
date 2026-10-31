# build_entity_observation_basis

**Entry point:** `build_entity_observation_basis` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [normalization_diagnostics](../modules/normalization_diagnostics.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_entity_observation_basis
    participant p1 as _validate_basis_inputs
    participant p2 as _validate_entity_coordinate
    participant p3 as _unknown_basis
    participant p4 as _normalize_entity_observation
    participant p5 as hash_json
    participant p6 as NormalizationDiagnostic
    participant p7 as ConceptObservationBasis
    participant p8 as _validate_source_path
    participant p9 as _inventory_language
    participant p10 as _validate_hash
    participant p11 as canonical_json_bytes
    participant p12 as _validate_extractor_ref
    participant p13 as require_positive_int
    participant p14 as _record_array
    participant p15 as _validate_inventory_complete
    participant p16 as _record_name
    participant p17 as _validate_entity_record
    participant p18 as _structural_copy
    participant p19 as require_repository_relative_path
    participant p20 as require_sha256
    participant p21 as require_nonnegative_int
    participant p22 as _validate_module_entity_record
    participant p23 as _failure
    participant p24 as _optional_record_array
    participant p25 as _validate_optional_json_array
    participant p26 as _validate_optional_mapping
    participant p27 as _validate_optional_record_array
    participant p28 as _validate_callable_record
    participant p29 as ValueError (src/llm_wiki_cli/services…alidate_entity_coordinate)
    participant p30 as diagnostic.at_source
    p0->>p1: _validate_basis_inputs
    p0->>p2: _validate_entity_coordinate
    p0->>p3: _unknown_basis
    p0->>p4: _normalize_entity_observation
    p0->>p5: hash_json
    p0->>p6: NormalizationDiagnostic
    p0->>p7: ConceptObservationBasis
    p1->>p8: _validate_source_path
    p4->>p9: _inventory_language
    p1->>p10: _validate_hash
    p5->>p11: canonical_json_bytes
    p1->>p12: _validate_extractor_ref
    p2->>p13: require_positive_int
    p4->>p14: _record_array
    p1->>p15: _validate_inventory_complete
    p4->>p16: _record_name
    p4->>p17: _validate_entity_record
    p4->>p18: _structural_copy
    p8->>p19: require_repository_relative_path
    p10->>p20: require_sha256
    p13->>p21: require_nonnegative_int
    p17->>p22: _validate_module_entity_record
    p9->>p23: _failure
    p14->>p24: _optional_record_array
    p17->>p25: _validate_optional_json_array
    p17->>p26: _validate_optional_mapping
    p17->>p27: _validate_optional_record_array
    p17->>p28: _validate_callable_record
    p2-->>p29: ValueError (src/llm_wiki_cli/services…alidate_entity_coordinate)('entity_name must be a non-empty string')
    p3-->>p30: diagnostic.at_source(source_path, scope, extractor_ref, entity_name, occurrence)
```

> Call sequence diagram shows 30 of 301 interactions; 271 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 73 (72 omitted); unresolved 1 of 58 (57 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 4 | - | external | 7 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 4 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 4 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 6 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 13 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 4 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 27 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 27 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 13 |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 29 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 93 groups; 85 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 171; effect analysis evaluated: 157, partial: 3, unavailable: 11. Counts include steps omitted from the displayed trace.

Collector observations for 160 source steps with known totals: observed: 766, emitted: 751, omitted: 15. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `build_entity_observation_basis` | `available` | `evaluated` | `available` | `19` | `19` | `0` |
| `_validate_basis_inputs` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_validate_source_path` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `require_repository_relative_path` | `available` | `partial` | `available` | `14` | `10` | `4` |
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_syntax_key` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `type (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. build_entity_observation_basis"]
    s2["2. _validate_basis_inputs"]
    s3["3. _validate_source_path"]
    s4["4. require_repository_relative_path"]
    s5["5. isinstance (src/llm_wiki_cli/services…_repository_relative_path)"]
    s6["6. _syntax_key"]
    s7["7. type (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s8["8. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s9["9. any (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s10["10. type (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s11["11. type (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s12["12. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s1 -->|"_validate_basis_inputs(source_path, source_content_hash, extractor_ref, inventory_complete)"| s2
    s2 -->|"_validate_source_path(source_path)"| s3
    s3 -->|"require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)" .-> s5
    s4 -->|"_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)"| s6
    s6 -. "type (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s7
    s6 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s8
    s6 -. "any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)" .-> s9
    s6 -. "type (src/llm_wiki_cli/services/validation.py:_syntax_key)(v)" .-> s10
    s6 -. "type (src/llm_wiki_cli/services/validation.py:_syntax_key)(v)" .-> s11
    s6 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(v)" .-> s12
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/knowledge_evidence.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_entity_observation_basis` | `source_path: str`, `file_data: Mapping[str, Any] \| None`, `entity_name: str`, `occurrence: int`, `source_content_hash: str`, `extractor_ref: str`, `inventory_complete: bool` | `ENTITY_OBSERVATION_SCOPE`, `UNKNOWN_INSUFFICIENT_INVENTORY`, `_InventoryNormalizationError`, `ENTITY_OBSERVATION_SCOPE`, `ENTITY_OBSERVATION_SCOPE`, `UNKNOWN_INVALID_INVENTORY`, `UNKNOWN_INVALID_INVENTORY`, `ENTITY_OBSERVATION_SCOPE` | - | `_unknown_basis(...)`, `_unknown_basis(...)`, `_unknown_basis(...)`, `ConceptObservationBasis(...)` |
| `_validate_basis_inputs` | `source_path: object`, `source_content_hash: object`, `extractor_ref: object`, `inventory_complete: object` | - | - | - |
| `_validate_source_path` | `source_path: object` | - | - | - |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `type (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `type (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_entity_observation_basis | _validate_basis_inputs | 380 | `_validate_basis_inputs(source_path, source_content_hash, extractor_ref, inventory_complete)` |
| _validate_basis_inputs | _validate_source_path | 840 | `_validate_source_path(source_path)` |
| _validate_source_path | require_repository_relative_path | 868 | `require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…_repository_relative_path) | 299 | `isinstance(value, str)` |
| require_repository_relative_path | _syntax_key | 301 | `_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)` |
| _syntax_key | type (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `type(value)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `len(value)` |
| _syntax_key | any (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `any(...)` |
| _syntax_key | type (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `type(v)` |
| _syntax_key | type (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `type(v)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `len(v)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_repository_relative_path` | `isinstance` | 299 |
| external_call | `_syntax_key` | `type` | 54 |
| external_call | `_syntax_key` | `any` | 55 |
| external_call | `_syntax_key` | `type` | 55 |
| step_limit | `build_entity_observation_basis` | `first 12 steps` | 0 |
| truncated_flow | `build_entity_observation_basis` | `depth limit` | 0 |

## Behavior

This flow starts at `build_entity_observation_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
