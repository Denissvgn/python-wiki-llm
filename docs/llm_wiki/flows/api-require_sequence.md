# require_sequence

**Entry point:** `require_sequence` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_sequence
    participant p1 as isinstance
    p0-->>p1: isinstance(value, (...))
    p0-->>p1: isinstance(value, Mapping)
    p0-->>p1: isinstance(value, container_type)
    p0-->>p1: isinstance(value, Sequence)
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 4 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 7, emitted: 7, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. require_sequence"]
    s2["2. isinstance"]
    s3["3. isinstance"]
    s4["4. isinstance"]
    s5["5. isinstance"]
    s1 -. "isinstance(value, (...))" .-> s2
    s1 -. "isinstance(value, Mapping)" .-> s3
    s1 -. "isinstance(value, container_type)" .-> s4
    s1 -. "isinstance(value, Sequence)" .-> s5
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_sequence` | `value: object`, `error: Exception`, `container_type: type[object] \| tuple[type[object], ...]`, `reject_mapping: bool` | `Mapping`, `Sequence` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_sequence | isinstance | 790 | `isinstance(value, (...))` |
| require_sequence | isinstance | 791 | `isinstance(value, Mapping)` |
| require_sequence | isinstance | 792 | `isinstance(value, container_type)` |
| require_sequence | isinstance | 795 | `isinstance(value, Sequence)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_sequence` | `isinstance` | 790 |
| external_call | `require_sequence` | `isinstance` | 791 |
| external_call | `require_sequence` | `isinstance` | 792 |
| external_call | `require_sequence` | `isinstance` | 795 |

## Behavior

This flow starts at `require_sequence` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
