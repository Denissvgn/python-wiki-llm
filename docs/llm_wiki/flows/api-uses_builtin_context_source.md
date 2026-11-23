# uses_builtin_context_source

**Entry point:** `uses_builtin_context_source` (`api`)
**Source:** [domain_pack](../modules/domain_pack.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md), [pack_interfaces](../modules/pack_interfaces.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as uses_builtin_context_source
    participant p1 as type
    participant p2 as current_pack
    participant p3 as active_pack
    participant p4 as _ACTIVE_PACK.get
    p0-->>p1: type(...)
    p0->>p2: current_pack
    p2->>p3: active_pack
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
    s1["1. uses_builtin_context_source"]
    s2["2. type"]
    s3["3. current_pack"]
    s4["4. active_pack"]
    s5["5. _ACTIVE_PACK.get"]
    s1 -. "type(...)" .-> s2
    s1 -->|"current_pack(data not statically known)"| s3
    s3 -->|"active_pack(data not statically known)"| s4
    s4 -. "_ACTIVE_PACK.get(data not statically known)" .-> s5
    click s1 "../modules/domain_pack.md"
    click s3 "../modules/domain_pack.md"
    click s4 "../modules/pack_interfaces.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `uses_builtin_context_source` | - | `CodeContextSource` | - | `...` |
| `type` | - | - | - | - |
| `current_pack` | - | `CODE_DOCS_PACK` | - | `...` |
| `active_pack` | - | - | - | `_ACTIVE_PACK.get(...)` |
| `_ACTIVE_PACK.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| uses_builtin_context_source | type | 231 | `type(...)` |
| uses_builtin_context_source | current_pack | 231 | `current_pack(data not statically known)` |
| current_pack | active_pack | 324 | `active_pack(data not statically known)` |
| active_pack | _ACTIVE_PACK.get | 643 | `_ACTIVE_PACK.get(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `uses_builtin_context_source` | `type` | 231 |
| unresolved_call | `active_pack` | `_ACTIVE_PACK.get` | 643 |

## Behavior

This flow starts at `uses_builtin_context_source` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
