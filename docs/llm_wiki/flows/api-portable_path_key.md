# portable_path_key

**Entry point:** `portable_path_key` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as portable_path_key
    participant p1 as unicodedata.normalize(…).casefold
    participant p2 as unicodedata.normalize
    p0-->>p1: unicodedata.normalize(…).casefold
    p0-->>p2: unicodedata.normalize('NFC', value)
```

> Call sequence diagram shows 2 of 2 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. portable_path_key"]
    s2["2. unicodedata.normalize(…).casefold"]
    s3["3. unicodedata.normalize"]
    s1 -. "unicodedata.normalize(…).casefold(data not statically known)" .-> s2
    s1 -. "unicodedata.normalize('NFC', value)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `portable_path_key` | `value: str` | - | - | `...` |
| `unicodedata.normalize(…).casefold` | - | - | - | - |
| `unicodedata.normalize` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| portable_path_key | unicodedata.normalize(…).casefold | 461 | `unicodedata.normalize('NFC', value).casefold(data not statically known)` |
| portable_path_key | unicodedata.normalize | 461 | `unicodedata.normalize('NFC', value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `portable_path_key` | `unicodedata.normalize('NFC', value).casefold` | 461 |
| external_call | `portable_path_key` | `unicodedata.normalize` | 461 |

## Behavior

This flow starts at `portable_path_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
