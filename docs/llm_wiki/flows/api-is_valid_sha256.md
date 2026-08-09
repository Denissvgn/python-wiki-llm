# is_valid_sha256

**Entry point:** `is_valid_sha256` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_valid_sha256
    participant p1 as isinstance
    participant p2 as fullmatch
    p0-->>p1: isinstance
    p0-->>p2: fullmatch
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_valid_sha256"]
    s2["2. isinstance"]
    s3["3. fullmatch"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "_SHA256_RE.fullmatch(value)" .-> s3
    click s1 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_valid_sha256` | `value: object` | - | - | `...` |
| `isinstance` | - | - | - | - |
| `fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_valid_sha256 | isinstance | 152 | `isinstance(value, str)` |
| is_valid_sha256 | fullmatch | 152 | `_SHA256_RE.fullmatch(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `is_valid_sha256` | `isinstance` | 152 |
| unresolved_call | `is_valid_sha256` | `_SHA256_RE.fullmatch` | 152 |

## Behavior

This flow starts at `is_valid_sha256` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
