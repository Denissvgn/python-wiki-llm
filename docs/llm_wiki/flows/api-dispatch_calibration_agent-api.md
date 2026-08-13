# dispatch_calibration_agent

**Entry point:** `dispatch_calibration_agent` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as dispatch_calibration_agent
    participant p1 as _call_calibration_controller
    participant p2 as getattr
    p0->>p1: _call_calibration_controller
    p1-->>p2: getattr
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. dispatch_calibration_agent"]
    s2["2. _call_calibration_controller"]
    s3["3. getattr"]
    s1 -->|"_call_calibration_controller('dispatch_calibration_agent', root, role=role)"| s2
    s2 -. "getattr(controller, name)" .-> s3
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `dispatch_calibration_agent` | `root: str \| Path`, `role: str` | - | - | `_call_calibration_controller(...)` |
| `_call_calibration_controller` | `name: str`, `args: Any`, `kwargs: Any` | - | - | `...` |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| dispatch_calibration_agent | _call_calibration_controller | 2525 | `_call_calibration_controller('dispatch_calibration_agent', root, role=role)` |
| _call_calibration_controller | getattr | 2456 | `getattr(controller, name)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_call_calibration_controller` | `getattr` | 2456 |

## Behavior

This flow starts at `dispatch_calibration_agent` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
