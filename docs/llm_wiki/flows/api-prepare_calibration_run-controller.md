# prepare_calibration_run

**Entry point:** `prepare_calibration_run` (`api`)
**Source:** [controller](../modules/controller.md)
**Modules touched:** [broker](../modules/broker.md), [calibration_contracts](../modules/calibration_contracts.md), [controller](../modules/controller.md), [documentation_policy](../modules/documentation_policy.md), and 3 more

**Complete modules touched:**

- [broker](../modules/broker.md)
- [calibration_contracts](../modules/calibration_contracts.md)
- [controller](../modules/controller.md)
- [documentation_policy](../modules/documentation_policy.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [protected_artifacts](../modules/protected_artifacts.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as prepare_calibration_run
    participant p1 as _json_round_trip
    participant p2 as _validate_execution_manifest
    participant p3 as _load_control_workspace
    participant p4 as _assert_controls_match
    participant p5 as _validate_protected_root_placement
    participant p6 as _compile_evidence_bundle
    participant p7 as _portable_control_record
    participant p8 as _utc_now
    participant p9 as _commit_transition
    participant p10 as P0CalibrationSchemaError
    participant p11 as P0CalibrationIntegrityError
    participant p12 as _implementation_worktree_roots
    participant p13 as canonical_json_bytes
    participant p14 as _build_role_capability_matrix
    participant p15 as _sha256_json
    participant p16 as _initial_role_state
    participant p17 as ProtectedArtifactStore
    participant p18 as _require_exact_fields
    participant p19 as _normalize_bound_roots
    participant p20 as _require_choice
    participant p21 as _assert_regular_directory
    participant p22 as _read_workspace_json
    participant p23 as _assert_portable_leaf_name
    participant p24 as _required_mapping (src/llm_wiki_cli/services/calibration/controller.py)
    participant p25 as _paths_overlap
    participant p26 as _require_positive_int
    participant p27 as _load_control_runtime_policy
    participant p28 as _required_evidence_path
    participant p29 as isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p30 as store.lock
    p0->>p1: _json_round_trip
    p0->>p2: _validate_execution_manifest
    p0->>p3: _load_control_workspace
    p0->>p4: _assert_controls_match
    p0->>p5: _validate_protected_root_placement
    p0->>p6: _compile_evidence_bundle
    p0->>p7: _portable_control_record
    p0->>p8: _utc_now
    p0->>p9: _commit_transition
    p0->>p10: P0CalibrationSchemaError
    p0->>p11: P0CalibrationIntegrityError
    p0->>p12: _implementation_worktree_roots
    p0->>p13: canonical_json_bytes
    p0->>p14: _build_role_capability_matrix
    p0->>p15: _sha256_json
    p0->>p16: _initial_role_state
    p0->>p17: ProtectedArtifactStore
    p2->>p18: _require_exact_fields
    p6->>p19: _normalize_bound_roots
    p2->>p20: _require_choice
    p3->>p21: _assert_regular_directory
    p3->>p22: _read_workspace_json
    p5->>p23: _assert_portable_leaf_name
    p2->>p24: _required_mapping (src/llm_wiki_cli/services/calibration/controller.py)
    p5->>p25: _paths_overlap
    p2->>p26: _require_positive_int
    p3->>p27: _load_control_runtime_policy
    p3->>p28: _required_evidence_path
    p0-->>p29: isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces, (...))
    p0-->>p30: store.lock
```

> Call sequence diagram shows 30 of 1294 interactions; 1264 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 350 (349 omitted); unresolved 1 of 396 (395 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/controller.py:prepare_calibration_run` | 1 | - | external | 16 |
| `src/llm_wiki_cli/services/calibration/controller.py:_json_round_trip` | 5 | - | external | 4 |
| `src/llm_wiki_cli/services/calibration/controller.py:_json_round_trip` | 5 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 3 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 15 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 15 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 14 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 2 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 14 | - | unresolved | 2 |
> Omission summary shows 8 of 256 groups; 248 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 549; effect analysis evaluated: 317, partial: 14, unavailable: 218. Counts include steps omitted from the displayed trace.

Collector observations for 331 source steps with known totals: observed: 1483, emitted: 1449, omitted: 34. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `prepare_calibration_run` | `available` | `evaluated` | `available` | `12` | `12` | `0` |
| `isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services…y:prepare_calibration_run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `P0CalibrationSchemaError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_json_round_trip` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `P0CalibrationSchemaError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `json.dumps (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `json.loads (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `P0CalibrationSchemaError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `P0CalibrationSchemaError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. prepare_calibration_run"]
    s2["2. isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)"]
    s3["3. len (src/llm_wiki_cli/services…y:prepare_calibration_run)"]
    s4["4. P0CalibrationSchemaError"]
    s5["5. _json_round_trip"]
    s6["6. isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)"]
    s7["7. P0CalibrationSchemaError"]
    s8["8. json.dumps (src/llm_wiki_cli/services…oller.py:_json_round_trip)"]
    s9["9. json.loads (src/llm_wiki_cli/services…oller.py:_json_round_trip)"]
    s10["10. P0CalibrationSchemaError"]
    s11["11. isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)"]
    s12["12. P0CalibrationSchemaError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces, (...))" .-> s2
    s1 -. "len (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces)" .-> s3
    s1 -->|"P0CalibrationSchemaError('prepare requires exactly two documentation control workspaces.')"| s4
    s1 -->|"_json_round_trip(execution_manifest)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)(payload, Mapping)" .-> s6
    s5 -->|"P0CalibrationSchemaError('Calibration payload must be an object.')"| s7
    s5 -. "json.dumps (src/llm_wiki_cli/services…oller.py:_json_round_trip)(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(...))" .-> s8
    s5 -. "json.loads (src/llm_wiki_cli/services…oller.py:_json_round_trip)(encoded)" .-> s9
    s5 -->|"P0CalibrationSchemaError(...)"| s10
    s5 -. "isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)(normalized, dict)" .-> s11
    s5 -->|"P0CalibrationSchemaError('Calibration payload must be an object.')"| s12
    click s1 "../modules/controller.md"
    click s4 "../modules/controller.md"
    click s5 "../modules/controller.md"
    click s7 "../modules/controller.md"
    click s10 "../modules/controller.md"
    click s12 "../modules/controller.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `prepare_calibration_run` | `root: str \| Path`, `control_workspaces: Sequence[str \| Path]`, `execution_manifest: Mapping[str, Any]` | `_MAX_BUNDLE_BYTES`, `_MAX_BUNDLE_BYTES`, `P0_CALIBRATION_RUNTIME_BINDINGS_SCHEMA_VERSION`, `P0_CALIBRATION_RUN_SCHEMA_VERSION`, `P0_CALIBRATION_DECISION_SCOPE`, `CALIBRATION_ROLES`, `_ZERO_HASH`, `ProtectedArtifactError` | - | `_commit_transition(...)` |
| `isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)` | - | - | - | - |
| `len (src/llm_wiki_cli/services…y:prepare_calibration_run)` | - | - | - | - |
| `P0CalibrationSchemaError` | - | - | - | - |
| `_json_round_trip` | `payload: Mapping[str, Any]` | `Mapping` | - | `normalized` |
| `isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | - | - | - | - |
| `P0CalibrationSchemaError` | - | - | - | - |
| `json.dumps (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | - | - | - | - |
| `P0CalibrationSchemaError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip)` | - | - | - | - |
| `P0CalibrationSchemaError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| prepare_calibration_run | isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run) | 508 | `isinstance(control_workspaces, (...))` |
| prepare_calibration_run | len (src/llm_wiki_cli/services…y:prepare_calibration_run) | 508 | `len(control_workspaces)` |
| prepare_calibration_run | P0CalibrationSchemaError | 509 | `P0CalibrationSchemaError('prepare requires exactly two documentation control workspaces.')` |
| prepare_calibration_run | _json_round_trip | 512 | `_json_round_trip(execution_manifest)` |
| _json_round_trip | isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip) | 6865 | `isinstance(payload, Mapping)` |
| _json_round_trip | P0CalibrationSchemaError | 6866 | `P0CalibrationSchemaError('Calibration payload must be an object.')` |
| _json_round_trip | json.dumps (src/llm_wiki_cli/services…oller.py:_json_round_trip) | 6868 | `json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(...))` |
| _json_round_trip | json.loads (src/llm_wiki_cli/services…oller.py:_json_round_trip) | 6875 | `json.loads(encoded)` |
| _json_round_trip | P0CalibrationSchemaError | 6877 | `P0CalibrationSchemaError(...)` |
| _json_round_trip | isinstance (src/llm_wiki_cli/services…oller.py:_json_round_trip) | 6880 | `isinstance(normalized, dict)` |
| _json_round_trip | P0CalibrationSchemaError | 6881 | `P0CalibrationSchemaError('Calibration payload must be an object.')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `prepare_calibration_run` | `isinstance` | 508 |
| external_call | `_json_round_trip` | `isinstance` | 6865 |
| external_call | `_json_round_trip` | `json.dumps` | 6868 |
| external_call | `_json_round_trip` | `json.loads` | 6875 |
| external_call | `_json_round_trip` | `isinstance` | 6880 |
| step_limit | `prepare_calibration_run` | `first 12 steps` | 0 |
| truncated_flow | `prepare_calibration_run` | `depth limit` | 0 |

## Behavior

This flow starts at `prepare_calibration_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
