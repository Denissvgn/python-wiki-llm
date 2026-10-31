# infrastructure_evidence_by_page

**Entry point:** `infrastructure_evidence_by_page` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as infrastructure_evidence_by_page
    participant p1 as _prior_infrastructure_state
    participant p2 as _record_mapping
    participant p3 as build_infrastructure_observation_basis
    participant p4 as InfrastructureSyncError
    participant p5 as _validate_source_path
    participant p6 as _validate_hash
    participant p7 as _validate_extractor_ref
    participant p8 as _valid_repository_path
    participant p9 as require_repository_relative_path
    participant p10 as require_sha256
    participant p11 as is_portable_relative_path
    participant p12 as require_portable_relative_path
    participant p13 as require_trimmed_text
    participant p14 as require_nonempty_text
    participant p15 as _default_path_error
    participant p16 as _check_path_collision
    participant p17 as require_portable_path_component
    participant p18 as ConceptObservationBasis
    participant p19 as _valid_page_path
    participant p20 as is_valid_sha256
    participant p21 as require_string
    participant p22 as _syntax_key
    participant p23 as _known_syntax
    participant p24 as _remember_syntax
    participant p25 as SharedValidationError
    participant p26 as portable_path_key
    participant p27 as contains_control_character
    participant p28 as list
    participant p29 as state.get
    p0->>p1: _prior_infrastructure_state
    p0->>p2: _record_mapping
    p0->>p3: build_infrastructure_observation_basis
    p0->>p4: InfrastructureSyncError
    p3->>p5: _validate_source_path
    p3->>p6: _validate_hash
    p3->>p7: _validate_extractor_ref
    p2->>p8: _valid_repository_path
    p5->>p9: require_repository_relative_path
    p6->>p10: require_sha256
    p8->>p11: is_portable_relative_path
    p11->>p12: require_portable_relative_path
    p10->>p13: require_trimmed_text
    p13->>p14: require_nonempty_text
    p12->>p15: _default_path_error
    p12->>p16: _check_path_collision
    p12->>p17: require_portable_path_component
    p3->>p18: ConceptObservationBasis
    p2->>p19: _valid_page_path
    p2->>p20: is_valid_sha256
    p7->>p21: require_string
    p9->>p22: _syntax_key
    p9->>p23: _known_syntax
    p9->>p24: _remember_syntax
    p15->>p25: SharedValidationError
    p16->>p26: portable_path_key
    p14->>p27: contains_control_character
    p0-->>p28: list(sources.items(...))
    p0-->>p29: state.get('sources')
    p0-->>p29: state.get('tombstones')
```

> Call sequence diagram shows 30 of 165 interactions; 135 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 55 (54 omitted); unresolved 2 of 47 (45 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_prior_infrastructure_state` | 2 | - | external | 4 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_prior_infrastructure_state` | 2 | [src/llm_wiki_cli/services/infrastructure_sync.py](../modules/infrastructure_sync.md) | internal | 2 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_prior_infrastructure_state` | 2 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_record_mapping` | 11 | - | external | 9 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_record_mapping` | 11 | [src/llm_wiki_cli/services/infrastructure_sync.py](../modules/infrastructure_sync.md) | internal | 15 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_record_mapping` | 11 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:_valid_repository_path` | 18 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 21 | - | external | 4 |
> Omission summary shows 8 of 40 groups; 32 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 64; effect analysis evaluated: 35, partial: 4, unavailable: 25. Counts include steps omitted from the displayed trace.

Collector observations for 39 source steps with known totals: observed: 209, emitted: 184, omitted: 25. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `infrastructure_evidence_by_page` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `_prior_infrastructure_state` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InfrastructureSyncError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InfrastructureSyncError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `deepcopy (src/llm_wiki_cli/services…rior_infrastructure_state)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `dict (src/llm_wiki_cli/services…rior_infrastructure_state)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_record_mapping` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…e_sync.py:_record_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. infrastructure_evidence_by_page"]
    s2["2. _prior_infrastructure_state"]
    s3["3. isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)"]
    s4["4. isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)"]
    s5["5. InfrastructureSyncError"]
    s6["6. value.get"]
    s7["7. InfrastructureSyncError"]
    s8["8. value.get"]
    s9["9. deepcopy (src/llm_wiki_cli/services…rior_infrastructure_state)"]
    s10["10. dict (src/llm_wiki_cli/services…rior_infrastructure_state)"]
    s11["11. _record_mapping"]
    s12["12. isinstance (src/llm_wiki_cli/services…e_sync.py:_record_mapping)"]
    s1 -->|"_prior_infrastructure_state(generation_inputs)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)(generation_inputs, Mapping)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)(value, Mapping)" .-> s4
    s2 -->|"InfrastructureSyncError('generation_inputs.infrastructure must be an object.')"| s5
    s2 -. "value.get('schema_version')" .-> s6
    s2 -->|"InfrastructureSyncError(...)"| s7
    s2 -. "value.get('schema_version')" .-> s8
    s2 -. "deepcopy (src/llm_wiki_cli/services…rior_infrastructure_state)(dict(...))" .-> s9
    s2 -. "dict (src/llm_wiki_cli/services…rior_infrastructure_state)(value)" .-> s10
    s1 -->|"_record_mapping(state.get(...), field_name='sources')"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…e_sync.py:_record_mapping)(value, Mapping)" .-> s12
    b0["mutation records.extend"]
    s1 -. "mutation records.extend" .-> b0
    click s1 "../modules/infrastructure_sync.md"
    click s2 "../modules/infrastructure_sync.md"
    click s5 "../modules/infrastructure_sync.md"
    click s7 "../modules/infrastructure_sync.md"
    click s11 "../modules/infrastructure_sync.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `infrastructure_evidence_by_page` | `generation_inputs: Mapping[str, object] \| None` | `INFRASTRUCTURE_EXTRACTOR_REF` | `result[...]` | `{...}`, `result` |
| `_prior_infrastructure_state` | `generation_inputs: Mapping[str, object] \| None` | `Mapping`, `INFRASTRUCTURE_GENERATION_INPUT_KEY`, `INFRASTRUCTURE_GENERATION_INPUT_KEY`, `Mapping`, `INFRASTRUCTURE_SYNC_SCHEMA_VERSION` | - | `{...}`, `{...}`, `deepcopy(...)` |
| `isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…rior_infrastructure_state)` | - | - | - | - |
| `InfrastructureSyncError` | - | - | - | - |
| `value.get` | - | - | - | - |
| `InfrastructureSyncError` | - | - | - | - |
| `value.get` | - | - | - | - |
| `deepcopy (src/llm_wiki_cli/services…rior_infrastructure_state)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…rior_infrastructure_state)` | - | - | - | - |
| `_record_mapping` | `value: object`, `field_name: str` | `Mapping`, `Mapping`, `Mapping`, `INFRASTRUCTURE_DISCOVERY_ROOT` | `result[...]` | `{...}`, `result` |
| `isinstance (src/llm_wiki_cli/services…e_sync.py:_record_mapping)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| infrastructure_evidence_by_page | _prior_infrastructure_state | 262 | `_prior_infrastructure_state(generation_inputs)` |
| _prior_infrastructure_state | isinstance (src/llm_wiki_cli/services…rior_infrastructure_state) | 107 | `isinstance(generation_inputs, Mapping)` |
| _prior_infrastructure_state | isinstance (src/llm_wiki_cli/services…rior_infrastructure_state) | 112 | `isinstance(value, Mapping)` |
| _prior_infrastructure_state | InfrastructureSyncError | 113 | `InfrastructureSyncError('generation_inputs.infrastructure must be an object.')` |
| _prior_infrastructure_state | value.get | 116 | `value.get('schema_version')` |
| _prior_infrastructure_state | InfrastructureSyncError | 117 | `InfrastructureSyncError(...)` |
| _prior_infrastructure_state | value.get | 119 | `value.get('schema_version')` |
| _prior_infrastructure_state | deepcopy (src/llm_wiki_cli/services…rior_infrastructure_state) | 121 | `deepcopy(dict(...))` |
| _prior_infrastructure_state | dict (src/llm_wiki_cli/services…rior_infrastructure_state) | 121 | `dict(value)` |
| infrastructure_evidence_by_page | _record_mapping | 265 | `_record_mapping(state.get(...), field_name='sources')` |
| _record_mapping | isinstance (src/llm_wiki_cli/services…e_sync.py:_record_mapping) | 149 | `isinstance(value, Mapping)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `records.extend` | `infrastructure_evidence_by_page` | 268 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_prior_infrastructure_state` | `isinstance` | 107 |
| external_call | `_prior_infrastructure_state` | `isinstance` | 112 |
| unresolved_call | `_prior_infrastructure_state` | `value.get` | 116 |
| unresolved_call | `_prior_infrastructure_state` | `value.get` | 119 |
| external_call | `_prior_infrastructure_state` | `deepcopy` | 121 |
| external_call | `_record_mapping` | `isinstance` | 149 |
| step_limit | `infrastructure_evidence_by_page` | `first 12 steps` | 0 |
| truncated_flow | `infrastructure_evidence_by_page` | `depth limit` | 0 |

## Behavior

This flow starts at `infrastructure_evidence_by_page` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
