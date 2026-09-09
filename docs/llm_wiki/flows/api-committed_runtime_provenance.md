# committed_runtime_provenance

**Entry point:** `committed_runtime_provenance` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [immutable](../modules/immutable.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 12 more

**Complete modules touched:**

- [immutable](../modules/immutable.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as committed_runtime_provenance
    participant p1 as _previous_committed_artifacts
    participant p2 as capture_committed_knowledge
    participant p3 as resolve
    participant p4 as Path
    participant p5 as read_bytes
    participant p6 as from_payload
    participant p7 as _decode_json_object
    participant p8 as isinstance
    participant p9 as KnowledgeArtifactError
    participant p10 as decode
    participant p11 as loads
    participant p12 as _unique_json_object
    participant p13 as _reject_json_constant
    participant p14 as to_payload
    participant p15 as validate_knowledge_artifacts
    participant p16 as validate_surface_index_bytes
    participant p17 as _validate_surface_payload
    participant p18 as _validate_utf8_json
    participant p19 as get
    p0->>p1: _previous_committed_artifacts
    p1->>p2: capture_committed_knowledge
    p2-->>p3: resolve
    p2-->>p4: Path
    p2-->>p5: read_bytes
    p2-->>p6: from_payload
    p2->>p7: _decode_json_object
    p7-->>p8: isinstance
    p7->>p9: KnowledgeArtifactError
    p7-->>p10: decode
    p7->>p9: KnowledgeArtifactError
    p7-->>p11: loads
    p7->>p12: _unique_json_object
    p12->>p9: KnowledgeArtifactError
    p7->>p13: _reject_json_constant
    p13->>p9: KnowledgeArtifactError
    p7-->>p8: isinstance
    p7->>p9: KnowledgeArtifactError
    p7-->>p8: isinstance
    p7->>p9: KnowledgeArtifactError
    p2-->>p14: to_payload
    p2-->>p14: to_payload
    p2->>p9: KnowledgeArtifactError
    p2->>p15: validate_knowledge_artifacts
    p15->>p16: validate_surface_index_bytes
    p16->>p7: _decode_json_object
    p16->>p17: _validate_surface_payload
    p17->>p18: _validate_utf8_json
    p17-->>p19: get
    p17->>p9: KnowledgeArtifactError
```

> Call sequence diagram shows 30 of 499 interactions; 469 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. committed_runtime_provenance"]
    s2["2. _previous_committed_artifacts"]
    s3["3. capture_committed_knowledge"]
    s4["4. resolve"]
    s5["5. Path"]
    s6["6. read_bytes"]
    s7["7. from_payload"]
    s8["8. _decode_json_object"]
    s9["9. isinstance"]
    s10["10. KnowledgeArtifactError"]
    s11["11. decode"]
    s12["12. KnowledgeArtifactError"]
    s1 -->|"_previous_committed_artifacts(wiki_dir, manifest, committed_state=committed_state)"| s2
    s2 -->|"capture_committed_knowledge(wiki_dir, manifest)"| s3
    s3 -. "Path(wiki_dir).resolve(data not statically known)" .-> s4
    s3 -. "Path(wiki_dir)" .-> s5
    s3 -. "(root / name).read_bytes(data not statically known)" .-> s6
    s3 -. "SyncManifest.from_payload(_decode_json_object(...))" .-> s7
    s3 -->|"_decode_json_object(captured[...], 'manifest')"| s8
    s8 -. "isinstance(content, bytes)" .-> s9
    s8 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s10
    s8 -. "content.decode('utf-8')" .-> s11
    s8 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s12
    click s1 "../modules/knowledge_orchestration.md"
    click s2 "../modules/knowledge_orchestration.md"
    click s3 "../modules/knowledge_orchestration.md"
    click s8 "../modules/knowledge_artifacts.md"
    click s10 "../modules/knowledge_artifacts.md"
    click s12 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `committed_runtime_provenance` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None`, `committed_state: CommittedKnowledgeState \| None` | - | - | `None`, `CommittedRuntimeProvenance(...)` |
| `_previous_committed_artifacts` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None`, `committed_state: CommittedKnowledgeState \| None` | - | - | `state.artifacts` |
| `capture_committed_knowledge` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MANIFEST_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KnowledgeArtifactError`, `_COMMITTED_STATE_TOKEN` | `captured[...]`, `captured[...]` | `state` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `read_bytes` | - | - | - | - |
| `from_payload` | - | - | - | - |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `decode` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| committed_runtime_provenance | _previous_committed_artifacts | 719 | `_previous_committed_artifacts(wiki_dir, manifest, committed_state=committed_state)` |
| _previous_committed_artifacts | capture_committed_knowledge | 690 | `capture_committed_knowledge(wiki_dir, manifest)` |
| capture_committed_knowledge | resolve | 226 | `Path(wiki_dir).resolve(data not statically known)` |
| capture_committed_knowledge | Path | 226 | `Path(wiki_dir)` |
| capture_committed_knowledge | read_bytes | 230 | `(root / name).read_bytes(data not statically known)` |
| capture_committed_knowledge | from_payload | 237 | `SyncManifest.from_payload(_decode_json_object(...))` |
| capture_committed_knowledge | _decode_json_object | 238 | `_decode_json_object(captured[...], 'manifest')` |
| _decode_json_object | isinstance | 574 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 575 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | decode | 577 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 579 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_committed_knowledge` | `Path(wiki_dir).resolve` | 226 |
| unresolved_call | `capture_committed_knowledge` | `(root / name).read_bytes` | 230 |
| external_call | `capture_committed_knowledge` | `SyncManifest.from_payload` | 237 |
| unresolved_call | `_decode_json_object` | `isinstance` | 574 |
| unresolved_call | `_decode_json_object` | `content.decode` | 577 |
| step_limit | `committed_runtime_provenance` | `first 12 steps` | 0 |
| truncated_flow | `committed_runtime_provenance` | `depth limit` | 0 |

## Behavior

This flow starts at `committed_runtime_provenance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
