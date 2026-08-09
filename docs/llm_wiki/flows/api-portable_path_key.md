# portable_path_key

**Entry point:** `portable_path_key` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as portable_path_key
    participant p1 as casefold
    participant p2 as normalize
    p0-->>p1: casefold
    p0-->>p2: normalize
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. portable_path_key"]
    s2["2. casefold"]
    s3["3. normalize"]
    s1 -. "unicodedata.normalize('NFC', value).casefold(data not statically known)" .-> s2
    s1 -. "unicodedata.normalize('NFC', value)" .-> s3
    click s1 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `portable_path_key` | `value: str` | - | - | `...` |
| `casefold` | - | - | - | - |
| `normalize` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| portable_path_key | casefold | 412 | `unicodedata.normalize('NFC', value).casefold(data not statically known)` |
| portable_path_key | normalize | 412 | `unicodedata.normalize('NFC', value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `portable_path_key` | `unicodedata.normalize('NFC', value).casefold` | 412 |
| external_call | `portable_path_key` | `unicodedata.normalize` | 412 |

## Behavior

This flow starts at `portable_path_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
