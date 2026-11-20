# context_related_sources

**Entry point:** `context_related_sources` (`api`)
**Source:** [domain_pack](../modules/domain_pack.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md)

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
    participant p6 as _ACTIVE_PACK.get
    participant p7 as type
    p0->>p1: current_pack
    p0-->>p2: source.related_sources(inventory)
    p0-->>p3: isinstance(related, Mapping)
    p0-->>p4: TypeError(...)
    p0->>p5: _qualified_type_name
    p1-->>p6: _ACTIVE_PACK.get
    p5-->>p7: type(value)
```

> Call sequence diagram shows 7 of 7 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 3 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 3; effect analysis evaluated: 3, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 7, emitted: 7, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. context_related_sources"]
    s2["2. current_pack"]
    s3["3. _ACTIVE_PACK.get"]
    s4["4. source.related_sources"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. _qualified_type_name"]
    s8["8. type"]
    s1 -->|"current_pack(data not statically known)"| s2
    s2 -. "_ACTIVE_PACK.get(data not statically known)" .-> s3
    s1 -. "source.related_sources(inventory)" .-> s4
    s1 -. "isinstance(related, Mapping)" .-> s5
    s1 -. "TypeError(...)" .-> s6
    s1 -->|"_qualified_type_name(source)"| s7
    s7 -. "type(value)" .-> s8
    click s1 "../modules/domain_pack.md"
    click s2 "../modules/domain_pack.md"
    click s7 "../modules/domain_pack.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `context_related_sources` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping` | - | `related` |
| `current_pack` | - | `CODE_DOCS_PACK` | - | `...` |
| `_ACTIVE_PACK.get` | - | - | - | - |
| `source.related_sources` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_qualified_type_name` | `value: object` | - | - | `...` |
| `type` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| context_related_sources | current_pack | 219 | `current_pack(data not statically known)` |
| current_pack | _ACTIVE_PACK.get | 588 | `_ACTIVE_PACK.get(data not statically known)` |
| context_related_sources | source.related_sources | 220 | `source.related_sources(inventory)` |
| context_related_sources | isinstance | 221 | `isinstance(related, Mapping)` |
| context_related_sources | TypeError | 222 | `TypeError(...)` |
| context_related_sources | _qualified_type_name | 223 | `_qualified_type_name(source)` |
| _qualified_type_name | type | 478 | `type(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `current_pack` | `_ACTIVE_PACK.get` | 588 |
| unresolved_call | `context_related_sources` | `source.related_sources` | 220 |
| external_call | `context_related_sources` | `isinstance` | 221 |
| external_call | `context_related_sources` | `TypeError` | 222 |
| external_call | `_qualified_type_name` | `type` | 478 |

## Behavior

This flow starts at `context_related_sources` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
