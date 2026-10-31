# knowledge_freshness_hint

**Entry point:** `knowledge_freshness_hint` (`api`)
**Source:** [knowledge_observability](../modules/knowledge_observability.md)
**Modules touched:** [knowledge_observability](../modules/knowledge_observability.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as knowledge_freshness_hint
    participant p1 as isinstance
    participant p2 as ValueError
    p0-->>p1: isinstance(state, ComputedFreshness)
    p0-->>p1: isinstance(reason_code, str)
    p0-->>p2: ValueError('basis-incompatible freshness requires a known actionable reason code')
    p0-->>p2: ValueError('basis-incompatible freshness requires a known actionable reason code')
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 4 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 9, emitted: 9, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. knowledge_freshness_hint"]
    s2["2. isinstance"]
    s3["3. isinstance"]
    s4["4. ValueError"]
    s5["5. ValueError"]
    s1 -. "isinstance(state, ComputedFreshness)" .-> s2
    s1 -. "isinstance(reason_code, str)" .-> s3
    s1 -. "ValueError('basis-incompatible freshness requires a known actionable reason code')" .-> s4
    s1 -. "ValueError('basis-incompatible freshness requires a known actionable reason code')" .-> s5
    click s1 "../modules/knowledge_observability.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `knowledge_freshness_hint` | `state: ComputedFreshness \| str \| None`, `reason_code: object` | `ComputedFreshness`, `ComputedFreshness`, `ComputedFreshness`, `BASIS_INCOMPATIBLE_HINTS` | - | `SOURCE_CHANGED_STRUCTURE_UNCHANGED`, `None`, `BASIS_INCOMPATIBLE_HINTS[...]` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `ValueError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| knowledge_freshness_hint | isinstance | 471 | `isinstance(state, ComputedFreshness)` |
| knowledge_freshness_hint | isinstance | 478 | `isinstance(reason_code, str)` |
| knowledge_freshness_hint | ValueError | 479 | `ValueError('basis-incompatible freshness requires a known actionable reason code')` |
| knowledge_freshness_hint | ValueError | 485 | `ValueError('basis-incompatible freshness requires a known actionable reason code')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `knowledge_freshness_hint` | `isinstance` | 471 |
| external_call | `knowledge_freshness_hint` | `isinstance` | 478 |
| external_call | `knowledge_freshness_hint` | `ValueError` | 479 |
| external_call | `knowledge_freshness_hint` | `ValueError` | 485 |

## Behavior

This flow starts at `knowledge_freshness_hint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
