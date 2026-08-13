# record_calibration_agent_result

**Entry point:** `record_calibration_agent_result` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as record_calibration_agent_result
    participant p1 as _call_calibration_controller
    participant p2 as getattr
    p0->>p1: _call_calibration_controller
    p1-->>p2: getattr
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. record_calibration_agent_result"]
    s2["2. _call_calibration_controller"]
    s3["3. getattr"]
    s1 -->|"_call_calibration_controller('record_calibration_agent_result', root, dispatch_receipt=dispatch_receipt, result=result)"| s2
    s2 -. "getattr(controller, name)" .-> s3
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `record_calibration_agent_result` | `root: str \| Path`, `dispatch_receipt: P0CalibrationDispatchReceipt \| Mapping[str, Any]`, `result: P0CalibrationAgentResult \| Mapping[str, Any]` | - | - | `_call_calibration_controller(...)` |
| `_call_calibration_controller` | `name: str`, `args: Any`, `kwargs: Any` | - | - | `...` |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| record_calibration_agent_result | _call_calibration_controller | 2541 | `_call_calibration_controller('record_calibration_agent_result', root, dispatch_receipt=dispatch_receipt, result=result)` |
| _call_calibration_controller | getattr | 2456 | `getattr(controller, name)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_call_calibration_controller` | `getattr` | 2456 |

## Behavior

This flow starts at `record_calibration_agent_result` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
