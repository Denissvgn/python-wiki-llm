# formatted_json_text

**Entry point:** `formatted_json_text` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as formatted_json_text
    participant p1 as dumps
    p0-->>p1: dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. formatted_json_text"]
    s2["2. dumps"]
    s1 -. "json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s2
    click s1 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `formatted_json_text` | `value: Any` | - | - | `...` |
| `dumps` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| formatted_json_text | dumps | 177 | `json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `formatted_json_text` | `json.dumps` | 177 |

## Behavior

This flow starts at `formatted_json_text` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
