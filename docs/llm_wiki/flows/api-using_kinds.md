# using_kinds

**Entry point:** `using_kinds` (`api`)
**Source:** [knowledge_kinds](../modules/knowledge_kinds.md)
**Modules touched:** [knowledge_kinds](../modules/knowledge_kinds.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as using_kinds
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _ACTIVE_KINDS.set
    participant p4 as _ACTIVE_KINDS.reset
    p0-->>p1: isinstance(registry, KindRegistry)
    p0-->>p2: TypeError('registry must be a KindRegistry')
    p0-->>p3: _ACTIVE_KINDS.set(registry)
    p0-->>p4: _ACTIVE_KINDS.reset(token)
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
    s1["1. using_kinds"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _ACTIVE_KINDS.set"]
    s5["5. _ACTIVE_KINDS.reset"]
    s1 -. "isinstance(registry, KindRegistry)" .-> s2
    s1 -. "TypeError('registry must be a KindRegistry')" .-> s3
    s1 -. "_ACTIVE_KINDS.set(registry)" .-> s4
    s1 -. "_ACTIVE_KINDS.reset(token)" .-> s5
    click s1 "../modules/knowledge_kinds.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `using_kinds` | `registry: KindRegistry` | `KindRegistry` | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_ACTIVE_KINDS.set` | - | - | - | - |
| `_ACTIVE_KINDS.reset` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| using_kinds | isinstance | 272 | `isinstance(registry, KindRegistry)` |
| using_kinds | TypeError | 273 | `TypeError('registry must be a KindRegistry')` |
| using_kinds | _ACTIVE_KINDS.set | 274 | `_ACTIVE_KINDS.set(registry)` |
| using_kinds | _ACTIVE_KINDS.reset | 278 | `_ACTIVE_KINDS.reset(token)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `using_kinds` | `isinstance` | 272 |
| external_call | `using_kinds` | `TypeError` | 273 |
| unresolved_call | `using_kinds` | `_ACTIVE_KINDS.reset` | 278 |

## Behavior

This flow starts at `using_kinds` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
