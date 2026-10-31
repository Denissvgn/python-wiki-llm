# verify_calibration_run

**Entry point:** `verify_calibration_run` (`api`)
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
    participant p0 as verify_calibration_run
    participant p1 as _open_store
    participant p2 as _load_run_locked
    participant p3 as _recheck_bound_controls
    participant p4 as _authority_freshness_failure
    participant p5 as P0CalibrationAgentResult.from_dict
    participant p6 as _validate_semantic_result
    participant p7 as _frozen_intake_proposals
    participant p8 as _validate_coherent_verifier
    participant p9 as _validate_verification_report
    participant p10 as P0CalibrationVerificationReport.from_dict
    participant p11 as _build_task_oracle
    participant p12 as _bounded_error
    participant p13 as _terminal_transition_locked
    participant p14 as P0CalibrationTransitionError
    participant p15 as _build_label_field_contract
    participant p16 as _build_optimizer_search_contract
    participant p17 as _sha256_json
    participant p18 as _json_round_trip
    participant p19 as _utc_now
    participant p20 as _commit_transition
    participant p21 as _bound_outbound_roots
    participant p22 as _load_emergency_rejection
    participant p23 as _validate_agent_result
    participant p24 as _recover_pending_transaction
    participant p25 as _block_ambiguous_recovery
    participant p26 as _persist_emergency_rejection
    participant p27 as _validate_authority_grant
    participant p28 as _sanitize_outbound_value
    participant p29 as all (src/llm_wiki_cli/services…py:verify_calibration_run)
    participant p30 as store.lock
    p0->>p1: _open_store
    p0->>p2: _load_run_locked
    p0->>p3: _recheck_bound_controls
    p0->>p4: _authority_freshness_failure
    p0->>p5: P0CalibrationAgentResult.from_dict
    p0->>p6: _validate_semantic_result
    p0->>p7: _frozen_intake_proposals
    p0->>p8: _validate_coherent_verifier
    p0->>p9: _validate_verification_report
    p0->>p10: P0CalibrationVerificationReport.from_dict
    p0->>p11: _build_task_oracle
    p0->>p12: _bounded_error
    p0->>p13: _terminal_transition_locked
    p0->>p14: P0CalibrationTransitionError
    p0->>p15: _build_label_field_contract
    p0->>p16: _build_optimizer_search_contract
    p0->>p17: _sha256_json
    p0->>p18: _json_round_trip
    p0->>p19: _utc_now
    p0->>p20: _commit_transition
    p7->>p21: _bound_outbound_roots
    p2->>p22: _load_emergency_rejection
    p5->>p23: _validate_agent_result
    p2->>p24: _recover_pending_transaction
    p2->>p25: _block_ambiguous_recovery
    p2->>p26: _persist_emergency_rejection
    p4->>p27: _validate_authority_grant
    p7->>p28: _sanitize_outbound_value
    p0-->>p29: all (src/llm_wiki_cli/services…py:verify_calibration_run)(...)
    p0-->>p30: store.lock
```

> Call sequence diagram shows 30 of 1562 interactions; 1532 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 370 (369 omitted); unresolved 1 of 537 (536 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | [src/llm_wiki_cli/services/protected_artifacts.py](../modules/protected_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_run_locked` | 7 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_emergency_rejection` | 9 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_emergency_rejection` | 9 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 5 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 12 | - | external | 9 |
> Omission summary shows 8 of 233 groups; 225 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 656; effect analysis evaluated: 387, partial: 14, unavailable: 255. Counts include steps omitted from the displayed trace.

Collector observations for 401 source steps with known totals: observed: 1756, emitted: 1708, omitted: 48. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `verify_calibration_run` | `available` | `partial` | `available` | `29` | `24` | `5` |
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
    s1["1. verify_calibration_run"]
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
    b0["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b0
    b1["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b1
    b2["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b2
    b3["mutation checks.append"]
    s1 -. "mutation checks.append" .-> b3
    b4["mutation report_payload.update"]
    s1 -. "mutation report_payload.update" .-> b4
    b5["mutation artifacts.update"]
    s1 -. "mutation artifacts.update" .-> b5
    click s1 "../modules/controller.md"
    click s2 "../modules/controller.md"
    click s3 "../modules/protected_artifacts.md"
    click s4 "../modules/controller.md"
    click s7 "../modules/controller.md"
    click s9 "../modules/controller.md"
    click s11 "../modules/controller.md"
    click s12 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verify_calibration_run` | `root: str \| Path`, `advance: bool` | `CALIBRATION_ROLES`, `CALIBRATION_ROLES`, `_MAX_BUNDLE_BYTES`, `CALIBRATION_ROLES`, `_MAX_RESULT_BYTES`, `P0CalibrationError`, `ProtectedArtifactError`, `P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION` | `frozen_results[...]`, `report_payload[...]`, `report_payload[...]`, `report_payload[...]` | `P0CalibrationVerificationReport.from_dict(...)`, `P0CalibrationVerificationReport.from_dict(...)`, `P0CalibrationVerificationReport.from_dict(...)`, `P0CalibrationVerificationReport.from_dict(...)` |
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
| verify_calibration_run | _open_store | 3200 | `_open_store(root)` |
| _open_store | ProtectedArtifactStore | 5824 | `ProtectedArtifactStore(root)` |
| _open_store | P0CalibrationIntegrityError | 5826 | `P0CalibrationIntegrityError(str(...))` |
| _open_store | str (src/llm_wiki_cli/services…controller.py:_open_store) | 5826 | `str(exc)` |
| verify_calibration_run | store.lock | 3201 | `store.lock(data not statically known)` |
| verify_calibration_run | _load_run_locked | 3202 | `_load_run_locked(store)` |
| _load_run_locked | store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked) | 4771 | `store.exists('terminal-rejection.json')` |
| _load_run_locked | _load_emergency_rejection | 4772 | `_load_emergency_rejection(store)` |
| _load_emergency_rejection | store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection) | 4931 | `store.read_json('terminal-rejection.json')` |
| _load_emergency_rejection | _require_exact_fields | 4932 | `_require_exact_fields(record, {...}, label='emergency rejection')` |
| _require_exact_fields | require_exact_fields | 6663 | `require_shared_exact_fields(payload, allowed=fields, required=fields, mapping_error=P0CalibrationSchemaError(...), missing_error=..., unknown_error=..., invalid_error=...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `checks.append` | `verify_calibration_run` | 3205 |
| mutation | `checks.append` | `verify_calibration_run` | 3213 |
| mutation | `checks.append` | `verify_calibration_run` | 3224 |
| mutation | `checks.append` | `verify_calibration_run` | 3267 |
| mutation | `report_payload.update` | `verify_calibration_run` | 3371 |
| mutation | `artifacts.update` | `verify_calibration_run` | 3385 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `verify_calibration_run` | `store.lock` | 3201 |
| unresolved_call | `_load_run_locked` | `store.exists` | 4771 |
| unresolved_call | `_load_emergency_rejection` | `store.read_json` | 4931 |
| step_limit | `verify_calibration_run` | `first 12 steps` | 0 |
| truncated_flow | `verify_calibration_run` | `depth limit` | 0 |

## Behavior

This flow starts at `verify_calibration_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
