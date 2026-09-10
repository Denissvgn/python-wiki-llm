# canonical_json_bytes

**Entry point:** `canonical_json_bytes` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as canonical_json_bytes
    participant p1 as canonical_json_text(…).encode
    participant p2 as canonical_json_text
    participant p3 as json.dumps
    p0-->>p1: canonical_json_text(…).encode
    p0->>p2: canonical_json_text
    p2-->>p3: json.dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. canonical_json_bytes"]
    s2["2. canonical_json_text(…).encode"]
    s3["3. canonical_json_text"]
    s4["4. json.dumps"]
    s1 -. "canonical_json_text(…).encode('utf-8')" .-> s2
    s1 -->|"canonical_json_text(value)"| s3
    s3 -. "json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)" .-> s4
    click s1 "../modules/knowledge_evidence.md"
    click s3 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `canonical_json_bytes` | `value: Any` | - | - | `...` |
| `canonical_json_text(…).encode` | - | - | - | - |
| `canonical_json_text` | `value: Any` | - | - | `json.dumps(...)` |
| `json.dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| canonical_json_bytes | canonical_json_text(…).encode | 171 | `canonical_json_text(value).encode('utf-8')` |
| canonical_json_bytes | canonical_json_text | 171 | `canonical_json_text(value)` |
| canonical_json_text | json.dumps | 159 | `json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `canonical_json_bytes` | `canonical_json_text(value).encode` | 171 |
| external_call | `canonical_json_text` | `json.dumps` | 159 |

## Behavior

This flow starts at `canonical_json_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
