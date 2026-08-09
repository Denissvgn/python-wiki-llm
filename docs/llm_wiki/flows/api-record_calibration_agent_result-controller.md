# record_calibration_agent_result

**Entry point:** `record_calibration_agent_result` (`api`)
**Source:** [controller](../modules/controller.md)
**Modules touched:** [calibration_contracts](../modules/calibration_contracts.md), [controller](../modules/controller.md), [documentation_policy](../modules/documentation_policy.md), [host_broker](../modules/host_broker.md), and 2 more

**Complete modules touched:**

- [calibration_contracts](../modules/calibration_contracts.md)
- [controller](../modules/controller.md)
- [documentation_policy](../modules/documentation_policy.md)
- [host_broker](../modules/host_broker.md)
- [protected_artifacts](../modules/protected_artifacts.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as record_calibration_agent_result
    participant p1 as _record_p0_calibration_agent_result
    participant p2 as isinstance
    participant p3 as from_dict
    participant p4 as _open_store
    participant p5 as ProtectedArtifactStore
    participant p6 as P0CalibrationIntegrityError
    participant p7 as str
    participant p8 as lock
    participant p9 as _load_run_locked
    participant p10 as exists
    participant p11 as _load_emergency_rejection
    participant p12 as read_json
    participant p13 as _require_exact_fields
    participant p14 as require_exact_fields
    participant p15 as set
    participant p16 as tuple
    participant p17 as sorted
    participant p18 as invalid_error
    participant p19 as error_factory
    participant p20 as P0CalibrationSchemaError
    participant p21 as title
    participant p22 as AssertionError
    p0->>p1: _record_p0_calibration_agent_result
    p1-->>p2: isinstance
    p1-->>p3: from_dict
    p1-->>p2: isinstance
    p1-->>p3: from_dict
    p1->>p4: _open_store
    p4->>p5: ProtectedArtifactStore
    p4->>p6: P0CalibrationIntegrityError
    p4-->>p7: str
    p1-->>p8: lock
    p1->>p9: _load_run_locked
    p9-->>p10: exists
    p9->>p11: _load_emergency_rejection
    p11-->>p12: read_json
    p11->>p13: _require_exact_fields
    p13->>p14: require_exact_fields
    p14-->>p2: isinstance
    p14-->>p7: str
    p14-->>p15: set
    p14-->>p15: set
    p14-->>p15: set
    p14-->>p16: tuple
    p14-->>p17: sorted
    p14-->>p16: tuple
    p14-->>p17: sorted
    p14-->>p18: invalid_error
    p14-->>p19: error_factory
    p13->>p20: P0CalibrationSchemaError
    p13-->>p21: title
    p13-->>p22: AssertionError
```

> Call sequence diagram shows 30 of 1413 interactions; 1383 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. record_calibration_agent_result"]
    s2["2. _record_p0_calibration_agent_result"]
    s3["3. isinstance"]
    s4["4. from_dict"]
    s5["5. isinstance"]
    s6["6. from_dict"]
    s7["7. _open_store"]
    s8["8. ProtectedArtifactStore"]
    s9["9. P0CalibrationIntegrityError"]
    s10["10. str"]
    s11["11. lock"]
    s12["12. _load_run_locked"]
    s1 -->|"_record_p0_calibration_agent_result(root, dispatch_receipt=dispatch_receipt, result=result, allow_local_dispatch=False)"| s2
    s2 -. "isinstance(dispatch_receipt, P0CalibrationDispatchReceipt)" .-> s3
    s2 -. "P0CalibrationDispatchReceipt.from_dict(dispatch_receipt)" .-> s4
    s2 -. "isinstance(result, P0CalibrationAgentResult)" .-> s5
    s2 -. "P0CalibrationAgentResult.from_dict(result)" .-> s6
    s2 -->|"_open_store(root)"| s7
    s7 -->|"ProtectedArtifactStore(root)"| s8
    s7 -->|"P0CalibrationIntegrityError(str(...))"| s9
    s7 -. "str(exc)" .-> s10
    s2 -. "store.lock(data not statically known)" .-> s11
    s2 -->|"_load_run_locked(store)"| s12
    b0["mutation broker_authentication_artifacts.append"]
    s2 -. "mutation broker_authentication_artifacts.append" .-> b0
    b1["mutation active.pop"]
    s2 -. "mutation active.pop" .-> b1
    b2["mutation active.pop"]
    s2 -. "mutation active.pop" .-> b2
    b3["mutation active.pop"]
    s2 -. "mutation active.pop" .-> b3
    click s1 "../modules/controller.md"
    click s2 "../modules/controller.md"
    click s7 "../modules/controller.md"
    click s8 "../modules/protected_artifacts.md"
    click s9 "../modules/controller.md"
    click s12 "../modules/controller.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `record_calibration_agent_result` | `root: str \| Path`, `dispatch_receipt: P0CalibrationDispatchReceipt \| Mapping[str, Any]`, `result: P0CalibrationAgentResult \| Mapping[str, Any]` | - | - | `_record_p0_calibration_agent_result(...)` |
| `_record_p0_calibration_agent_result` | `root: str \| Path`, `dispatch_receipt: P0CalibrationDispatchReceipt \| Mapping[str, Any]`, `result: P0CalibrationAgentResult \| Mapping[str, Any]`, `allow_local_dispatch: bool` | `P0CalibrationDispatchReceipt`, `P0CalibrationAgentResult`, `Mapping`, `CALIBRATION_TERMINAL_STATES`, `CALIBRATION_ROLES`, `Mapping`, `_MAX_RESULT_BYTES`, `_ExternalBrokerAuthenticationUnavailable` | `recorded[...]`, `roles[...]`, `receipts[...]`, `results[...]`, `artifacts[...]`, `artifacts[...]`, `receipt_authentications[...]`, `artifacts[...]` | `run`, `_commit_transition(...)`, `_commit_transition(...)` |
| `isinstance` | - | - | - | - |
| `from_dict` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `from_dict` | - | - | - | - |
| `_open_store` | `root: str \| Path` | `ProtectedArtifactError` | - | `ProtectedArtifactStore(...)` |
| `ProtectedArtifactStore` | - | - | - | - |
| `P0CalibrationIntegrityError` | - | - | - | - |
| `str` | - | - | - | - |
| `lock` | - | - | - | - |
| `_load_run_locked` | `store: ProtectedArtifactStore` | `P0CalibrationRecoveryError`, `P0CalibrationError`, `ProtectedArtifactError`, `ProtectedArtifactError`, `CALIBRATION_TERMINAL_STATES`, `P0CalibrationError`, `ProtectedArtifactError` | - | `_load_emergency_rejection(...)`, `_block_ambiguous_recovery(...)`, `_persist_emergency_rejection(...)`, `_terminal_transition_locked(...)`, `run`, `_persist_emergency_rejection(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| record_calibration_agent_result | _record_p0_calibration_agent_result | 2610 | `_record_p0_calibration_agent_result(root, dispatch_receipt=dispatch_receipt, result=result, allow_local_dispatch=False)` |
| _record_p0_calibration_agent_result | isinstance | 2627 | `isinstance(dispatch_receipt, P0CalibrationDispatchReceipt)` |
| _record_p0_calibration_agent_result | from_dict | 2628 | `P0CalibrationDispatchReceipt.from_dict(dispatch_receipt)` |
| _record_p0_calibration_agent_result | isinstance | 2632 | `isinstance(result, P0CalibrationAgentResult)` |
| _record_p0_calibration_agent_result | from_dict | 2633 | `P0CalibrationAgentResult.from_dict(result)` |
| _record_p0_calibration_agent_result | _open_store | 2635 | `_open_store(root)` |
| _open_store | ProtectedArtifactStore | 5824 | `ProtectedArtifactStore(root)` |
| _open_store | P0CalibrationIntegrityError | 5826 | `P0CalibrationIntegrityError(str(...))` |
| _open_store | str | 5826 | `str(exc)` |
| _record_p0_calibration_agent_result | lock | 2636 | `store.lock(data not statically known)` |
| _record_p0_calibration_agent_result | _load_run_locked | 2637 | `_load_run_locked(store)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `broker_authentication_artifacts.append` | `_record_p0_calibration_agent_result` | 2777 |
| mutation | `active.pop` | `_record_p0_calibration_agent_result` | 2798 |
| mutation | `active.pop` | `_record_p0_calibration_agent_result` | 2908 |
| mutation | `active.pop` | `_record_p0_calibration_agent_result` | 2952 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_record_p0_calibration_agent_result` | `isinstance` | 2627 |
| unresolved_call | `_record_p0_calibration_agent_result` | `P0CalibrationDispatchReceipt.from_dict` | 2628 |
| unresolved_call | `_record_p0_calibration_agent_result` | `isinstance` | 2632 |
| unresolved_call | `_record_p0_calibration_agent_result` | `P0CalibrationAgentResult.from_dict` | 2633 |
| unresolved_call | `_record_p0_calibration_agent_result` | `store.lock` | 2636 |
| step_limit | `record_calibration_agent_result` | `first 12 steps` | 0 |
| truncated_flow | `record_calibration_agent_result` | `depth limit` | 0 |

## Behavior

This flow starts at `record_calibration_agent_result` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
