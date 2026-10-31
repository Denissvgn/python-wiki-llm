# with_infrastructure_deselection_generation_input

**Entry point:** `with_infrastructure_deselection_generation_input` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_sync](../modules/infrastructure_sync.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as with_infrastructure_deselection_generation_input
    participant p1 as deepcopy
    participant p2 as dict
    p0-->>p1: deepcopy(dict(...))
    p0-->>p2: dict(generation_inputs)
    p0-->>p1: deepcopy(plan.deselection_only_state)
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 4, emitted: 4, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. with_infrastructure_deselection_generation_input"]
    s2["2. deepcopy"]
    s3["3. dict"]
    s4["4. deepcopy"]
    s1 -. "deepcopy(dict(...))" .-> s2
    s1 -. "dict(generation_inputs)" .-> s3
    s1 -. "deepcopy(plan.deselection_only_state)" .-> s4
    click s1 "../modules/infrastructure_sync.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `with_infrastructure_deselection_generation_input` | `generation_inputs: Mapping[str, object]`, `plan: InfrastructureSyncPlan` | - | `result[...]` | `result` |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `deepcopy` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| with_infrastructure_deselection_generation_input | deepcopy | 779 | `deepcopy(dict(...))` |
| with_infrastructure_deselection_generation_input | dict | 779 | `dict(generation_inputs)` |
| with_infrastructure_deselection_generation_input | deepcopy | 781 | `deepcopy(plan.deselection_only_state)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `with_infrastructure_deselection_generation_input` | `deepcopy` | 779 |
| external_call | `with_infrastructure_deselection_generation_input` | `deepcopy` | 781 |

## Behavior

This flow starts at `with_infrastructure_deselection_generation_input` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
