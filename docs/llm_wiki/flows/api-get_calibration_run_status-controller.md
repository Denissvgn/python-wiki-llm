# get_calibration_run_status

**Entry point:** `get_calibration_run_status` (`api`)
**Source:** [controller](../modules/controller.md)
**Modules touched:** [calibration_contracts](../modules/calibration_contracts.md), [controller](../modules/controller.md), [documentation_policy](../modules/documentation_policy.md), and 4 more

**Complete modules touched:**

- [calibration_contracts](../modules/calibration_contracts.md)
- [controller](../modules/controller.md)
- [documentation_policy](../modules/documentation_policy.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [host_broker](../modules/host_broker.md)
- [protected_artifacts](../modules/protected_artifacts.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_calibration_run_status
    participant p1 as _open_store
    participant p2 as _load_run_locked
    participant p3 as _recheck_bound_controls
    participant p4 as _authority_freshness_failure
    participant p5 as _stale_active_dispatches
    participant p6 as _status_from_run
    participant p7 as _terminal_transition_locked
    participant p8 as _has_indeterminate_admission_probe
    participant p9 as _load_emergency_rejection
    participant p10 as _recover_pending_transaction
    participant p11 as _block_ambiguous_recovery
    participant p12 as _persist_emergency_rejection
    participant p13 as _validate_authority_grant
    participant p14 as _validate_host_authorization
    participant p15 as _unknown_root_entries
    participant p16 as _load_control_workspace
    participant p17 as _validate_isolation_attestation
    participant p18 as _assert_controls_match
    participant p19 as _portable_control_record
    participant p20 as _validate_external_broker_authentication
    participant p21 as _authenticate_external_attestation
    participant p22 as _revalidate_external_receipt_authentications
    participant p23 as require_attestation_authentication
    participant p24 as _require_exact_fields
    participant p25 as _assert_regular_directory
    participant p26 as _validate_pending_transaction_for_recovery
    participant p27 as _read_workspace_json
    participant p28 as _utc_now
    participant p29 as datetime.now (src/llm_wiki_cli/services…:_stale_active_dispatches)
    participant p30 as store.lock
    p0->>p1: _open_store
    p0->>p2: _load_run_locked
    p0->>p3: _recheck_bound_controls
    p0->>p4: _authority_freshness_failure
    p0->>p5: _stale_active_dispatches
    p0->>p6: _status_from_run
    p0->>p7: _terminal_transition_locked
    p0->>p8: _has_indeterminate_admission_probe
    p2->>p9: _load_emergency_rejection
    p2->>p10: _recover_pending_transaction
    p2->>p11: _block_ambiguous_recovery
    p2->>p12: _persist_emergency_rejection
    p4->>p13: _validate_authority_grant
    p4->>p14: _validate_host_authorization
    p2->>p15: _unknown_root_entries
    p3->>p16: _load_control_workspace
    p4->>p17: _validate_isolation_attestation
    p3->>p18: _assert_controls_match
    p3->>p19: _portable_control_record
    p4->>p20: _validate_external_broker_authentication
    p4->>p21: _authenticate_external_attestation
    p4->>p22: _revalidate_external_receipt_authentications
    p21->>p23: require_attestation_authentication
    p9->>p24: _require_exact_fields
    p16->>p25: _assert_regular_directory
    p10->>p26: _validate_pending_transaction_for_recovery
    p16->>p27: _read_workspace_json
    p11->>p28: _utc_now
    p5-->>p29: datetime.now (src/llm_wiki_cli/services…:_stale_active_dispatches)(timezone.utc)
    p0-->>p30: store.lock
```

> Call sequence diagram shows 30 of 1230 interactions; 1200 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 279 (278 omitted); unresolved 1 of 439 (438 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | [src/llm_wiki_cli/services/protected_artifacts.py](../modules/protected_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_run_locked` | 7 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_emergency_rejection` | 9 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 12 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 12 | - | unresolved | 2 |
> Omission summary shows 8 of 191 groups; 183 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 513; effect analysis evaluated: 293, partial: 10, unavailable: 210. Counts include steps omitted from the displayed trace.

Collector observations for 303 source steps with known totals: observed: 1330, emitted: 1298, omitted: 32. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `get_calibration_run_status` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_open_store` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `ProtectedArtifactStore` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `P0CalibrationIntegrityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `str (src/llm_wiki_cli/services…controller.py:_open_store)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `store.lock` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_load_run_locked` | `available` | `evaluated` | `available` | `14` | `14` | `0` |
| `store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_load_emergency_rejection` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_require_exact_fields` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `require_exact_fields` | `available` | `partial` | `available` | `10` | `9` | `1` |

```mermaid
flowchart LR
    s1["1. get_calibration_run_status"]
    s2["2. _open_store"]
    s3["3. ProtectedArtifactStore"]
    s4["4. P0CalibrationIntegrityError"]
    s5["5. str (src/llm_wiki_cli/services…controller.py:_open_store)"]
    s6["6. store.lock"]
    s7["7. _load_run_locked"]
    s8["8. store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked)"]
    s9["9. _load_emergency_rejection"]
    s10["10. store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection)"]
    s11["11. _require_exact_fields"]
    s12["12. require_exact_fields"]
    s1 -->|"_open_store(root)"| s2
    s2 -->|"ProtectedArtifactStore(root)"| s3
    s2 -->|"P0CalibrationIntegrityError(str(...))"| s4
    s2 -. "str (src/llm_wiki_cli/services…controller.py:_open_store)(exc)" .-> s5
    s1 -. "store.lock(data not statically known)" .-> s6
    s1 -->|"_load_run_locked(store)"| s7
    s7 -. "store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked)('terminal-rejection.json')" .-> s8
    s7 -->|"_load_emergency_rejection(store)"| s9
    s9 -. "store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection)('terminal-rejection.json')" .-> s10
    s9 -->|"_require_exact_fields(record, {...}, label='emergency rejection')"| s11
    s11 -->|"require_exact_fields(…)"| s12
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
| `get_calibration_run_status` | `root: str \| Path` | `CALIBRATION_TERMINAL_STATES`, `CALIBRATION_TERMINAL_STATES` | - | `_status_from_run(...)` |
| `_open_store` | `root: str \| Path` | `ProtectedArtifactError` | - | `ProtectedArtifactStore(...)` |
| `ProtectedArtifactStore` | - | - | - | - |
| `P0CalibrationIntegrityError` | - | - | - | - |
| `str (src/llm_wiki_cli/services…controller.py:_open_store)` | - | - | - | - |
| `store.lock` | - | - | - | - |
| `_load_run_locked` | `store: ProtectedArtifactStore` | `P0CalibrationRecoveryError`, `P0CalibrationError`, `ProtectedArtifactError`, `ProtectedArtifactError`, `CALIBRATION_TERMINAL_STATES`, `P0CalibrationError`, `ProtectedArtifactError` | - | `_load_emergency_rejection(...)`, `_block_ambiguous_recovery(...)`, `_persist_emergency_rejection(...)`, `_terminal_transition_locked(...)`, `run`, `_persist_emergency_rejection(...)` |
| `store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked)` | - | - | - | - |
| `_load_emergency_rejection` | `store: ProtectedArtifactStore` | `P0_CALIBRATION_EMERGENCY_REJECTION_SCHEMA_VERSION`, `P0_CALIBRATION_DECISION_SCOPE` | - | `run` |
| `store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection)` | - | - | - | - |
| `_require_exact_fields` | `payload: Mapping[str, Any]`, `fields: set[str]`, `label: str` | - | - | `require_shared_exact_fields(...)` |
| `require_exact_fields` | `value: object`, `allowed: Iterable[str]`, `required: Iterable[str]`, `mapping_error: Exception`, `missing_error: _ErrorFactory`, `unknown_error: _ErrorFactory`, `invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception] \| None`, `stringify_keys: bool` | `Mapping` | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_calibration_run_status | _open_store | 658 | `_open_store(root)` |
| _open_store | ProtectedArtifactStore | 5824 | `ProtectedArtifactStore(root)` |
| _open_store | P0CalibrationIntegrityError | 5826 | `P0CalibrationIntegrityError(str(...))` |
| _open_store | str (src/llm_wiki_cli/services…controller.py:_open_store) | 5826 | `str(exc)` |
| get_calibration_run_status | store.lock | 659 | `store.lock(data not statically known)` |
| get_calibration_run_status | _load_run_locked | 660 | `_load_run_locked(store)` |
| _load_run_locked | store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked) | 4771 | `store.exists('terminal-rejection.json')` |
| _load_run_locked | _load_emergency_rejection | 4772 | `_load_emergency_rejection(store)` |
| _load_emergency_rejection | store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection) | 4931 | `store.read_json('terminal-rejection.json')` |
| _load_emergency_rejection | _require_exact_fields | 4932 | `_require_exact_fields(record, {...}, label='emergency rejection')` |
| _require_exact_fields | require_exact_fields | 6663 | `require_shared_exact_fields(payload, allowed=fields, required=fields, mapping_error=P0CalibrationSchemaError(...), missing_error=..., unknown_error=..., invalid_error=...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `get_calibration_run_status` | `store.lock` | 659 |
| unresolved_call | `_load_run_locked` | `store.exists` | 4771 |
| unresolved_call | `_load_emergency_rejection` | `store.read_json` | 4931 |
| step_limit | `get_calibration_run_status` | `first 12 steps` | 0 |
| truncated_flow | `get_calibration_run_status` | `depth limit` | 0 |

## Behavior

This flow starts at `get_calibration_run_status` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
