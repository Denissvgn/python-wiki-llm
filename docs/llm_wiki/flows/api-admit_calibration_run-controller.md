# admit_calibration_run

**Entry point:** `admit_calibration_run` (`api`)
**Source:** [controller](../modules/controller.md)
**Modules touched:** [broker](../modules/broker.md), [calibration_contracts](../modules/calibration_contracts.md), [controller](../modules/controller.md), [documentation_policy](../modules/documentation_policy.md), and 4 more

**Complete modules touched:**

- [broker](../modules/broker.md)
- [calibration_contracts](../modules/calibration_contracts.md)
- [controller](../modules/controller.md)
- [documentation_policy](../modules/documentation_policy.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [host_broker](../modules/host_broker.md)
- [protected_artifacts](../modules/protected_artifacts.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as admit_calibration_run
    participant p1 as _open_store
    participant p2 as ProtectedArtifactStore
    participant p3 as P0CalibrationIntegrityError
    participant p4 as str
    participant p5 as lock
    participant p6 as _load_run_locked
    participant p7 as exists
    participant p8 as _load_emergency_rejection
    participant p9 as read_json
    participant p10 as _require_exact_fields
    participant p11 as require_exact_fields
    participant p12 as isinstance
    participant p13 as set
    participant p14 as tuple
    participant p15 as sorted
    participant p16 as invalid_error
    participant p17 as error_factory
    participant p18 as P0CalibrationSchemaError
    participant p19 as title
    participant p20 as AssertionError
    participant p21 as format_field_differences
    p0->>p1: _open_store
    p1->>p2: ProtectedArtifactStore
    p1->>p3: P0CalibrationIntegrityError
    p1-->>p4: str
    p0-->>p5: lock
    p0->>p6: _load_run_locked
    p6-->>p7: exists
    p6->>p8: _load_emergency_rejection
    p8-->>p9: read_json
    p8->>p10: _require_exact_fields
    p10->>p11: require_exact_fields
    p11-->>p12: isinstance
    p11-->>p4: str
    p11-->>p13: set
    p11-->>p13: set
    p11-->>p13: set
    p11-->>p14: tuple
    p11-->>p15: sorted
    p11-->>p14: tuple
    p11-->>p15: sorted
    p11-->>p16: invalid_error
    p11-->>p17: error_factory
    p10->>p18: P0CalibrationSchemaError
    p10-->>p19: title
    p10-->>p20: AssertionError
    p10-->>p20: AssertionError
    p10->>p18: P0CalibrationSchemaError
    p10-->>p19: title
    p10->>p21: format_field_differences
    p21-->>p14: tuple
```

> Call sequence diagram shows 30 of 1681 interactions; 1651 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. admit_calibration_run"]
    s2["2. _open_store"]
    s3["3. ProtectedArtifactStore"]
    s4["4. P0CalibrationIntegrityError"]
    s5["5. str"]
    s6["6. lock"]
    s7["7. _load_run_locked"]
    s8["8. exists"]
    s9["9. _load_emergency_rejection"]
    s10["10. read_json"]
    s11["11. _require_exact_fields"]
    s12["12. require_exact_fields"]
    s1 -->|"_open_store(root)"| s2
    s2 -->|"ProtectedArtifactStore(root)"| s3
    s2 -->|"P0CalibrationIntegrityError(str(...))"| s4
    s2 -. "str(exc)" .-> s5
    s1 -. "store.lock(data not statically known)" .-> s6
    s1 -->|"_load_run_locked(store)"| s7
    s7 -. "store.exists('terminal-rejection.json')" .-> s8
    s7 -->|"_load_emergency_rejection(store)"| s9
    s9 -. "store.read_json('terminal-rejection.json')" .-> s10
    s9 -->|"_require_exact_fields(record, {...}, label='emergency rejection')"| s11
    s11 -->|"require_shared_exact_fields(payload, allowed=fields, required=fields, mapping_error=P0CalibrationSchemaError(...), missing_error=..., unknown_error=..., invali…"| s12
    click s1 "../modules/controller.md"
    click s2 "../modules/controller.md"
    click s3 "../modules/protected_artifacts.md"
    click s4 "../modules/controller.md"
    click s7 "../modules/controller.md"
    click s9 "../modules/controller.md"
    click s11 "../modules/controller.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `admit_calibration_run` | `root: str \| Path`, `authority_grant: Mapping[str, Any]`, `broker_attestation: Mapping[str, Any] \| None` | `timezone`, `P0CalibrationError` | - | `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `run`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)` |
| `_open_store` | `root: str \| Path` | `ProtectedArtifactError` | - | `ProtectedArtifactStore(...)` |
| `ProtectedArtifactStore` | - | - | - | - |
| `P0CalibrationIntegrityError` | - | - | - | - |
| `str` | - | - | - | - |
| `lock` | - | - | - | - |
| `_load_run_locked` | `store: ProtectedArtifactStore` | `P0CalibrationRecoveryError`, `P0CalibrationError`, `ProtectedArtifactError`, `ProtectedArtifactError`, `CALIBRATION_TERMINAL_STATES`, `P0CalibrationError`, `ProtectedArtifactError` | - | `_load_emergency_rejection(...)`, `_block_ambiguous_recovery(...)`, `_persist_emergency_rejection(...)`, `_terminal_transition_locked(...)`, `run`, `_persist_emergency_rejection(...)` |
| `exists` | - | - | - | - |
| `_load_emergency_rejection` | `store: ProtectedArtifactStore` | `P0_CALIBRATION_EMERGENCY_REJECTION_SCHEMA_VERSION`, `P0_CALIBRATION_DECISION_SCOPE` | - | `run` |
| `read_json` | - | - | - | - |
| `_require_exact_fields` | `payload: Mapping[str, Any]`, `fields: set[str]`, `label: str` | - | - | `require_shared_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| admit_calibration_run | _open_store | 782 | `_open_store(root)` |
| _open_store | ProtectedArtifactStore | 5824 | `ProtectedArtifactStore(root)` |
| _open_store | P0CalibrationIntegrityError | 5826 | `P0CalibrationIntegrityError(str(...))` |
| _open_store | str | 5826 | `str(exc)` |
| admit_calibration_run | lock | 783 | `store.lock(data not statically known)` |
| admit_calibration_run | _load_run_locked | 784 | `_load_run_locked(store)` |
| _load_run_locked | exists | 4771 | `store.exists('terminal-rejection.json')` |
| _load_run_locked | _load_emergency_rejection | 4772 | `_load_emergency_rejection(store)` |
| _load_emergency_rejection | read_json | 4931 | `store.read_json('terminal-rejection.json')` |
| _load_emergency_rejection | _require_exact_fields | 4932 | `_require_exact_fields(record, {...}, label='emergency rejection')` |
| _require_exact_fields | require_exact_fields | 6663 | `require_shared_exact_fields(payload, allowed=fields, required=fields, mapping_error=P0CalibrationSchemaError(...), missing_error=..., unknown_error=..., invalid_error=...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `admit_calibration_run` | `store.lock` | 783 |
| unresolved_call | `_load_run_locked` | `store.exists` | 4771 |
| unresolved_call | `_load_emergency_rejection` | `store.read_json` | 4931 |
| step_limit | `admit_calibration_run` | `first 12 steps` | 0 |
| truncated_flow | `admit_calibration_run` | `depth limit` | 0 |

## Behavior

This flow starts at `admit_calibration_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
