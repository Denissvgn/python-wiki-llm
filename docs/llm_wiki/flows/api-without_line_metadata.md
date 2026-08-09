# without_line_metadata

**Entry point:** `without_line_metadata` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as without_line_metadata
    participant p1 as isinstance
    participant p2 as sorted
    participant p3 as items
    p0-->>p1: isinstance
    p0->>p0: without_line_metadata
    p0-->>p2: sorted
    p0-->>p3: items
    p0-->>p1: isinstance
    p0->>p0: without_line_metadata
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. without_line_metadata"]
    s2["2. isinstance"]
    s3["3. without_line_metadata"]
    s4["4. sorted"]
    s5["5. items"]
    s6["6. isinstance"]
    s7["7. without_line_metadata"]
    s1 -. "isinstance(value, dict)" .-> s2
    s1 -->|"without_line_metadata(item)"| s3
    s1 -. "sorted(value.items(...))" .-> s4
    s1 -. "value.items(data not statically known)" .-> s5
    s1 -. "isinstance(value, list)" .-> s6
    s1 -->|"without_line_metadata(item)"| s7
    click s1 "../modules/knowledge_evidence.md"
    click s3 "../modules/knowledge_evidence.md"
    click s7 "../modules/knowledge_evidence.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `without_line_metadata` | `value: Any` | - | - | `...`, `...`, `value` |
| `isinstance` | - | - | - | - |
| `without_line_metadata` | `value: Any` | - | - | `...`, `...`, `value` |
| `sorted` | - | - | - | - |
| `items` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `without_line_metadata` | `value: Any` | - | - | `...`, `...`, `value` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| without_line_metadata | isinstance | 921 | `isinstance(value, dict)` |
| without_line_metadata | without_line_metadata | 923 | `without_line_metadata(item)` |
| without_line_metadata | sorted | 924 | `sorted(value.items(...))` |
| without_line_metadata | items | 924 | `value.items(data not statically known)` |
| without_line_metadata | isinstance | 927 | `isinstance(value, list)` |
| without_line_metadata | without_line_metadata | 928 | `without_line_metadata(item)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `without_line_metadata` | `isinstance` | 921 |
| unresolved_call | `without_line_metadata` | `sorted` | 924 |
| unresolved_call | `without_line_metadata` | `value.items` | 924 |
| unresolved_call | `without_line_metadata` | `isinstance` | 927 |

## Behavior

This flow starts at `without_line_metadata` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
