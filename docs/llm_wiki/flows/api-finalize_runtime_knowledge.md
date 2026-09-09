# finalize_runtime_knowledge

**Entry point:** `finalize_runtime_knowledge` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [immutable](../modules/immutable.md), [infrastructure_sync](../modules/infrastructure_sync.md), [io](../modules/io.md), and 19 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [immutable](../modules/immutable.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [markdown_sections](../modules/markdown_sections.md)
- [progress](../modules/progress.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as finalize_runtime_knowledge
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as capture_committed_knowledge
    participant p4 as resolve
    participant p5 as Path
    participant p6 as read_bytes
    participant p7 as from_payload
    participant p8 as _decode_json_object
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
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: capture_committed_knowledge
    p3-->>p4: resolve
    p3-->>p5: Path
    p3-->>p6: read_bytes
    p3-->>p7: from_payload
    p3->>p8: _decode_json_object
    p8-->>p1: isinstance
    p8->>p9: KnowledgeArtifactError
    p8-->>p10: decode
    p8->>p9: KnowledgeArtifactError
    p8-->>p11: loads
    p8->>p12: _unique_json_object
    p12->>p9: KnowledgeArtifactError
    p8->>p13: _reject_json_constant
    p13->>p9: KnowledgeArtifactError
    p8-->>p1: isinstance
    p8->>p9: KnowledgeArtifactError
    p8-->>p1: isinstance
    p8->>p9: KnowledgeArtifactError
    p3-->>p14: to_payload
    p3-->>p14: to_payload
    p3->>p9: KnowledgeArtifactError
    p3->>p15: validate_knowledge_artifacts
    p15->>p16: validate_surface_index_bytes
    p16->>p8: _decode_json_object
    p16->>p17: _validate_surface_payload
    p17->>p18: _validate_utf8_json
    p18-->>p1: isinstance
```

> Call sequence diagram shows 30 of 1993 interactions; 1963 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. finalize_runtime_knowledge"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. capture_committed_knowledge"]
    s5["5. resolve"]
    s6["6. Path"]
    s7["7. read_bytes"]
    s8["8. from_payload"]
    s9["9. _decode_json_object"]
    s10["10. isinstance"]
    s11["11. KnowledgeArtifactError"]
    s12["12. decode"]
    s1 -. "isinstance(inputs, RuntimeKnowledgeInputs)" .-> s2
    s1 -. "TypeError('inputs must be a RuntimeKnowledgeInputs')" .-> s3
    s1 -->|"capture_committed_knowledge(inputs.target_wiki_dir, inputs.previous_manifest)"| s4
    s4 -. "Path(wiki_dir).resolve(data not statically known)" .-> s5
    s4 -. "Path(wiki_dir)" .-> s6
    s4 -. "(root / name).read_bytes(data not statically known)" .-> s7
    s4 -. "SyncManifest.from_payload(_decode_json_object(...))" .-> s8
    s4 -->|"_decode_json_object(captured[...], 'manifest')"| s9
    s9 -. "isinstance(content, bytes)" .-> s10
    s9 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s11
    s9 -. "content.decode('utf-8')" .-> s12
    click s1 "../modules/knowledge_orchestration.md"
    click s4 "../modules/knowledge_orchestration.md"
    click s9 "../modules/knowledge_artifacts.md"
    click s11 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `finalize_runtime_knowledge` | `inputs: RuntimeKnowledgeInputs`, `dry_run: bool`, `fault_injector: FaultInjector \| None` | `RuntimeKnowledgeInputs`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME` | - | `_commit_runtime_knowledge(...)`, `_commit_runtime_knowledge(...)`, `_commit_runtime_knowledge(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `capture_committed_knowledge` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MANIFEST_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KnowledgeArtifactError`, `_COMMITTED_STATE_TOKEN` | `captured[...]`, `captured[...]` | `state` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `read_bytes` | - | - | - | - |
| `from_payload` | - | - | - | - |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `decode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| finalize_runtime_knowledge | isinstance | 771 | `isinstance(inputs, RuntimeKnowledgeInputs)` |
| finalize_runtime_knowledge | TypeError | 772 | `TypeError('inputs must be a RuntimeKnowledgeInputs')` |
| finalize_runtime_knowledge | capture_committed_knowledge | 775 | `capture_committed_knowledge(inputs.target_wiki_dir, inputs.previous_manifest)` |
| capture_committed_knowledge | resolve | 226 | `Path(wiki_dir).resolve(data not statically known)` |
| capture_committed_knowledge | Path | 226 | `Path(wiki_dir)` |
| capture_committed_knowledge | read_bytes | 230 | `(root / name).read_bytes(data not statically known)` |
| capture_committed_knowledge | from_payload | 237 | `SyncManifest.from_payload(_decode_json_object(...))` |
| capture_committed_knowledge | _decode_json_object | 238 | `_decode_json_object(captured[...], 'manifest')` |
| _decode_json_object | isinstance | 574 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 575 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | decode | 577 | `content.decode('utf-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `finalize_runtime_knowledge` | `isinstance` | 771 |
| unresolved_call | `finalize_runtime_knowledge` | `TypeError` | 772 |
| unresolved_call | `capture_committed_knowledge` | `Path(wiki_dir).resolve` | 226 |
| unresolved_call | `capture_committed_knowledge` | `(root / name).read_bytes` | 230 |
| external_call | `capture_committed_knowledge` | `SyncManifest.from_payload` | 237 |
| unresolved_call | `_decode_json_object` | `isinstance` | 574 |
| unresolved_call | `_decode_json_object` | `content.decode` | 577 |
| step_limit | `finalize_runtime_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `finalize_runtime_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `finalize_runtime_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
