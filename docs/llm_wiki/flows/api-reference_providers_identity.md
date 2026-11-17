# reference_providers_identity

**Entry point:** `reference_providers_identity` (`api`)
**Source:** [reference_providers](../modules/reference_providers.md)
**Modules touched:** [reference_providers](../modules/reference_providers.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as reference_providers_identity
    participant p1 as tuple
    participant p2 as type
    participant p3 as provider.identity
    p0-->>p1: tuple(...)
    p0-->>p2: type(provider)
    p0-->>p3: provider.identity
```

> Call sequence diagram shows 3 of 3 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 4, emitted: 4, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. reference_providers_identity"]
    s2["2. tuple"]
    s3["3. type"]
    s4["4. provider.identity"]
    s1 -. "tuple(...)" .-> s2
    s1 -. "type(provider)" .-> s3
    s1 -. "provider.identity(data not statically known)" .-> s4
    click s1 "../modules/reference_providers.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reference_providers_identity` | `providers: tuple[ReferenceProvider, ...]` | `_BUILTIN_TYPES` | - | `None`, `...` |
| `tuple` | - | - | - | - |
| `type` | - | - | - | - |
| `provider.identity` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reference_providers_identity | tuple | 351 | `tuple(...)` |
| reference_providers_identity | type | 351 | `type(provider)` |
| reference_providers_identity | provider.identity | 353 | `provider.identity(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `reference_providers_identity` | `type` | 351 |
| unresolved_call | `reference_providers_identity` | `provider.identity` | 353 |

## Behavior

This flow starts at `reference_providers_identity` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
