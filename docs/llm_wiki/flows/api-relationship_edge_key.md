# relationship_edge_key

**Entry point:** `relationship_edge_key` (`api`)
**Source:** [knowledge_graph](../modules/knowledge_graph.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_graph](../modules/knowledge_graph.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as relationship_edge_key
    participant p1 as next
    participant p2 as KnowledgeGraphError
    participant p3 as sha256_bytes
    participant p4 as hexdigest
    participant p5 as sha256
    participant p6 as encode
    participant p7 as _canonical_json
    participant p8 as canonical_json_text
    participant p9 as dumps
    p0-->>p1: next
    p0->>p2: KnowledgeGraphError
    p0->>p3: sha256_bytes
    p3-->>p4: hexdigest
    p3-->>p5: sha256
    p0-->>p6: encode
    p0->>p7: _canonical_json
    p7->>p8: canonical_json_text
    p8-->>p9: dumps
    p7->>p2: KnowledgeGraphError
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. relationship_edge_key"]
    s2["2. next"]
    s3["3. KnowledgeGraphError"]
    s4["4. sha256_bytes"]
    s5["5. hexdigest"]
    s6["6. sha256"]
    s7["7. encode"]
    s8["8. _canonical_json"]
    s9["9. canonical_json_text"]
    s10["10. dumps"]
    s11["11. KnowledgeGraphError"]
    s1 -. "next(..., None)" .-> s2
    s1 -->|"KnowledgeGraphError(..., 'is required for edge identity')"| s3
    s1 -->|"sha256_bytes(...)"| s4
    s4 -. "hashlib.sha256(value).hexdigest(data not statically known)" .-> s5
    s4 -. "hashlib.sha256(value)" .-> s6
    s1 -. "_canonical_json(preimage).encode('utf-8')" .-> s7
    s1 -->|"_canonical_json(preimage)"| s8
    s8 -->|"canonical_json_text(value)"| s9
    s9 -. "json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)" .-> s10
    s8 -->|"KnowledgeGraphError('value', 'must be finite canonical JSON')"| s11
    click s1 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s4 "../modules/knowledge_evidence.md"
    click s8 "../modules/knowledge_graph.md"
    click s9 "../modules/knowledge_evidence.md"
    click s11 "../modules/knowledge_graph.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `relationship_edge_key` | `identity: Mapping[str, Any]` | `TYPED_GRAPH_SCHEMA_VERSION` | - | `sha256_bytes(...)` |
| `next` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `sha256_bytes` | `value: bytes` | - | - | `...` |
| `hexdigest` | - | - | - | - |
| `sha256` | - | - | - | - |
| `encode` | - | - | - | - |
| `_canonical_json` | `value: object` | - | - | `canonical_json_text(...)` |
| `canonical_json_text` | `value: Any` | - | - | `json.dumps(...)` |
| `dumps` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| relationship_edge_key | next | 302 | `next(..., None)` |
| relationship_edge_key | KnowledgeGraphError | 304 | `KnowledgeGraphError(..., 'is required for edge identity')` |
| relationship_edge_key | sha256_bytes | 309 | `sha256_bytes(...)` |
| sha256_bytes | hexdigest | 197 | `hashlib.sha256(value).hexdigest(data not statically known)` |
| sha256_bytes | sha256 | 197 | `hashlib.sha256(value)` |
| relationship_edge_key | encode | 309 | `_canonical_json(preimage).encode('utf-8')` |
| relationship_edge_key | _canonical_json | 309 | `_canonical_json(preimage)` |
| _canonical_json | canonical_json_text | 2229 | `canonical_json_text(value)` |
| canonical_json_text | dumps | 158 | `json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)` |
| _canonical_json | KnowledgeGraphError | 2231 | `KnowledgeGraphError('value', 'must be finite canonical JSON')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `relationship_edge_key` | `next` | 302 |
| external_call | `sha256_bytes` | `hashlib.sha256(value).hexdigest` | 197 |
| external_call | `sha256_bytes` | `hashlib.sha256` | 197 |
| unresolved_call | `relationship_edge_key` | `_canonical_json(preimage).encode` | 309 |
| external_call | `canonical_json_text` | `json.dumps` | 158 |

## Behavior

This flow starts at `relationship_edge_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
