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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as admit_calibration_run
    participant p1 as _open_store
    participant p2 as store.lock
    participant p3 as _load_run_locked
    participant p4 as _recheck_bound_controls
    participant p5 as _terminal_transition_locked
    participant p6 as _sha256_json
    participant p7 as _json_round_trip
    participant p8 as _authority_freshness_failure
    participant p9 as P0CalibrationTransitionError
    participant p10 as _has_indeterminate_admission_probe
    participant p11 as store.read_json (src/llm_wiki_cli/services….py:admit_calibration_run)
    participant p12 as run.payload.get (src/llm_wiki_cli/services….py:admit_calibration_run)
    participant p13 as _pre_admission_authority_freshness_failure
    participant p14 as run.payload[…].get (src/llm_wiki_cli/services….py:admit_calibration_run)
    participant p15 as isinstance (src/llm_wiki_cli/services….py:admit_calibration_run)
    participant p16 as _admit_local_oci
    participant p17 as _admit_external_broker
    participant p18 as _validate_authority_grant
    p0->>p1: _open_store
    p0-->>p2: store.lock
    p0->>p3: _load_run_locked
    p0->>p4: _recheck_bound_controls
    p0->>p5: _terminal_transition_locked
    p0->>p6: _sha256_json
    p0->>p7: _json_round_trip
    p0->>p8: _authority_freshness_failure
    p0->>p5: _terminal_transition_locked
    p0->>p5: _terminal_transition_locked
    p0->>p9: P0CalibrationTransitionError
    p0->>p4: _recheck_bound_controls
    p0->>p5: _terminal_transition_locked
    p0->>p10: _has_indeterminate_admission_probe
    p0->>p5: _terminal_transition_locked
    p0-->>p11: store.read_json (src/llm_wiki_cli/services….py:admit_calibration_run)('baseline/execution-manifest.json')
    p0->>p7: _json_round_trip
    p0-->>p12: run.payload.get (src/llm_wiki_cli/services….py:admit_calibration_run)('authority_hash')
    p0->>p6: _sha256_json
    p0->>p5: _terminal_transition_locked
    p0->>p13: _pre_admission_authority_freshness_failure
    p0->>p5: _terminal_transition_locked
    p0-->>p14: run.payload[…].get (src/llm_wiki_cli/services….py:admit_calibration_run)('authority_grant')
    p0-->>p15: isinstance (src/llm_wiki_cli/services….py:admit_calibration_run)(authority_path, str)
    p0->>p5: _terminal_transition_locked
    p0-->>p11: store.read_json (src/llm_wiki_cli/services….py:admit_calibration_run)(authority_path)
    p0->>p5: _terminal_transition_locked
    p0->>p16: _admit_local_oci
    p0->>p17: _admit_external_broker
    p0->>p18: _validate_authority_grant
```

> Call sequence diagram shows 30 of 1938 interactions; 1908 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 469 (468 omitted); unresolved 5 of 595 (590 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | [src/llm_wiki_cli/services/protected_artifacts.py](../modules/protected_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_open_store` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_run_locked` | 7 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_run_locked` | 7 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 13 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_emergency_rejection` | 9 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/calibration/controller.py:_load_emergency_rejection` | 9 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 5 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
> Omission summary shows 8 of 340 groups; 332 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. admit_calibration_run"]
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
| `admit_calibration_run` | `root: str \| Path`, `authority_grant: Mapping[str, Any]`, `broker_attestation: Mapping[str, Any] \| None` | `timezone`, `P0CalibrationError` | - | `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `run`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)`, `_terminal_transition_locked(...)` |
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
| admit_calibration_run | _open_store | 782 | `_open_store(root)` |
| _open_store | ProtectedArtifactStore | 5824 | `ProtectedArtifactStore(root)` |
| _open_store | P0CalibrationIntegrityError | 5826 | `P0CalibrationIntegrityError(str(...))` |
| _open_store | str (src/llm_wiki_cli/services…controller.py:_open_store) | 5826 | `str(exc)` |
| admit_calibration_run | store.lock | 783 | `store.lock(data not statically known)` |
| admit_calibration_run | _load_run_locked | 784 | `_load_run_locked(store)` |
| _load_run_locked | store.exists (src/llm_wiki_cli/services…oller.py:_load_run_locked) | 4771 | `store.exists('terminal-rejection.json')` |
| _load_run_locked | _load_emergency_rejection | 4772 | `_load_emergency_rejection(store)` |
| _load_emergency_rejection | store.read_json (src/llm_wiki_cli/services…_load_emergency_rejection) | 4931 | `store.read_json('terminal-rejection.json')` |
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
