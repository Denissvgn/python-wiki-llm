# current_reference_providers

**Entry point:** `current_reference_providers` (`api`)
**Source:** [reference_providers](../modules/reference_providers.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md), [pack_interfaces](../modules/pack_interfaces.md), [reference_providers](../modules/reference_providers.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as current_reference_providers
    participant p1 as current_pack
    participant p2 as active_pack
    participant p3 as _ACTIVE_PACK.get
    p0->>p1: current_pack
    p1->>p2: active_pack
    p2-->>p3: _ACTIVE_PACK.get
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 3, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 4, emitted: 4, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. current_reference_providers"]
    s2["2. current_pack"]
    s3["3. active_pack"]
    s4["4. _ACTIVE_PACK.get"]
    s1 -->|"current_pack(data not statically known)"| s2
    s2 -->|"active_pack(data not statically known)"| s3
    s3 -. "_ACTIVE_PACK.get(data not statically known)" .-> s4
    click s1 "../modules/reference_providers.md"
    click s2 "../modules/domain_pack.md"
    click s3 "../modules/pack_interfaces.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `current_reference_providers` | - | - | - | `...` |
| `current_pack` | - | `CODE_DOCS_PACK` | - | `...` |
| `active_pack` | - | - | - | `_ACTIVE_PACK.get(...)` |
| `_ACTIVE_PACK.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| current_reference_providers | current_pack | 360 | `current_pack(data not statically known)` |
| current_pack | active_pack | 324 | `active_pack(data not statically known)` |
| active_pack | _ACTIVE_PACK.get | 643 | `_ACTIVE_PACK.get(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `active_pack` | `_ACTIVE_PACK.get` | 643 |

## Behavior

This flow starts at `current_reference_providers` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
