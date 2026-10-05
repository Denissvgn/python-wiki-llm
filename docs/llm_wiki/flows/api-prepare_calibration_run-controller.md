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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as prepare_calibration_run
    participant p1 as isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p2 as len (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p3 as P0CalibrationSchemaError
    participant p4 as _json_round_trip
    participant p5 as _validate_execution_manifest
    participant p6 as _load_control_workspace
    participant p7 as Path (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p8 as enumerate (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p9 as P0CalibrationIntegrityError
    participant p10 as _assert_controls_match
    participant p11 as _validate_protected_root_placement
    participant p12 as str (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p13 as uuid.uuid4 (src/llm_wiki_cli/services…y:prepare_calibration_run)
    participant p14 as _implementation_worktree_roots
    participant p15 as _compile_evidence_bundle
    participant p16 as zip
    participant p17 as _portable_control_record
    participant p18 as any (src/llm_wiki_cli/services…y:prepare_calibration_run)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces, (...))
    p0-->>p2: len (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces)
    p0->>p3: P0CalibrationSchemaError
    p0->>p4: _json_round_trip
    p0->>p5: _validate_execution_manifest
    p0->>p6: _load_control_workspace
    p0-->>p7: Path (src/llm_wiki_cli/services…y:prepare_calibration_run)(value)
    p0-->>p8: enumerate (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces, start=1)
    p0->>p9: P0CalibrationIntegrityError
    p0->>p9: P0CalibrationIntegrityError
    p0->>p10: _assert_controls_match
    p0->>p11: _validate_protected_root_placement
    p0-->>p7: Path (src/llm_wiki_cli/services…y:prepare_calibration_run)(root)
    p0-->>p12: str (src/llm_wiki_cli/services…y:prepare_calibration_run)(uuid.uuid4(...))
    p0-->>p13: uuid.uuid4 (src/llm_wiki_cli/services…y:prepare_calibration_run)
    p0->>p14: _implementation_worktree_roots
    p0-->>p7: Path (src/llm_wiki_cli/services…y:prepare_calibration_run)(record[...])
    p0->>p15: _compile_evidence_bundle
    p0->>p15: _compile_evidence_bundle
    p0->>p9: P0CalibrationIntegrityError
    p0->>p6: _load_control_workspace
    p0-->>p7: Path (src/llm_wiki_cli/services…y:prepare_calibration_run)(value)
    p0-->>p8: enumerate (src/llm_wiki_cli/services…y:prepare_calibration_run)(control_workspaces, start=1)
    p0->>p10: _assert_controls_match
    p0-->>p16: zip(controls, refreshed_controls)
    p0->>p17: _portable_control_record
    p0->>p17: _portable_control_record
    p0-->>p18: any (src/llm_wiki_cli/services…y:prepare_calibration_run)(...)
    p0->>p9: P0CalibrationIntegrityError
    p0-->>p2: len (src/llm_wiki_cli/services…y:prepare_calibration_run)(canonical_json_bytes(...))
```

> Call sequence diagram shows 30 of 1294 interactions; 1264 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 13 of 350 (337 omitted); unresolved 0 of 396 (396 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/calibration/controller.py:_json_round_trip` | 5 | - | external | 4 |
| `src/llm_wiki_cli/services/calibration/controller.py:_json_round_trip` | 5 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 3 |
| `src/llm_wiki_cli/services/calibration/controller.py:_validate_execution_manifest` | 13 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 20 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 14 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 15 | - | external | 9 |
| `src/llm_wiki_cli/services/validation.py:require_exact_fields` | 15 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 14 | [src/llm_wiki_cli/services/calibration/controller.py](../modules/controller.md) | internal | 2 |
| `src/llm_wiki_cli/services/calibration/controller.py:_require_exact_fields` | 14 | - | unresolved | 2 |
> Omission summary shows 8 of 258 groups; 250 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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

*No boundary effects detected.*

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
