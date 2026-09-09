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
    participant p3 as replace
    participant p4 as capture_committed_knowledge
    participant p5 as resolve
    participant p6 as Path
    participant p7 as read_bytes
    participant p8 as from_payload
    participant p9 as _decode_json_object
    participant p10 as KnowledgeArtifactError
    participant p11 as decode
    participant p12 as loads
    participant p13 as _unique_json_object
    participant p14 as _reject_json_constant
    participant p15 as to_payload
    participant p16 as validate_knowledge_artifacts
    participant p17 as validate_surface_index_bytes
    participant p18 as _validate_surface_payload
    participant p19 as _validate_utf8_json
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: replace
    p0->>p4: capture_committed_knowledge
    p4-->>p5: resolve
    p4-->>p6: Path
    p4-->>p7: read_bytes
    p4-->>p8: from_payload
    p4->>p9: _decode_json_object
    p9-->>p1: isinstance
    p9->>p10: KnowledgeArtifactError
    p9-->>p11: decode
    p9->>p10: KnowledgeArtifactError
    p9-->>p12: loads
    p9->>p13: _unique_json_object
    p13->>p10: KnowledgeArtifactError
    p9->>p14: _reject_json_constant
    p14->>p10: KnowledgeArtifactError
    p9-->>p1: isinstance
    p9->>p10: KnowledgeArtifactError
    p9-->>p1: isinstance
    p9->>p10: KnowledgeArtifactError
    p4-->>p15: to_payload
    p4-->>p15: to_payload
    p4->>p10: KnowledgeArtifactError
    p4->>p16: validate_knowledge_artifacts
    p16->>p17: validate_surface_index_bytes
    p17->>p9: _decode_json_object
    p17->>p18: _validate_surface_payload
    p18->>p19: _validate_utf8_json
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
    s4["4. replace"]
    s5["5. capture_committed_knowledge"]
    s6["6. resolve"]
    s7["7. Path"]
    s8["8. read_bytes"]
    s9["9. from_payload"]
    s10["10. _decode_json_object"]
    s11["11. isinstance"]
    s12["12. KnowledgeArtifactError"]
    s1 -. "isinstance(inputs, RuntimeKnowledgeInputs)" .-> s2
    s1 -. "TypeError('inputs must be a RuntimeKnowledgeInputs')" .-> s3
    s1 -. "replace(inputs, committed_state=capture_committed_knowledge(...))" .-> s4
    s1 -->|"capture_committed_knowledge(inputs.target_wiki_dir, inputs.previous_manifest)"| s5
    s5 -. "Path(wiki_dir).resolve(data not statically known)" .-> s6
    s5 -. "Path(wiki_dir)" .-> s7
    s5 -. "(root / name).read_bytes(data not statically known)" .-> s8
    s5 -. "SyncManifest.from_payload(_decode_json_object(...))" .-> s9
    s5 -->|"_decode_json_object(captured[...], 'manifest')"| s10
    s10 -. "isinstance(content, bytes)" .-> s11
    s10 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s12
    click s1 "../modules/knowledge_orchestration.md"
    click s5 "../modules/knowledge_orchestration.md"
    click s10 "../modules/knowledge_artifacts.md"
    click s12 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `finalize_runtime_knowledge` | `inputs: RuntimeKnowledgeInputs`, `dry_run: bool`, `fault_injector: FaultInjector \| None` | `RuntimeKnowledgeInputs`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME`, `GOVERNANCE_FILENAME` | - | `_commit_runtime_knowledge(...)`, `_commit_runtime_knowledge(...)`, `_commit_runtime_knowledge(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `replace` | - | - | - | - |
| `capture_committed_knowledge` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MANIFEST_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KnowledgeArtifactError`, `_COMMITTED_STATE_TOKEN` | `captured[...]`, `captured[...]` | `state` |
| `resolve` | - | - | - | - |
| `Path` | - | - | - | - |
| `read_bytes` | - | - | - | - |
| `from_payload` | - | - | - | - |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| finalize_runtime_knowledge | isinstance | 769 | `isinstance(inputs, RuntimeKnowledgeInputs)` |
| finalize_runtime_knowledge | TypeError | 770 | `TypeError('inputs must be a RuntimeKnowledgeInputs')` |
| finalize_runtime_knowledge | replace | 772 | `replace(inputs, committed_state=capture_committed_knowledge(...))` |
| finalize_runtime_knowledge | capture_committed_knowledge | 774 | `capture_committed_knowledge(inputs.target_wiki_dir, inputs.previous_manifest)` |
| capture_committed_knowledge | resolve | 226 | `Path(wiki_dir).resolve(data not statically known)` |
| capture_committed_knowledge | Path | 226 | `Path(wiki_dir)` |
| capture_committed_knowledge | read_bytes | 230 | `(root / name).read_bytes(data not statically known)` |
| capture_committed_knowledge | from_payload | 237 | `SyncManifest.from_payload(_decode_json_object(...))` |
| capture_committed_knowledge | _decode_json_object | 238 | `_decode_json_object(captured[...], 'manifest')` |
| _decode_json_object | isinstance | 574 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 575 | `KnowledgeArtifactError(field, 'must be bytes')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `finalize_runtime_knowledge` | `isinstance` | 769 |
| unresolved_call | `finalize_runtime_knowledge` | `TypeError` | 770 |
| external_call | `finalize_runtime_knowledge` | `replace` | 772 |
| unresolved_call | `capture_committed_knowledge` | `Path(wiki_dir).resolve` | 226 |
| unresolved_call | `capture_committed_knowledge` | `(root / name).read_bytes` | 230 |
| external_call | `capture_committed_knowledge` | `SyncManifest.from_payload` | 237 |
| unresolved_call | `_decode_json_object` | `isinstance` | 574 |
| step_limit | `finalize_runtime_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `finalize_runtime_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `finalize_runtime_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
