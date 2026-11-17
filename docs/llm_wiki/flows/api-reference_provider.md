# reference_provider

**Entry point:** `reference_provider` (`api`)
**Source:** [reference_providers](../modules/reference_providers.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md), [reference_providers](../modules/reference_providers.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as reference_provider
    participant p1 as current_reference_providers
    participant p2 as KeyError
    participant p3 as current_pack
    participant p4 as _ACTIVE_PACK.get
    p0->>p1: current_reference_providers
    p0-->>p2: KeyError(...)
    p1->>p3: current_pack
    p3-->>p4: _ACTIVE_PACK.get
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 3, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 5, emitted: 5, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. reference_provider"]
    s2["2. current_reference_providers"]
    s3["3. current_pack"]
    s4["4. _ACTIVE_PACK.get"]
    s5["5. KeyError"]
    s1 -->|"current_reference_providers(data not statically known)"| s2
    s2 -->|"current_pack(data not statically known)"| s3
    s3 -. "_ACTIVE_PACK.get(data not statically known)" .-> s4
    s1 -. "KeyError(...)" .-> s5
    click s1 "../modules/reference_providers.md"
    click s2 "../modules/reference_providers.md"
    click s3 "../modules/domain_pack.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reference_provider` | `kind: str` | - | - | `providers[...]` |
| `current_reference_providers` | - | - | - | `...` |
| `current_pack` | - | `CODE_DOCS_PACK` | - | `...` |
| `_ACTIVE_PACK.get` | - | - | - | - |
| `KeyError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reference_provider | current_reference_providers | 365 | `current_reference_providers(data not statically known)` |
| current_reference_providers | current_pack | 360 | `current_pack(data not statically known)` |
| current_pack | _ACTIVE_PACK.get | 850 | `_ACTIVE_PACK.get(data not statically known)` |
| reference_provider | KeyError | 367 | `KeyError(...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `current_pack` | `_ACTIVE_PACK.get` | 850 |
| external_call | `reference_provider` | `KeyError` | 367 |

## Behavior

This flow starts at `reference_provider` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
