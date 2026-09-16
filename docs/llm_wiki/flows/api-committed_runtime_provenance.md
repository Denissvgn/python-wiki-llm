# committed_runtime_provenance

**Entry point:** `committed_runtime_provenance` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [immutable](../modules/immutable.md), [infrastructure_sync](../modules/infrastructure_sync.md), and 18 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
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
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as committed_runtime_provenance
    participant p1 as _previous_committed_artifacts
    participant p2 as capture_committed_knowledge
    participant p3 as Path(…).resolve
    participant p4 as Path (src/llm_wiki_cli/services…pture_committed_knowledge)
    participant p5 as (…).read_bytes
    participant p6 as SyncManifest.from_payload
    participant p7 as _mapping_value
    participant p8 as require_mapping
    participant p9 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p10 as key.encode
    participant p11 as SyncManifestError
    participant p12 as data.get (src/llm_wiki_cli/services…SyncManifest.from_payload)
    participant p13 as type (src/llm_wiki_cli/services…SyncManifest.from_payload)
    participant p14 as ManifestStoreReader
    participant p15 as reader.materialize
    participant p16 as isinstance (src/llm_wiki_cli/services…SyncManifest.from_payload)
    participant p17 as _copy_sources
    participant p18 as data.items
    participant p19 as isinstance (src/llm_wiki_cli/services…manifest.py:_copy_sources)
    participant p20 as deepcopy (src/llm_wiki_cli/services…manifest.py:_copy_sources)
    p0->>p1: _previous_committed_artifacts
    p1->>p2: capture_committed_knowledge
    p2-->>p3: Path(…).resolve
    p2-->>p4: Path (src/llm_wiki_cli/services…pture_committed_knowledge)
    p2-->>p5: (…).read_bytes
    p2->>p6: SyncManifest.from_payload
    p6->>p7: _mapping_value
    p7->>p8: require_mapping
    p8-->>p9: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p8-->>p9: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p8-->>p10: key.encode
    p7->>p11: SyncManifestError
    p7->>p11: SyncManifestError
    p6-->>p12: data.get (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p6-->>p13: type (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p6->>p11: SyncManifestError
    p6->>p14: ManifestStoreReader
    p6->>p6: SyncManifest.from_payload
    p6-->>p15: reader.materialize
    p6-->>p16: isinstance (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p6-->>p16: isinstance (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p6->>p11: SyncManifestError
    p6->>p11: SyncManifestError
    p6->>p11: SyncManifestError
    p6->>p17: _copy_sources
    p17->>p7: _mapping_value
    p17-->>p18: data.items
    p17-->>p19: isinstance (src/llm_wiki_cli/services…manifest.py:_copy_sources)
    p17->>p11: SyncManifestError
    p17-->>p20: deepcopy (src/llm_wiki_cli/services…manifest.py:_copy_sources)
```

> Call sequence diagram shows 30 of 729 interactions; 699 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. committed_runtime_provenance"]
    s2["2. _previous_committed_artifacts"]
    s3["3. capture_committed_knowledge"]
    s4["4. Path(…).resolve"]
    s5["5. Path (src/llm_wiki_cli/services…pture_committed_knowledge)"]
    s6["6. (…).read_bytes"]
    s7["7. SyncManifest.from_payload"]
    s8["8. _mapping_value"]
    s9["9. require_mapping"]
    s10["10. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s11["11. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s12["12. key.encode"]
    s1 -->|"_previous_committed_artifacts(wiki_dir, manifest, committed_state=committed_state)"| s2
    s2 -->|"capture_committed_knowledge(wiki_dir, manifest)"| s3
    s3 -. "Path(…).resolve(data not statically known)" .-> s4
    s3 -. "Path (src/llm_wiki_cli/services…pture_committed_knowledge)(wiki_dir)" .-> s5
    s3 -. "(…).read_bytes(data not statically known)" .-> s6
    s3 -->|"SyncManifest.from_payload(_decode_json_object(...), object_reader=...)"| s7
    s7 -->|"_mapping_value(value, 'manifest')"| s8
    s8 -->|"require_mapping(value, error=SyncManifestError(...), require_string_keys=True, key_error=SyncManifestError(...))"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s10
    s9 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s11
    s9 -. "key.encode('utf-8')" .-> s12
    b0["mutation captured.update"]
    s3 -. "mutation captured.update" .-> b0
    click s1 "../modules/knowledge_orchestration.md"
    click s2 "../modules/knowledge_orchestration.md"
    click s3 "../modules/knowledge_orchestration.md"
    click s7 "../modules/sync_manifest.md"
    click s8 "../modules/sync_manifest.md"
    click s9 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `committed_runtime_provenance` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None`, `committed_state: CommittedKnowledgeState \| None` | - | - | `None`, `CommittedRuntimeProvenance(...)` |
| `_previous_committed_artifacts` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None`, `committed_state: CommittedKnowledgeState \| None` | - | - | `state.artifacts` |
| `capture_committed_knowledge` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MANIFEST_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KnowledgeArtifactError`, `_COMMITTED_STATE_TOKEN` | `captured[...]`, `captured[...]` | `state` |
| `Path(…).resolve` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…pture_committed_knowledge)` | - | - | - | - |
| `(…).read_bytes` | - | - | - | - |
| `SyncManifest.from_payload` | `value: object`, `object_reader` | `MANIFEST_VERSION`, `LEGACY_MANIFEST_VERSION`, `Mapping`, `LEGACY_MANIFEST_VERSION`, `Mapping`, `LEGACY_MANIFEST_VERSION`, `Mapping`, `Mapping` | `manifest.storage_version`, `manifest.storage_objects`, `legacy_surfaces[...]`, `surfaces[...]` | `manifest`, `manifest`, `manifest` |
| `_mapping_value` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| committed_runtime_provenance | _previous_committed_artifacts | 726 | `_previous_committed_artifacts(wiki_dir, manifest, committed_state=committed_state)` |
| _previous_committed_artifacts | capture_committed_knowledge | 697 | `capture_committed_knowledge(wiki_dir, manifest)` |
| capture_committed_knowledge | Path(…).resolve | 228 | `Path(wiki_dir).resolve(data not statically known)` |
| capture_committed_knowledge | Path (src/llm_wiki_cli/services…pture_committed_knowledge) | 228 | `Path(wiki_dir)` |
| capture_committed_knowledge | (…).read_bytes | 232 | `(root / name).read_bytes(data not statically known)` |
| capture_committed_knowledge | SyncManifest.from_payload | 239 | `SyncManifest.from_payload(_decode_json_object(...), object_reader=...)` |
| SyncManifest.from_payload | _mapping_value | 992 | `_mapping_value(value, 'manifest')` |
| _mapping_value | require_mapping | 139 | `require_mapping(value, error=SyncManifestError(...), require_string_keys=True, key_error=SyncManifestError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `captured.update` | `capture_committed_knowledge` | 254 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_committed_knowledge` | `Path(wiki_dir).resolve` | 228 |
| unresolved_call | `capture_committed_knowledge` | `(root / name).read_bytes` | 232 |
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `committed_runtime_provenance` | `first 12 steps` | 0 |
| truncated_flow | `committed_runtime_provenance` | `depth limit` | 0 |

## Behavior

This flow starts at `committed_runtime_provenance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
