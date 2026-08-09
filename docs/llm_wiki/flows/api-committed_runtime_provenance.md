# committed_runtime_provenance

**Entry point:** `committed_runtime_provenance` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), and 11 more

**Complete modules touched:**

- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as committed_runtime_provenance
    participant p1 as _previous_committed_artifacts
    participant p2 as Path
    participant p3 as validate_knowledge_artifacts
    participant p4 as validate_surface_index_bytes
    participant p5 as _decode_json_object
    participant p6 as isinstance
    participant p7 as KnowledgeArtifactError
    participant p8 as decode
    participant p9 as loads
    participant p10 as _unique_json_object
    participant p11 as _reject_json_constant
    participant p12 as _validate_surface_payload
    participant p13 as _validate_utf8_json
    participant p14 as encode
    participant p15 as items
    p0->>p1: _previous_committed_artifacts
    p1-->>p2: Path
    p1->>p3: validate_knowledge_artifacts
    p3->>p4: validate_surface_index_bytes
    p4->>p5: _decode_json_object
    p5-->>p6: isinstance
    p5->>p7: KnowledgeArtifactError
    p5-->>p8: decode
    p5->>p7: KnowledgeArtifactError
    p5-->>p9: loads
    p5->>p10: _unique_json_object
    p10->>p7: KnowledgeArtifactError
    p5->>p11: _reject_json_constant
    p11->>p7: KnowledgeArtifactError
    p5-->>p6: isinstance
    p5->>p7: KnowledgeArtifactError
    p5-->>p6: isinstance
    p5->>p7: KnowledgeArtifactError
    p4->>p12: _validate_surface_payload
    p12->>p13: _validate_utf8_json
    p13-->>p6: isinstance
    p13-->>p14: encode
    p13->>p7: KnowledgeArtifactError
    p13-->>p6: isinstance
    p13-->>p15: items
    p13-->>p6: isinstance
    p13->>p7: KnowledgeArtifactError
    p13->>p13: _validate_utf8_json
    p13->>p13: _validate_utf8_json
    p13-->>p6: isinstance
```

> Call sequence diagram shows 30 of 738 interactions; 708 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. committed_runtime_provenance"]
    s2["2. _previous_committed_artifacts"]
    s3["3. Path"]
    s4["4. validate_knowledge_artifacts"]
    s5["5. validate_surface_index_bytes"]
    s6["6. _decode_json_object"]
    s7["7. isinstance"]
    s8["8. KnowledgeArtifactError"]
    s9["9. decode"]
    s10["10. KnowledgeArtifactError"]
    s11["11. loads"]
    s12["12. _unique_json_object"]
    s1 -->|"_previous_committed_artifacts(wiki_dir, manifest)"| s2
    s2 -. "Path(wiki_dir)" .-> s3
    s2 -->|"validate_knowledge_artifacts(surface_index_bytes=..., knowledge_index_bytes=..., manifest=manifest)"| s4
    s4 -->|"validate_surface_index_bytes(surface_index_bytes)"| s5
    s5 -->|"_decode_json_object(surface_index_bytes, 'surface_index_bytes')"| s6
    s6 -. "isinstance(content, bytes)" .-> s7
    s6 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s8
    s6 -. "content.decode('utf-8')" .-> s9
    s6 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s10
    s6 -. "json.loads(text, object_pairs_hook=..., parse_constant=...)" .-> s11
    s6 -->|"_unique_json_object(pairs, field)"| s12
    click s1 "../modules/knowledge_orchestration.md"
    click s2 "../modules/knowledge_orchestration.md"
    click s4 "../modules/knowledge_artifacts.md"
    click s5 "../modules/knowledge_artifacts.md"
    click s6 "../modules/knowledge_artifacts.md"
    click s8 "../modules/knowledge_artifacts.md"
    click s10 "../modules/knowledge_artifacts.md"
    click s12 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `committed_runtime_provenance` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | - | - | `None`, `CommittedRuntimeProvenance(...)` |
| `_previous_committed_artifacts` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | `KnowledgeArtifactError` | - | `None`, `None`, `None`, `validated` |
| `Path` | - | - | - | - |
| `validate_knowledge_artifacts` | `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes`, `manifest: SyncManifest` | `KNOWLEDGE_SCHEMA_VERSION`, `_KNOWLEDGE_SCHEMA_VERSION_RE`, `ConceptKind`, `KnowledgeGraphError`, `TYPED_GRAPH_EXTENSION_KEY`, `INVENTORY_HASH_EXTENSION`, `TYPED_GRAPH_EXTENSION_KEY`, `SECTION_OWNERSHIP_EXTENSION_KEY` | - | `ValidatedKnowledgeArtifacts(...)` |
| `validate_surface_index_bytes` | `surface_index_bytes: bytes` | - | - | `surface_payload` |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `decode` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `loads` | - | - | - | - |
| `_unique_json_object` | `pairs: list[tuple[str, Any]]`, `field: str` | - | `result[...]` | `result` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| committed_runtime_provenance | _previous_committed_artifacts | 614 | `_previous_committed_artifacts(wiki_dir, manifest)` |
| _previous_committed_artifacts | Path | 576 | `Path(wiki_dir)` |
| _previous_committed_artifacts | validate_knowledge_artifacts | 578 | `validate_knowledge_artifacts(surface_index_bytes=..., knowledge_index_bytes=..., manifest=manifest)` |
| validate_knowledge_artifacts | validate_surface_index_bytes | 205 | `validate_surface_index_bytes(surface_index_bytes)` |
| validate_surface_index_bytes | _decode_json_object | 174 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance | 502 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 503 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | decode | 505 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 507 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | loads | 509 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 511 | `_unique_json_object(pairs, field)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_decode_json_object` | `isinstance` | 502 |
| unresolved_call | `_decode_json_object` | `content.decode` | 505 |
| external_call | `_decode_json_object` | `json.loads` | 509 |
| step_limit | `committed_runtime_provenance` | `first 12 steps` | 0 |
| truncated_flow | `committed_runtime_provenance` | `depth limit` | 0 |

## Behavior

This flow starts at `committed_runtime_provenance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
