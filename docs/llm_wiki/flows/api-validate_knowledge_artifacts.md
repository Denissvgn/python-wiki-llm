# validate_knowledge_artifacts

**Entry point:** `validate_knowledge_artifacts` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 12 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_knowledge_artifacts
    participant p1 as validate_surface_index_bytes
    participant p2 as _decode_json_object
    participant p3 as isinstance
    participant p4 as KnowledgeArtifactError
    participant p5 as decode
    participant p6 as loads
    participant p7 as _unique_json_object
    participant p8 as _reject_json_constant
    participant p9 as _validate_surface_payload
    participant p10 as _validate_utf8_json
    participant p11 as encode
    participant p12 as items
    participant p13 as enumerate
    participant p14 as get
    p0->>p1: validate_surface_index_bytes
    p1->>p2: _decode_json_object
    p2-->>p3: isinstance
    p2->>p4: KnowledgeArtifactError
    p2-->>p5: decode
    p2->>p4: KnowledgeArtifactError
    p2-->>p6: loads
    p2->>p7: _unique_json_object
    p7->>p4: KnowledgeArtifactError
    p2->>p8: _reject_json_constant
    p8->>p4: KnowledgeArtifactError
    p2-->>p3: isinstance
    p2->>p4: KnowledgeArtifactError
    p2-->>p3: isinstance
    p2->>p4: KnowledgeArtifactError
    p1->>p9: _validate_surface_payload
    p9->>p10: _validate_utf8_json
    p10-->>p3: isinstance
    p10-->>p11: encode
    p10->>p4: KnowledgeArtifactError
    p10-->>p3: isinstance
    p10-->>p12: items
    p10-->>p3: isinstance
    p10->>p4: KnowledgeArtifactError
    p10->>p10: _validate_utf8_json
    p10->>p10: _validate_utf8_json
    p10-->>p3: isinstance
    p10-->>p13: enumerate
    p10->>p10: _validate_utf8_json
    p9-->>p14: get
```

> Call sequence diagram shows 30 of 1960 interactions; 1930 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_knowledge_artifacts"]
    s2["2. validate_surface_index_bytes"]
    s3["3. _decode_json_object"]
    s4["4. isinstance"]
    s5["5. KnowledgeArtifactError"]
    s6["6. decode"]
    s7["7. KnowledgeArtifactError"]
    s8["8. loads"]
    s9["9. _unique_json_object"]
    s10["10. KnowledgeArtifactError"]
    s11["11. _reject_json_constant"]
    s12["12. KnowledgeArtifactError"]
    s1 -->|"validate_surface_index_bytes(surface_index_bytes)"| s2
    s2 -->|"_decode_json_object(surface_index_bytes, 'surface_index_bytes')"| s3
    s3 -. "isinstance(content, bytes)" .-> s4
    s3 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s5
    s3 -. "content.decode('utf-8')" .-> s6
    s3 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s7
    s3 -. "json.loads(text, object_pairs_hook=..., parse_constant=...)" .-> s8
    s3 -->|"_unique_json_object(pairs, field)"| s9
    s9 -->|"KnowledgeArtifactError(field, ...)"| s10
    s3 -->|"_reject_json_constant(value, field)"| s11
    s11 -->|"KnowledgeArtifactError(field, ...)"| s12
    click s1 "../modules/knowledge_artifacts.md"
    click s2 "../modules/knowledge_artifacts.md"
    click s3 "../modules/knowledge_artifacts.md"
    click s5 "../modules/knowledge_artifacts.md"
    click s7 "../modules/knowledge_artifacts.md"
    click s9 "../modules/knowledge_artifacts.md"
    click s10 "../modules/knowledge_artifacts.md"
    click s11 "../modules/knowledge_artifacts.md"
    click s12 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_knowledge_artifacts` | `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes`, `manifest: SyncManifest` | `KNOWLEDGE_SCHEMA_VERSION`, `_KNOWLEDGE_SCHEMA_VERSION_RE`, `ConceptKind`, `KnowledgeGraphError`, `TYPED_GRAPH_EXTENSION_KEY`, `INVENTORY_HASH_EXTENSION`, `TYPED_GRAPH_EXTENSION_KEY`, `SECTION_OWNERSHIP_EXTENSION_KEY` | - | `ValidatedKnowledgeArtifacts(...)` |
| `validate_surface_index_bytes` | `surface_index_bytes: bytes` | - | - | `surface_payload` |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `decode` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `loads` | - | - | - | - |
| `_unique_json_object` | `pairs: list[tuple[str, Any]]`, `field: str` | - | `result[...]` | `result` |
| `KnowledgeArtifactError` | - | - | - | - |
| `_reject_json_constant` | `value: str`, `field: str` | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_artifacts | validate_surface_index_bytes | 205 | `validate_surface_index_bytes(surface_index_bytes)` |
| validate_surface_index_bytes | _decode_json_object | 174 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance | 502 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 503 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | decode | 505 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 507 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | loads | 509 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 511 | `_unique_json_object(pairs, field)` |
| _unique_json_object | KnowledgeArtifactError | 530 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | _reject_json_constant | 512 | `_reject_json_constant(value, field)` |
| _reject_json_constant | KnowledgeArtifactError | 536 | `KnowledgeArtifactError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_decode_json_object` | `isinstance` | 502 |
| unresolved_call | `_decode_json_object` | `content.decode` | 505 |
| external_call | `_decode_json_object` | `json.loads` | 509 |
| step_limit | `validate_knowledge_artifacts` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_artifacts` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_artifacts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
