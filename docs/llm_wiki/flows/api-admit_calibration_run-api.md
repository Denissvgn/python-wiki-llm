# admit_calibration_run

**Entry point:** `admit_calibration_run` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as admit_calibration_run
    participant p1 as _call_calibration_controller
    participant p2 as <dynamic>
    participant p3 as getattr
    p0->>p1: _call_calibration_controller
    p1-->>p2: <dynamic>(..., **=kwargs)
    p1-->>p3: getattr(controller, name)
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. admit_calibration_run"]
    s2["2. _call_calibration_controller"]
    s3["3. #60;dynamic#62;"]
    s4["4. getattr"]
    s1 -->|"_call_calibration_controller('admit_calibration_run', root, authority_grant=authority_grant, broker_attestation=broker_attestation)"| s2
    s2 -. "#60;dynamic#62;(..., **=kwargs)" .-> s3
    s2 -. "getattr(controller, name)" .-> s4
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `admit_calibration_run` | `root: str \| Path`, `authority_grant: Mapping[str, Any]`, `broker_attestation: Mapping[str, Any] \| None` | - | - | `_call_calibration_controller(...)` |
| `_call_calibration_controller` | `name: str`, `args: Any`, `kwargs: Any` | - | - | `...` |
| `<dynamic>` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| admit_calibration_run | _call_calibration_controller | 3473 | `_call_calibration_controller('admit_calibration_run', root, authority_grant=authority_grant, broker_attestation=broker_attestation)` |
| _call_calibration_controller | <dynamic> | 3444 | `<dynamic>(..., **=kwargs)` |
| _call_calibration_controller | getattr | 3444 | `getattr(controller, name)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_call_calibration_controller` | `<dynamic>` | 3444 |
| external_call | `_call_calibration_controller` | `getattr` | 3444 |

## Behavior

This flow starts at `admit_calibration_run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
