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
    participant p1 as _validator_identity
    participant p2 as _storage_validator_identity
    participant p3 as validate_surface_index_bytes
    participant p4 as _require_validation_receipt
    participant p5 as freeze
    participant p6 as StorageReadSession.read
    participant p7 as SyncManifest.from_payload
    participant p8 as StorageReadSession.recheck
    participant p9 as open_knowledge_store
    participant p10 as _validated_index_data
    participant p11 as _validate_artifact_parity
    participant p12 as KnowledgeArtifactError
    participant p13 as _model_to_payload
    participant p14 as _decode_json_object
    participant p15 as StorageReadSession
    participant p16 as KnowledgeStorageError
    participant p17 as physical_objects
    participant p18 as _is_future_schema_version
    participant p19 as logical_digest
    participant p20 as validate_knowledge_index
    participant p21 as maintenance_core
    participant p22 as _require_relative_name
    participant p23 as _mapping_value
    participant p24 as StorageReadSession.phase
    participant p25 as _validate_surface_payload
    participant p26 as _validation_module_identity
    participant p27 as _surface_page_index
    participant p28 as StorageReadSession.read_ranges
    participant p29 as Path (src/llm_wiki_cli/services…idate_knowledge_artifacts)
    participant p30 as Path(…).resolve
    p0->>p1: _validator_identity
    p0->>p2: _storage_validator_identity
    p0->>p3: validate_surface_index_bytes
    p0->>p4: _require_validation_receipt
    p0->>p5: freeze
    p0->>p6: StorageReadSession.read
    p0->>p7: SyncManifest.from_payload
    p0->>p8: StorageReadSession.recheck
    p0->>p9: open_knowledge_store
    p0->>p10: _validated_index_data
    p0->>p11: _validate_artifact_parity
    p0->>p12: KnowledgeArtifactError
    p0->>p13: _model_to_payload
    p0->>p14: _decode_json_object
    p0->>p15: StorageReadSession
    p0->>p16: KnowledgeStorageError
    p0->>p17: physical_objects
    p0->>p18: _is_future_schema_version
    p0->>p19: logical_digest
    p0->>p20: validate_knowledge_index
    p1->>p21: maintenance_core
    p6->>p22: _require_relative_name
    p7->>p23: _mapping_value
    p8->>p24: StorageReadSession.phase
    p3->>p25: _validate_surface_payload
    p1->>p26: _validation_module_identity
    p3->>p27: _surface_page_index
    p8->>p28: StorageReadSession.read_ranges
    p0-->>p29: Path (src/llm_wiki_cli/services…idate_knowledge_artifacts)(wiki_dir)
    p0-->>p30: Path(…).resolve
```

> Call sequence diagram shows 30 of 2282 interactions; 2252 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 660 (659 omitted); unresolved 1 of 377 (376 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/maintenance_state.py:maintenance_core` | 3 | [src/llm_wiki_cli/services/maintenance_state.py](../modules/maintenance_state.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validator_identity` | 2 | - | external | 6 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validation_module_identity` | 6 | - | external | 22 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validation_module_identity` | 6 | - | unresolved | 10 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validation_module_identity` | 6 | [src/llm_wiki_cli/services/knowledge_index.py](../modules/knowledge_index.md) | internal | 5 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validation_callable_identity` | 15 | - | external | 10 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validation_callable_identity` | 15 | [src/llm_wiki_cli/services/knowledge_index.py](../modules/knowledge_index.md) | internal | 7 |
| `src/llm_wiki_cli/services/knowledge_index.py:_validation_policy_value` | 24 | - | external | 31 |
> Omission summary shows 8 of 527 groups; 519 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1246; effect analysis evaluated: 701, partial: 42, unavailable: 503. Counts include steps omitted from the displayed trace.

Collector observations for 743 source steps with known totals: observed: 3900, emitted: 3709, omitted: 191. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_knowledge_artifacts` | `available` | `partial` | `available` | `26` | `17` | `9` |
| `_validator_identity` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `maintenance_core` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `MaintenanceCore` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…ex.py:_validator_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_module_identity` | `available` | `evaluated` | `available` | `11` | `11` | `0` |
| `sorted (src/llm_wiki_cli/services…alidation_module_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `vars(…).items (src/llm_wiki_cli/services…alidation_module_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `vars` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `inspect.isfunction (src/llm_wiki_cli/services…alidation_module_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…alidation_module_identity)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `callable` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. validate_knowledge_artifacts"]
    s2["2. _validator_identity"]
    s3["3. maintenance_core"]
    s4["4. MaintenanceCore"]
    s5["5. tuple (src/llm_wiki_cli/services…ex.py:_validator_identity)"]
    s6["6. _validation_module_identity"]
    s7["7. sorted (src/llm_wiki_cli/services…alidation_module_identity)"]
    s8["8. vars(…).items (src/llm_wiki_cli/services…alidation_module_identity)"]
    s9["9. vars"]
    s10["10. inspect.isfunction (src/llm_wiki_cli/services…alidation_module_identity)"]
    s11["11. isinstance (src/llm_wiki_cli/services…alidation_module_identity)"]
    s12["12. callable"]
    s1 -->|"_validator_identity(data not statically known)"| s2
    s2 -->|"maintenance_core(data not statically known)"| s3
    s3 -->|"MaintenanceCore(validate_implementation_evidence)"| s4
    s2 -. "tuple (src/llm_wiki_cli/services…ex.py:_validator_identity)(...)" .-> s5
    s2 -->|"_validation_module_identity(module)"| s6
    s6 -. "sorted (src/llm_wiki_cli/services…alidation_module_identity)(...)" .-> s7
    s6 -. "vars(…).items (src/llm_wiki_cli/services…alidation_module_identity)(data not statically known)" .-> s8
    s6 -. "vars(module)" .-> s9
    s6 -. "inspect.isfunction (src/llm_wiki_cli/services…alidation_module_identity)(value)" .-> s10
    s6 -. "isinstance (src/llm_wiki_cli/services…alidation_module_identity)(value, partial)" .-> s11
    s6 -. "callable(value)" .-> s12
    b0["mutation functions.append"]
    s6 -. "mutation functions.append" .-> b0
    b1["mutation methods.append"]
    s6 -. "mutation methods.append" .-> b1
    b2["mutation methods.append"]
    s6 -. "mutation methods.append" .-> b2
    b3["mutation methods.append"]
    s6 -. "mutation methods.append" .-> b3
    b4["mutation classes.append"]
    s6 -. "mutation classes.append" .-> b4
    b5["mutation policy.append"]
    s6 -. "mutation policy.append" .-> b5
    click s1 "../modules/knowledge_artifacts.md"
    click s2 "../modules/knowledge_index.md"
    click s3 "../modules/maintenance_state.md"
    click s4 "../modules/maintenance_state.md"
    click s6 "../modules/knowledge_index.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_knowledge_artifacts` | `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes`, `manifest: SyncManifest`, `object_reader: Callable[[str, int], bytes] \| None`, `wiki_dir: str \| Path \| None`, `_validation_receipt: object \| None`, `_receipt_wiki_root: Path \| None`, `_storage_validation_receipt: object \| None` | `STORE_SCHEMA`, `PACKED_SCHEMAS`, `STORE_SCHEMA`, `PACKED_SCHEMAS`, `KNOWLEDGE_INDEX_FILENAME`, `SURFACE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MAX_EXPANDED_BYTES` | - | `_validate_artifact_parity(...)` |
| `_validator_identity` | - | `KNOWLEDGE_SCHEMA_VERSION` | - | `(...)` |
| `maintenance_core` | - | `_CORE`, `_CORE` | `_CORE` | `_CORE` |
| `MaintenanceCore` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…ex.py:_validator_identity)` | - | - | - | - |
| `_validation_module_identity` | `module` | `partial`, `partial`, `Enum` | - | `(...)` |
| `sorted (src/llm_wiki_cli/services…alidation_module_identity)` | - | - | - | - |
| `vars(…).items (src/llm_wiki_cli/services…alidation_module_identity)` | - | - | - | - |
| `vars` | - | - | - | - |
| `inspect.isfunction (src/llm_wiki_cli/services…alidation_module_identity)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…alidation_module_identity)` | - | - | - | - |
| `callable` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_artifacts | _validator_identity | 316 | `_validator_identity(data not statically known)` |
| _validator_identity | maintenance_core | 387 | `maintenance_state.maintenance_core(data not statically known)` |
| maintenance_core | MaintenanceCore | 958 | `MaintenanceCore(validate_implementation_evidence)` |
| _validator_identity | tuple (src/llm_wiki_cli/services…ex.py:_validator_identity) | 390 | `tuple(...)` |
| _validator_identity | _validation_module_identity | 390 | `_validation_module_identity(module)` |
| _validation_module_identity | sorted (src/llm_wiki_cli/services…alidation_module_identity) | 448 | `sorted(...)` |
| _validation_module_identity | vars(…).items (src/llm_wiki_cli/services…alidation_module_identity) | 448 | `vars(module).items(data not statically known)` |
| _validation_module_identity | vars | 448 | `vars(module)` |
| _validation_module_identity | inspect.isfunction (src/llm_wiki_cli/services…alidation_module_identity) | 449 | `inspect.isfunction(value)` |
| _validation_module_identity | isinstance (src/llm_wiki_cli/services…alidation_module_identity) | 449 | `isinstance(value, partial)` |
| _validation_module_identity | callable | 450 | `callable(value)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `functions.append` | `_validation_module_identity` | 451 |
| mutation | `methods.append` | `_validation_module_identity` | 459 |
| mutation | `methods.append` | `_validation_module_identity` | 461 |
| mutation | `methods.append` | `_validation_module_identity` | 464 |
| mutation | `classes.append` | `_validation_module_identity` | 466 |
| mutation | `policy.append` | `_validation_module_identity` | 468 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_validation_module_identity` | `sorted` | 448 |
| unresolved_call | `_validation_module_identity` | `vars(module).items` | 448 |
| external_call | `_validation_module_identity` | `vars` | 448 |
| external_call | `_validation_module_identity` | `inspect.isfunction` | 449 |
| external_call | `_validation_module_identity` | `isinstance` | 449 |
| external_call | `_validation_module_identity` | `callable` | 450 |
| step_limit | `validate_knowledge_artifacts` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_artifacts` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_artifacts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
