# build_calibration_agent_packet

**Entry point:** `build_calibration_agent_packet` (`api`)
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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_calibration_agent_packet
    participant p1 as _require_choice
    participant p2 as require_choice
    participant p3 as require_trimmed_text
    participant p4 as require_nonempty_text
    participant p5 as isinstance
    participant p6 as strip
    participant p7 as any
    participant p8 as ord
    participant p9 as frozenset
    participant p10 as choice_error
    participant p11 as P0CalibrationSchemaError
    participant p12 as join
    participant p13 as sorted
    participant p14 as _open_store
    participant p15 as ProtectedArtifactStore
    participant p16 as P0CalibrationIntegrityError
    participant p17 as str
    participant p18 as lock
    participant p19 as _load_run_locked
    participant p20 as exists
    participant p21 as _load_emergency_rejection
    participant p22 as read_json
    participant p23 as _require_exact_fields
    participant p24 as require_exact_fields
    participant p25 as set
    p0->>p1: _require_choice
    p1->>p2: require_choice
    p2->>p3: require_trimmed_text
    p3->>p4: require_nonempty_text
    p4-->>p5: isinstance
    p4-->>p6: strip
    p4-->>p7: any
    p4-->>p8: ord
    p4-->>p8: ord
    p2-->>p9: frozenset
    p2-->>p10: choice_error
    p1->>p11: P0CalibrationSchemaError
    p1->>p11: P0CalibrationSchemaError
    p1-->>p12: join
    p1-->>p13: sorted
    p0->>p14: _open_store
    p14->>p15: ProtectedArtifactStore
    p14->>p16: P0CalibrationIntegrityError
    p14-->>p17: str
    p0-->>p18: lock
    p0->>p19: _load_run_locked
    p19-->>p20: exists
    p19->>p21: _load_emergency_rejection
    p21-->>p22: read_json
    p21->>p23: _require_exact_fields
    p23->>p24: require_exact_fields
    p24-->>p5: isinstance
    p24-->>p17: str
    p24-->>p25: set
    p24-->>p25: set
```

> Call sequence diagram shows 30 of 1417 interactions; 1387 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_calibration_agent_packet"]
    s2["2. _require_choice"]
    s3["3. require_choice"]
    s4["4. require_trimmed_text"]
    s5["5. require_nonempty_text"]
    s6["6. isinstance"]
    s7["7. strip"]
    s8["8. any"]
    s9["9. ord"]
    s10["10. ord"]
    s11["11. frozenset"]
    s12["12. choice_error"]
    s1 -->|"_require_choice(role, CALIBRATION_ROLES, 'packet role')"| s2
    s2 -->|"require_shared_choice(value, choices, text_error=P0CalibrationSchemaError(...), choice_error=..., reject_control_characters=False)"| s3
    s3 -->|"require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)"| s4
    s4 -->|"require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)"| s5
    s5 -. "isinstance(value, str)" .-> s6
    s5 -. "value.strip(data not statically known)" .-> s7
    s5 -. "any(...)" .-> s8
    s5 -. "ord(character)" .-> s9
    s5 -. "ord(character)" .-> s10
    s3 -. "frozenset(choices)" .-> s11
    s3 -. "choice_error(allowed)" .-> s12
    click s1 "../modules/controller.md"
    click s2 "../modules/controller.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s5 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_calibration_agent_packet` | `root: str \| Path`, `role: str` | `CALIBRATION_ROLES`, `INTAKE_ROLES`, `CALIBRATION_ROLES`, `_MAX_BUNDLE_BYTES`, `P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION`, `CALIBRATION_CONTROLLER_MAX_PACKET_BYTES` | `roles[...]`, `packet_artifacts[...]`, `artifacts[...]` | `packet`, `P0CalibrationAgentPacket.from_dict(...)` |
| `_require_choice` | `value: Any`, `choices: Iterable[str]`, `label: str` | - | - | `require_shared_choice(...)` |
| `require_choice` | `value: object`, `choices: Iterable[str]`, `text_error: Exception`, `choice_error: Callable[[frozenset[str]], Exception]`, `reject_control_characters: bool` | - | - | `parsed` |
| `require_trimmed_text` | `value: object`, `error: Exception`, `reject_control_characters: bool` | - | - | `require_nonempty_text(...)` |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |
| `frozenset` | - | - | - | - |
| `choice_error` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_calibration_agent_packet | _require_choice | 1290 | `_require_choice(role, CALIBRATION_ROLES, 'packet role')` |
| _require_choice | require_choice | 6741 | `require_shared_choice(value, choices, text_error=P0CalibrationSchemaError(...), choice_error=..., reject_control_characters=False)` |
| require_choice | require_trimmed_text | 1035 | `require_trimmed_text(value, error=text_error, reject_control_characters=reject_control_characters)` |
| require_trimmed_text | require_nonempty_text | 658 | `require_nonempty_text(value, error=error, require_trimmed=True, reject_control_characters=reject_control_characters)` |
| require_nonempty_text | isinstance | 574 | `isinstance(value, str)` |
| require_nonempty_text | strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any | 582 | `any(...)` |
| require_nonempty_text | ord | 583 | `ord(character)` |
| require_nonempty_text | ord | 584 | `ord(character)` |
| require_choice | frozenset | 1040 | `frozenset(choices)` |
| require_choice | choice_error | 1042 | `choice_error(allowed)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_nonempty_text` | `isinstance` | 574 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 576 |
| unresolved_call | `require_nonempty_text` | `any` | 582 |
| unresolved_call | `require_nonempty_text` | `ord` | 583 |
| unresolved_call | `require_nonempty_text` | `ord` | 584 |
| unresolved_call | `require_choice` | `frozenset` | 1040 |
| unresolved_call | `require_choice` | `choice_error` | 1042 |
| step_limit | `build_calibration_agent_packet` | `first 12 steps` | 0 |
| truncated_flow | `build_calibration_agent_packet` | `depth limit` | 0 |

## Behavior

This flow starts at `build_calibration_agent_packet` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
