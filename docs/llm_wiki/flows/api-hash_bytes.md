# hash_bytes

**Entry point:** `hash_bytes` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [documentation_policy](../modules/documentation_policy.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_bytes
    participant p1 as hexdigest
    participant p2 as sha256
    p0-->>p1: hexdigest
    p0-->>p2: sha256
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_bytes"]
    s2["2. hexdigest"]
    s3["3. sha256"]
    s1 -. "hashlib.sha256(data).hexdigest(data not statically known)" .-> s2
    s1 -. "hashlib.sha256(data)" .-> s3
    click s1 "../modules/documentation_policy.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_bytes` | `data: bytes` | - | - | `...` |
| `hexdigest` | - | - | - | - |
| `sha256` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_bytes | hexdigest | 520 | `hashlib.sha256(data).hexdigest(data not statically known)` |
| hash_bytes | sha256 | 520 | `hashlib.sha256(data)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_bytes` | `hashlib.sha256(data).hexdigest` | 520 |
| external_call | `hash_bytes` | `hashlib.sha256` | 520 |

## Behavior

This flow starts at `hash_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
