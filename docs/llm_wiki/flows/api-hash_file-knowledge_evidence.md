# hash_file

**Entry point:** `hash_file` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_file
    participant p1 as sha256_bytes
    participant p2 as path.read_bytes
    participant p3 as hashlib.sha256(…).hexdigest
    participant p4 as hashlib.sha256
    p0->>p1: sha256_bytes
    p0-->>p2: path.read_bytes
    p1-->>p3: hashlib.sha256(…).hexdigest
    p1-->>p4: hashlib.sha256(value)
```

> Call sequence diagram shows 4 of 4 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 2 of 2 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_file"]
    s2["2. sha256_bytes"]
    s3["3. hashlib.sha256(…).hexdigest"]
    s4["4. hashlib.sha256"]
    s5["5. path.read_bytes"]
    s1 -->|"sha256_bytes(path.read_bytes(...))"| s2
    s2 -. "hashlib.sha256(…).hexdigest(data not statically known)" .-> s3
    s2 -. "hashlib.sha256(value)" .-> s4
    s1 -. "path.read_bytes(data not statically known)" .-> s5
    b0["filesystem_read path.read_bytes"]
    s1 -. "filesystem_read path.read_bytes" .-> b0
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_file` | `path: Path` | - | - | `sha256_bytes(...)`, `''` |
| `sha256_bytes` | `value: bytes` | - | - | `...` |
| `hashlib.sha256(…).hexdigest` | - | - | - | - |
| `hashlib.sha256` | - | - | - | - |
| `path.read_bytes` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_file | sha256_bytes | 938 | `sha256_bytes(path.read_bytes(...))` |
| sha256_bytes | hashlib.sha256(…).hexdigest | 221 | `hashlib.sha256(value).hexdigest(data not statically known)` |
| sha256_bytes | hashlib.sha256 | 221 | `hashlib.sha256(value)` |
| hash_file | path.read_bytes | 938 | `path.read_bytes(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_bytes` | `hash_file` | 938 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `sha256_bytes` | `hashlib.sha256(value).hexdigest` | 221 |
| external_call | `sha256_bytes` | `hashlib.sha256` | 221 |

## Behavior

This flow starts at `hash_file` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
