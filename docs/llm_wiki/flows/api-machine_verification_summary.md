# machine_verification_summary

**Entry point:** `machine_verification_summary` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [knowledge_verification](../modules/knowledge_verification.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as machine_verification_summary
    participant p1 as diagnostic.to_payload
    participant p2 as check.diagnostic_coverage.to_payload
    p0-->>p1: diagnostic.to_payload
    p0-->>p2: check.diagnostic_coverage.to_payload
```

> Call sequence diagram shows 2 of 2 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 0 of 0 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. machine_verification_summary"]
    s2["2. diagnostic.to_payload"]
    s3["3. check.diagnostic_coverage.to_payload"]
    s1 -. "diagnostic.to_payload(data not statically known)" .-> s2
    s1 -. "check.diagnostic_coverage.to_payload(data not statically known)" .-> s3
    click s1 "../modules/knowledge_verification.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `machine_verification_summary` | `receipt: VerificationReceipt`, `valid: bool`, `reasons: list[str]` | `VerificationResult` | - | `{...}` |
| `diagnostic.to_payload` | - | - | - | - |
| `check.diagnostic_coverage.to_payload` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| machine_verification_summary | diagnostic.to_payload | 252 | `diagnostic.to_payload(data not statically known)` |
| machine_verification_summary | check.diagnostic_coverage.to_payload | 254 | `check.diagnostic_coverage.to_payload(data not statically known)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `machine_verification_summary` | `diagnostic.to_payload` | 252 |
| unresolved_call | `machine_verification_summary` | `check.diagnostic_coverage.to_payload` | 254 |

## Behavior

This flow starts at `machine_verification_summary` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
