# validate_knowledge_artifacts

**Entry point:** `validate_knowledge_artifacts` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [filesystem_guard](../modules/filesystem_guard.md), and 27 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [progress](../modules/progress.md)
- [section_ownership](../modules/section_ownership.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_knowledge_artifacts
    participant p1 as validate_surface_index_bytes
    participant p2 as _require_validation_receipt
    participant p3 as freeze
    participant p4 as StorageReadSession.read
    participant p5 as SyncManifest.from_payload
    participant p6 as StorageReadSession.recheck
    participant p7 as open_knowledge_store
    participant p8 as _validated_index_serialization
    participant p9 as _validate_surface_knowledge_parity
    participant p10 as _validate_manifest_knowledge_parity
    participant p11 as validate_reuse_artifact_parity
    participant p12 as governance_hash_from_knowledge
    participant p13 as KnowledgeArtifactError
    participant p14 as _model_to_payload
    participant p15 as _decode_json_object
    participant p16 as StorageReadSession
    participant p17 as KnowledgeStorageError
    participant p18 as physical_objects
    participant p19 as _is_future_schema_version
    participant p20 as logical_digest
    participant p21 as validate_knowledge_index
    participant p22 as sha256_bytes
    participant p23 as typed_graph_from_knowledge_extensions
    participant p24 as validate_section_ownership
    participant p25 as ValidatedKnowledgeArtifacts
    participant p26 as EvaluatedEnvelope
    participant p27 as _ArtifactValidation
    participant p28 as _require_relative_name
    participant p29 as Path (src/llm_wiki_cli/services…idate_knowledge_artifacts)
    participant p30 as Path(…).resolve
    p0->>p1: validate_surface_index_bytes
    p0->>p2: _require_validation_receipt
    p0->>p3: freeze
    p0->>p4: StorageReadSession.read
    p0->>p5: SyncManifest.from_payload
    p0->>p6: StorageReadSession.recheck
    p0->>p7: open_knowledge_store
    p0->>p8: _validated_index_serialization
    p0->>p9: _validate_surface_knowledge_parity
    p0->>p10: _validate_manifest_knowledge_parity
    p0->>p11: validate_reuse_artifact_parity
    p0->>p12: governance_hash_from_knowledge
    p0->>p13: KnowledgeArtifactError
    p0->>p14: _model_to_payload
    p0->>p15: _decode_json_object
    p0->>p16: StorageReadSession
    p0->>p17: KnowledgeStorageError
    p0->>p18: physical_objects
    p0->>p19: _is_future_schema_version
    p0->>p20: logical_digest
    p0->>p21: validate_knowledge_index
    p0->>p22: sha256_bytes
    p0->>p23: typed_graph_from_knowledge_extensions
    p0->>p24: validate_section_ownership
    p0->>p25: ValidatedKnowledgeArtifacts
    p0->>p26: EvaluatedEnvelope
    p0->>p27: _ArtifactValidation
    p4->>p28: _require_relative_name
    p0-->>p29: Path (src/llm_wiki_cli/services…idate_knowledge_artifacts)(wiki_dir)
    p0-->>p30: Path(…).resolve
```

> Call sequence diagram shows 30 of 2253 interactions; 2223 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 632 (631 omitted); unresolved 1 of 376 (375 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:validate_surface_index_bytes` | 2 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_decode_json_object` | 3 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_decode_json_object` | 3 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 6 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_decode_json_object` | 3 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_unique_json_object` | 9 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_reject_json_constant` | 11 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_validate_surface_payload` | 17 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 8 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_validate_utf8_json` | 18 | - | external | 5 |
> Omission summary shows 8 of 510 groups; 502 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1246; effect analysis evaluated: 650, partial: 27, unavailable: 569. Counts include steps omitted from the displayed trace.

Collector observations for 677 source steps with known totals: observed: 3402, emitted: 3228, omitted: 174. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_knowledge_artifacts` | `available` | `partial` | `available` | `34` | `17` | `17` |
| `validate_surface_index_bytes` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_decode_json_object` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeArtifactError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `content.decode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeArtifactError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_unique_json_object` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `KnowledgeArtifactError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_reject_json_constant` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `KnowledgeArtifactError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. validate_knowledge_artifacts"]
    s2["2. validate_surface_index_bytes"]
    s3["3. _decode_json_object"]
    s4["4. isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)"]
    s5["5. KnowledgeArtifactError"]
    s6["6. content.decode"]
    s7["7. KnowledgeArtifactError"]
    s8["8. json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)"]
    s9["9. _unique_json_object"]
    s10["10. KnowledgeArtifactError"]
    s11["11. _reject_json_constant"]
    s12["12. KnowledgeArtifactError"]
    s1 -->|"validate_surface_index_bytes(surface_index_bytes)"| s2
    s2 -->|"_decode_json_object(surface_index_bytes, 'surface_index_bytes')"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)(content, bytes)" .-> s4
    s3 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s5
    s3 -. "content.decode('utf-8')" .-> s6
    s3 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s7
    s3 -. "json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)(text, object_pairs_hook=..., parse_constant=...)" .-> s8
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
| `validate_knowledge_artifacts` | `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes`, `manifest: SyncManifest`, `object_reader: Callable[[str, int], bytes] \| None`, `wiki_dir: str \| Path \| None`, `_validation_receipt: object \| None`, `_receipt_wiki_root: Path \| None`, `_storage_validation_receipt: object \| None` | `STORE_SCHEMA`, `PACKED_SCHEMAS`, `STORE_SCHEMA`, `PACKED_SCHEMAS`, `KNOWLEDGE_INDEX_FILENAME`, `SURFACE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MAX_EXPANDED_BYTES` | - | `validated` |
| `validate_surface_index_bytes` | `surface_index_bytes: bytes` | - | - | `surface_payload` |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `content.decode` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | - | - | - | - |
| `_unique_json_object` | `pairs: list[tuple[str, Any]]`, `field: str` | - | `result[...]` | `result` |
| `KnowledgeArtifactError` | - | - | - | - |
| `_reject_json_constant` | `value: str`, `field: str` | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_artifacts | validate_surface_index_bytes | 300 | `validate_surface_index_bytes(surface_index_bytes)` |
| validate_surface_index_bytes | _decode_json_object | 263 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 930 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 931 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | content.decode | 933 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 935 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 937 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 939 | `_unique_json_object(pairs, field)` |
| _unique_json_object | KnowledgeArtifactError | 958 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | _reject_json_constant | 940 | `_reject_json_constant(value, field)` |
| _reject_json_constant | KnowledgeArtifactError | 964 | `KnowledgeArtifactError(field, ...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_decode_json_object` | `isinstance` | 930 |
| unresolved_call | `_decode_json_object` | `content.decode` | 933 |
| external_call | `_decode_json_object` | `json.loads` | 937 |
| step_limit | `validate_knowledge_artifacts` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_artifacts` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_artifacts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
