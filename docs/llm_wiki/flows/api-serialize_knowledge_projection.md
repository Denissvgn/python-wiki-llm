# serialize_knowledge_projection

**Entry point:** `serialize_knowledge_projection` (`api`)
**Source:** [knowledge_projection](../modules/knowledge_projection.md)
**Modules touched:** [knowledge_projection](../modules/knowledge_projection.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_knowledge_projection
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as dumps
    participant p4 as to_payload
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: dumps
    p0-->>p4: to_payload
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_knowledge_projection"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. dumps"]
    s5["5. to_payload"]
    s1 -. "isinstance(projection, KnowledgeProjection)" .-> s2
    s1 -. "TypeError('projection must be a KnowledgeProjection')" .-> s3
    s1 -. "json.dumps(projection.to_payload(...), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)" .-> s4
    s1 -. "projection.to_payload(data not statically known)" .-> s5
    click s1 "../modules/knowledge_projection.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `serialize_knowledge_projection` | `projection: KnowledgeProjection` | `KnowledgeProjection` | - | `...` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `dumps` | - | - | - | - |
| `to_payload` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| serialize_knowledge_projection | isinstance | 388 | `isinstance(projection, KnowledgeProjection)` |
| serialize_knowledge_projection | TypeError | 389 | `TypeError('projection must be a KnowledgeProjection')` |
| serialize_knowledge_projection | dumps | 391 | `json.dumps(projection.to_payload(...), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)` |
| serialize_knowledge_projection | to_payload | 392 | `projection.to_payload(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `serialize_knowledge_projection` | `isinstance` | 388 |
| unresolved_call | `serialize_knowledge_projection` | `TypeError` | 389 |
| external_call | `serialize_knowledge_projection` | `json.dumps` | 391 |
| unresolved_call | `serialize_knowledge_projection` | `projection.to_payload` | 392 |

## Behavior

This flow starts at `serialize_knowledge_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
