# with_infrastructure_generation_input

**Entry point:** `with_infrastructure_generation_input` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_sync](../modules/infrastructure_sync.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as with_infrastructure_generation_input
    participant p1 as deepcopy
    participant p2 as dict
    p0-->>p1: deepcopy
    p0-->>p2: dict
    p0-->>p1: deepcopy
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. with_infrastructure_generation_input"]
    s2["2. deepcopy"]
    s3["3. dict"]
    s4["4. deepcopy"]
    s1 -. "deepcopy(dict(...))" .-> s2
    s1 -. "dict(generation_inputs)" .-> s3
    s1 -. "deepcopy(plan.next_state)" .-> s4
    click s1 "../modules/infrastructure_sync.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `with_infrastructure_generation_input` | `generation_inputs: Mapping[str, object]`, `plan: InfrastructureSyncPlan` | - | `result[...]` | `result` |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `deepcopy` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| with_infrastructure_generation_input | deepcopy | 760 | `deepcopy(dict(...))` |
| with_infrastructure_generation_input | dict | 760 | `dict(generation_inputs)` |
| with_infrastructure_generation_input | deepcopy | 761 | `deepcopy(plan.next_state)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `with_infrastructure_generation_input` | `deepcopy` | 760 |
| external_call | `with_infrastructure_generation_input` | `deepcopy` | 761 |

## Behavior

This flow starts at `with_infrastructure_generation_input` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
