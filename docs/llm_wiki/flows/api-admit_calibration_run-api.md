# admit_calibration_run

**Entry point:** `admit_calibration_run` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as admit_calibration_run
    participant p1 as _call_calibration_controller
    participant p2 as getattr
    p0->>p1: _call_calibration_controller
    p1-->>p2: getattr
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. admit_calibration_run"]
    s2["2. _call_calibration_controller"]
    s3["3. getattr"]
    s1 -->|"_call_calibration_controller('admit_calibration_run', root, authority_grant=authority_grant, broker_attestation=broker_attestation)"| s2
    s2 -. "getattr(controller, name)" .-> s3
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `admit_calibration_run` | `root: str \| Path`, `authority_grant: Mapping[str, Any]`, `broker_attestation: Mapping[str, Any] \| None` | - | - | `_call_calibration_controller(...)` |
| `_call_calibration_controller` | `name: str`, `args: Any`, `kwargs: Any` | - | - | `...` |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| admit_calibration_run | _call_calibration_controller | 1411 | `_call_calibration_controller('admit_calibration_run', root, authority_grant=authority_grant, broker_attestation=broker_attestation)` |
| _call_calibration_controller | getattr | 1382 | `getattr(controller, name)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_call_calibration_controller` | `getattr` | 1382 |

## Behavior

This flow starts at `admit_calibration_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
