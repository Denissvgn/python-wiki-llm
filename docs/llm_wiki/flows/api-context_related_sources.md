# context_related_sources

**Entry point:** `context_related_sources` (`api`)
**Source:** [domain_pack](../modules/domain_pack.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md), [pack_interfaces](../modules/pack_interfaces.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as context_related_sources
    participant p1 as current_pack
    participant p2 as source.related_sources
    participant p3 as isinstance
    participant p4 as TypeError
    participant p5 as _qualified_type_name
    participant p6 as active_pack
    participant p7 as type
    participant p8 as _ACTIVE_PACK.get
    p0->>p1: current_pack
    p0-->>p2: source.related_sources(inventory)
    p0-->>p3: isinstance(related, Mapping)
    p0-->>p4: TypeError(...)
    p0->>p5: _qualified_type_name
    p1->>p6: active_pack
    p5-->>p7: type(value)
    p6-->>p8: _ACTIVE_PACK.get
```

> Call sequence diagram shows 8 of 8 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 4, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 4 source steps with known totals: observed: 8, emitted: 8, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. context_related_sources"]
    s2["2. current_pack"]
    s3["3. active_pack"]
    s4["4. _ACTIVE_PACK.get"]
    s5["5. source.related_sources"]
    s6["6. isinstance"]
    s7["7. TypeError"]
    s8["8. _qualified_type_name"]
    s9["9. type"]
    s1 -->|"current_pack(data not statically known)"| s2
    s2 -->|"active_pack(data not statically known)"| s3
    s3 -. "_ACTIVE_PACK.get(data not statically known)" .-> s4
    s1 -. "source.related_sources(inventory)" .-> s5
    s1 -. "isinstance(related, Mapping)" .-> s6
    s1 -. "TypeError(...)" .-> s7
    s1 -->|"_qualified_type_name(source)"| s8
    s8 -. "type(value)" .-> s9
    click s1 "../modules/domain_pack.md"
    click s2 "../modules/domain_pack.md"
    click s3 "../modules/pack_interfaces.md"
    click s8 "../modules/pack_interfaces.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `context_related_sources` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping` | - | `related` |
| `current_pack` | - | `CODE_DOCS_PACK` | - | `...` |
| `active_pack` | - | - | - | `_ACTIVE_PACK.get(...)` |
| `_ACTIVE_PACK.get` | - | - | - | - |
| `source.related_sources` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_qualified_type_name` | `value: object` | - | - | `...` |
| `type` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| context_related_sources | current_pack | 211 | `current_pack(data not statically known)` |
| current_pack | active_pack | 324 | `active_pack(data not statically known)` |
| active_pack | _ACTIVE_PACK.get | 643 | `_ACTIVE_PACK.get(data not statically known)` |
| context_related_sources | source.related_sources | 212 | `source.related_sources(inventory)` |
| context_related_sources | isinstance | 213 | `isinstance(related, Mapping)` |
| context_related_sources | TypeError | 214 | `TypeError(...)` |
| context_related_sources | _qualified_type_name | 215 | `_qualified_type_name(source)` |
| _qualified_type_name | type | 546 | `type(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `active_pack` | `_ACTIVE_PACK.get` | 643 |
| unresolved_call | `context_related_sources` | `source.related_sources` | 212 |
| external_call | `context_related_sources` | `isinstance` | 213 |
| external_call | `context_related_sources` | `TypeError` | 214 |
| external_call | `_qualified_type_name` | `type` | 546 |

## Behavior

This flow starts at `context_related_sources` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
