# infrastructure_evidence_by_page

**Entry point:** `infrastructure_evidence_by_page` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as infrastructure_evidence_by_page
    participant p1 as _prior_infrastructure_state
    participant p2 as isinstance
    participant p3 as InfrastructureSyncError
    participant p4 as get
    participant p5 as deepcopy
    participant p6 as dict
    participant p7 as _record_mapping
    participant p8 as items
    participant p9 as _valid_repository_path
    participant p10 as PurePosixPath
    participant p11 as is_portable_relative_path
    participant p12 as require_portable_relative_path
    participant p13 as _default_path_error
    participant p14 as SharedValidationError
    participant p15 as fspath
    participant p16 as encode
    participant p17 as replace
    p0->>p1: _prior_infrastructure_state
    p1-->>p2: isinstance
    p1-->>p2: isinstance
    p1->>p3: InfrastructureSyncError
    p1-->>p4: get
    p1->>p3: InfrastructureSyncError
    p1-->>p4: get
    p1-->>p5: deepcopy
    p1-->>p6: dict
    p0->>p7: _record_mapping
    p7-->>p2: isinstance
    p7->>p3: InfrastructureSyncError
    p7-->>p8: items
    p7-->>p2: isinstance
    p7-->>p2: isinstance
    p7->>p3: InfrastructureSyncError
    p7->>p9: _valid_repository_path
    p9-->>p10: PurePosixPath
    p9->>p11: is_portable_relative_path
    p11->>p12: require_portable_relative_path
    p12-->>p2: isinstance
    p12->>p13: _default_path_error
    p13->>p14: SharedValidationError
    p12-->>p15: fspath
    p12-->>p2: isinstance
    p12->>p13: _default_path_error
    p12-->>p16: encode
    p12->>p13: _default_path_error
    p12->>p13: _default_path_error
    p12-->>p17: replace
```

> Call sequence diagram shows 30 of 150 interactions; 120 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. infrastructure_evidence_by_page"]
    s2["2. _prior_infrastructure_state"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. InfrastructureSyncError"]
    s6["6. get"]
    s7["7. InfrastructureSyncError"]
    s8["8. get"]
    s9["9. deepcopy"]
    s10["10. dict"]
    s11["11. _record_mapping"]
    s12["12. isinstance"]
    s1 -->|"_prior_infrastructure_state(generation_inputs)"| s2
    s2 -. "isinstance(generation_inputs, Mapping)" .-> s3
    s2 -. "isinstance(value, Mapping)" .-> s4
    s2 -->|"InfrastructureSyncError('generation_inputs.infrastructure must be an object.')"| s5
    s2 -. "value.get('schema_version')" .-> s6
    s2 -->|"InfrastructureSyncError(...)"| s7
    s2 -. "value.get('schema_version')" .-> s8
    s2 -. "deepcopy(dict(...))" .-> s9
    s2 -. "dict(value)" .-> s10
    s1 -->|"_record_mapping(state.get(...), field_name='sources')"| s11
    s11 -. "isinstance(value, Mapping)" .-> s12
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
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `InfrastructureSyncError` | - | - | - | - |
| `get` | - | - | - | - |
| `InfrastructureSyncError` | - | - | - | - |
| `get` | - | - | - | - |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `_record_mapping` | `value: object`, `field_name: str` | `Mapping`, `Mapping`, `Mapping`, `INFRASTRUCTURE_DISCOVERY_ROOT` | `result[...]` | `{...}`, `result` |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| infrastructure_evidence_by_page | _prior_infrastructure_state | 262 | `_prior_infrastructure_state(generation_inputs)` |
| _prior_infrastructure_state | isinstance | 107 | `isinstance(generation_inputs, Mapping)` |
| _prior_infrastructure_state | isinstance | 112 | `isinstance(value, Mapping)` |
| _prior_infrastructure_state | InfrastructureSyncError | 113 | `InfrastructureSyncError('generation_inputs.infrastructure must be an object.')` |
| _prior_infrastructure_state | get | 116 | `value.get('schema_version')` |
| _prior_infrastructure_state | InfrastructureSyncError | 117 | `InfrastructureSyncError(...)` |
| _prior_infrastructure_state | get | 119 | `value.get('schema_version')` |
| _prior_infrastructure_state | deepcopy | 121 | `deepcopy(dict(...))` |
| _prior_infrastructure_state | dict | 121 | `dict(value)` |
| infrastructure_evidence_by_page | _record_mapping | 265 | `_record_mapping(state.get(...), field_name='sources')` |
| _record_mapping | isinstance | 149 | `isinstance(value, Mapping)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `records.extend` | `infrastructure_evidence_by_page` | 268 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_prior_infrastructure_state` | `isinstance` | 107 |
| unresolved_call | `_prior_infrastructure_state` | `isinstance` | 112 |
| unresolved_call | `_prior_infrastructure_state` | `value.get` | 116 |
| unresolved_call | `_prior_infrastructure_state` | `value.get` | 119 |
| external_call | `_prior_infrastructure_state` | `deepcopy` | 121 |
| unresolved_call | `_record_mapping` | `isinstance` | 149 |
| step_limit | `infrastructure_evidence_by_page` | `first 12 steps` | 0 |

## Behavior

This flow starts at `infrastructure_evidence_by_page` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
