# hash_json

**Entry point:** `hash_json` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_json
    participant p1 as sha256_bytes
    participant p2 as hexdigest
    participant p3 as sha256
    participant p4 as canonical_json_bytes
    participant p5 as encode
    participant p6 as canonical_json_text
    participant p7 as dumps
    p0->>p1: sha256_bytes
    p1-->>p2: hexdigest
    p1-->>p3: sha256
    p0->>p4: canonical_json_bytes
    p4-->>p5: encode
    p4->>p6: canonical_json_text
    p6-->>p7: dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_json"]
    s2["2. sha256_bytes"]
    s3["3. hexdigest"]
    s4["4. sha256"]
    s5["5. canonical_json_bytes"]
    s6["6. encode"]
    s7["7. canonical_json_text"]
    s8["8. dumps"]
    s1 -->|"sha256_bytes(canonical_json_bytes(...))"| s2
    s2 -. "hashlib.sha256(value).hexdigest(data not statically known)" .-> s3
    s2 -. "hashlib.sha256(value)" .-> s4
    s1 -->|"canonical_json_bytes(value)"| s5
    s5 -. "canonical_json_text(value).encode('utf-8')" .-> s6
    s5 -->|"canonical_json_text(value)"| s7
    s7 -. "json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)" .-> s8
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s5 "../modules/knowledge_evidence.md"
    click s7 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_json` | `value: Any` | - | - | `sha256_bytes(...)` |
| `sha256_bytes` | `value: bytes` | - | - | `...` |
| `hexdigest` | - | - | - | - |
| `sha256` | - | - | - | - |
| `canonical_json_bytes` | `value: Any` | - | - | `...` |
| `encode` | - | - | - | - |
| `canonical_json_text` | `value: Any` | - | - | `json.dumps(...)` |
| `dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_json | sha256_bytes | 203 | `sha256_bytes(canonical_json_bytes(...))` |
| sha256_bytes | hexdigest | 197 | `hashlib.sha256(value).hexdigest(data not statically known)` |
| sha256_bytes | sha256 | 197 | `hashlib.sha256(value)` |
| hash_json | canonical_json_bytes | 203 | `canonical_json_bytes(value)` |
| canonical_json_bytes | encode | 170 | `canonical_json_text(value).encode('utf-8')` |
| canonical_json_bytes | canonical_json_text | 170 | `canonical_json_text(value)` |
| canonical_json_text | dumps | 158 | `json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `sha256_bytes` | `hashlib.sha256(value).hexdigest` | 197 |
| external_call | `sha256_bytes` | `hashlib.sha256` | 197 |
| unresolved_call | `canonical_json_bytes` | `canonical_json_text(value).encode` | 170 |
| external_call | `canonical_json_text` | `json.dumps` | 158 |

## Behavior

This flow starts at `hash_json` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
