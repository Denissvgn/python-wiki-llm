# formatted_json_bytes

**Entry point:** `formatted_json_bytes` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as formatted_json_bytes
    participant p1 as encode
    participant p2 as formatted_json_text
    participant p3 as dumps
    p0-->>p1: encode
    p0->>p2: formatted_json_text
    p2-->>p3: dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. formatted_json_bytes"]
    s2["2. encode"]
    s3["3. formatted_json_text"]
    s4["4. dumps"]
    s1 -. "formatted_json_text(value).encode('utf-8')" .-> s2
    s1 -->|"formatted_json_text(value)"| s3
    s3 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s4
    click s1 "../modules/knowledge_evidence.md"
    click s3 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `formatted_json_bytes` | `value: Any` | - | - | `...` |
| `encode` | - | - | - | - |
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| formatted_json_bytes | encode | 191 | `formatted_json_text(value).encode('utf-8')` |
| formatted_json_bytes | formatted_json_text | 191 | `formatted_json_text(value)` |
| formatted_json_text | dumps | 177 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `formatted_json_bytes` | `formatted_json_text(value).encode` | 191 |
| external_call | `formatted_json_text` | `json.dumps` | 177 |

## Behavior

This flow starts at `formatted_json_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
