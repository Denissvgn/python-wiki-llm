# using_pack

**Entry point:** `using_pack` (`api`)
**Source:** [domain_pack](../modules/domain_pack.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as using_pack
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _ACTIVE_PACK.set
    participant p4 as _ACTIVE_PACK.reset
    p0-->>p1: isinstance(pack, DomainPack)
    p0-->>p2: TypeError('pack must be a DomainPack')
    p0-->>p3: _ACTIVE_PACK.set(pack)
    p0-->>p4: _ACTIVE_PACK.reset(token)
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 2, emitted: 2, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. using_pack"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _ACTIVE_PACK.set"]
    s5["5. _ACTIVE_PACK.reset"]
    s1 -. "isinstance(pack, DomainPack)" .-> s2
    s1 -. "TypeError('pack must be a DomainPack')" .-> s3
    s1 -. "_ACTIVE_PACK.set(pack)" .-> s4
    s1 -. "_ACTIVE_PACK.reset(token)" .-> s5
    click s1 "../modules/domain_pack.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `using_pack` | `pack: DomainPack` | `DomainPack` | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_ACTIVE_PACK.set` | - | - | - | - |
| `_ACTIVE_PACK.reset` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| using_pack | isinstance | 864 | `isinstance(pack, DomainPack)` |
| using_pack | TypeError | 865 | `TypeError('pack must be a DomainPack')` |
| using_pack | _ACTIVE_PACK.set | 866 | `_ACTIVE_PACK.set(pack)` |
| using_pack | _ACTIVE_PACK.reset | 870 | `_ACTIVE_PACK.reset(token)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `using_pack` | `isinstance` | 864 |
| external_call | `using_pack` | `TypeError` | 865 |
| unresolved_call | `using_pack` | `_ACTIVE_PACK.reset` | 870 |

## Behavior

This flow starts at `using_pack` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
