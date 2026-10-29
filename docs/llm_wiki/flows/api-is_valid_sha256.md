# is_valid_sha256

**Entry point:** `is_valid_sha256` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_valid_sha256
    participant p1 as isinstance
    participant p2 as _SHA256_RE.fullmatch
    p0-->>p1: isinstance(value, str)
    p0-->>p2: _SHA256_RE.fullmatch(value)
```

> Call sequence diagram shows 2 of 2 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 1 source steps with known totals: observed: 2, emitted: 2, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. is_valid_sha256"]
    s2["2. isinstance"]
    s3["3. _SHA256_RE.fullmatch"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "_SHA256_RE.fullmatch(value)" .-> s3
    click s1 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_valid_sha256` | `value: object` | - | - | `...` |
| `isinstance` | - | - | - | - |
| `_SHA256_RE.fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_valid_sha256 | isinstance | 176 | `isinstance(value, str)` |
| is_valid_sha256 | _SHA256_RE.fullmatch | 176 | `_SHA256_RE.fullmatch(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `is_valid_sha256` | `isinstance` | 176 |
| unresolved_call | `is_valid_sha256` | `_SHA256_RE.fullmatch` | 176 |

## Behavior

This flow starts at `is_valid_sha256` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
