# build_knowledge_commit_plan

**Entry point:** `build_knowledge_commit_plan` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 11 more

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
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_commit_plan
    participant p1 as Path
    participant p2 as validate_knowledge_artifacts
    participant p3 as validate_surface_index_bytes
    participant p4 as _decode_json_object
    participant p5 as isinstance
    participant p6 as KnowledgeArtifactError
    participant p7 as decode
    participant p8 as loads
    participant p9 as _unique_json_object
    participant p10 as _reject_json_constant
    participant p11 as _validate_surface_payload
    participant p12 as _validate_utf8_json
    participant p13 as encode
    participant p14 as items
    participant p15 as enumerate
    p0-->>p1: Path
    p0->>p2: validate_knowledge_artifacts
    p2->>p3: validate_surface_index_bytes
    p3->>p4: _decode_json_object
    p4-->>p5: isinstance
    p4->>p6: KnowledgeArtifactError
    p4-->>p7: decode
    p4->>p6: KnowledgeArtifactError
    p4-->>p8: loads
    p4->>p9: _unique_json_object
    p9->>p6: KnowledgeArtifactError
    p4->>p10: _reject_json_constant
    p10->>p6: KnowledgeArtifactError
    p4-->>p5: isinstance
    p4->>p6: KnowledgeArtifactError
    p4-->>p5: isinstance
    p4->>p6: KnowledgeArtifactError
    p3->>p11: _validate_surface_payload
    p11->>p12: _validate_utf8_json
    p12-->>p5: isinstance
    p12-->>p13: encode
    p12->>p6: KnowledgeArtifactError
    p12-->>p5: isinstance
    p12-->>p14: items
    p12-->>p5: isinstance
    p12->>p6: KnowledgeArtifactError
    p12->>p12: _validate_utf8_json
    p12->>p12: _validate_utf8_json
    p12-->>p5: isinstance
    p12-->>p15: enumerate
```

> Call sequence diagram shows 30 of 1464 interactions; 1434 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_knowledge_commit_plan"]
    s2["2. Path"]
    s3["3. validate_knowledge_artifacts"]
    s4["4. validate_surface_index_bytes"]
    s5["5. _decode_json_object"]
    s6["6. isinstance"]
    s7["7. KnowledgeArtifactError"]
    s8["8. decode"]
    s9["9. KnowledgeArtifactError"]
    s10["10. loads"]
    s11["11. _unique_json_object"]
    s12["12. KnowledgeArtifactError"]
    s1 -. "Path(wiki_dir)" .-> s2
    s1 -->|"validate_knowledge_artifacts(surface_index_bytes=surface_index_bytes, knowledge_index_bytes=knowledge_index_bytes, manifest=manifest)"| s3
    s3 -->|"validate_surface_index_bytes(surface_index_bytes)"| s4
    s4 -->|"_decode_json_object(surface_index_bytes, 'surface_index_bytes')"| s5
    s5 -. "isinstance(content, bytes)" .-> s6
    s5 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s7
    s5 -. "content.decode('utf-8')" .-> s8
    s5 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s9
    s5 -. "json.loads(text, object_pairs_hook=..., parse_constant=...)" .-> s10
    s5 -->|"_unique_json_object(pairs, field)"| s11
    s11 -->|"KnowledgeArtifactError(field, ...)"| s12
    click s1 "../modules/knowledge_artifacts.md"
    click s3 "../modules/knowledge_artifacts.md"
    click s4 "../modules/knowledge_artifacts.md"
    click s5 "../modules/knowledge_artifacts.md"
    click s7 "../modules/knowledge_artifacts.md"
    click s9 "../modules/knowledge_artifacts.md"
    click s11 "../modules/knowledge_artifacts.md"
    click s12 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_commit_plan` | `wiki_dir: str \| Path`, `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes`, `manifest: SyncManifest` | `SyncManifest`, `SURFACE_INDEX_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MANIFEST_FILENAME` | - | `KnowledgeCommitPlan(...)` |
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
| `KnowledgeArtifactError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_commit_plan | Path | 344 | `Path(wiki_dir)` |
| build_knowledge_commit_plan | validate_knowledge_artifacts | 345 | `validate_knowledge_artifacts(surface_index_bytes=surface_index_bytes, knowledge_index_bytes=knowledge_index_bytes, manifest=manifest)` |
| validate_knowledge_artifacts | validate_surface_index_bytes | 205 | `validate_surface_index_bytes(surface_index_bytes)` |
| validate_surface_index_bytes | _decode_json_object | 174 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance | 502 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 503 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | decode | 505 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 507 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | loads | 509 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 511 | `_unique_json_object(pairs, field)` |
| _unique_json_object | KnowledgeArtifactError | 530 | `KnowledgeArtifactError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_decode_json_object` | `isinstance` | 502 |
| unresolved_call | `_decode_json_object` | `content.decode` | 505 |
| external_call | `_decode_json_object` | `json.loads` | 509 |
| step_limit | `build_knowledge_commit_plan` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_commit_plan` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_commit_plan` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
