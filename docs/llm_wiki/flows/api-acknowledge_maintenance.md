# acknowledge_maintenance

**Entry point:** `acknowledge_maintenance` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [api](../modules/api.md), [bootstrap_recovery](../modules/bootstrap_recovery.md), [canonical_json](../modules/canonical_json.md), and 61 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [api](../modules/api.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [plugins](../modules/plugins.md)
- [python_calls](../modules/python_calls.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [storage_spool](../modules/storage_spool.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)
- [yaml_formats](../modules/yaml_formats.md)
- [yaml_syntax](../modules/yaml_syntax.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as acknowledge_maintenance
    participant p1 as _detached
    participant p2 as maintenance_core
    participant p3 as acknowledge_maintenance_authority
    participant p4 as _validate_wiki_dir
    participant p5 as _identity (src/llm_wiki_cli/services/maintenance_state.py)
    participant p6 as require
    participant p7 as _absolute_path
    participant p8 as _outside_recovery
    participant p9 as maintenance_write_operation
    participant p10 as _capture
    participant p11 as owner_key
    participant p12 as reconcile_pending_maintenance
    participant p13 as project_maintenance_knowledge
    participant p14 as rebind_maintenance_reuse
    participant p15 as validated_artifact_bytes
    participant p16 as build_knowledge_commit_plan
    participant p17 as commit_knowledge_artifacts
    participant p18 as capture_context_read
    participant p19 as canonical_hash
    participant p20 as validate_reuse_commitment
    participant p21 as guard_maintenance_owner
    participant p22 as current_manifest_format
    participant p23 as governance_writer_lock
    participant p24 as bind_reuse_commitment
    participant p25 as storage_writer_lock
    participant p26 as _capture_spooled_wiki
    participant p27 as _recovery_directory
    participant p28 as _commit_sharded
    participant p29 as type (src/llm_wiki_cli/api.py:acknowledge_maintenance)
    participant p30 as core.validate_schema (src/llm_wiki_cli/api.py:acknowledge_maintenance)
    p0->>p1: _detached
    p0->>p2: maintenance_core
    p0->>p3: acknowledge_maintenance_authority
    p0->>p4: _validate_wiki_dir
    p3->>p5: _identity (src/llm_wiki_cli/services/maintenance_state.py)
    p1->>p6: require
    p3->>p7: _absolute_path
    p3->>p8: _outside_recovery
    p3->>p9: maintenance_write_operation
    p3->>p10: _capture
    p3->>p11: owner_key
    p3->>p12: reconcile_pending_maintenance
    p3->>p13: project_maintenance_knowledge
    p3->>p14: rebind_maintenance_reuse
    p3->>p15: validated_artifact_bytes
    p3->>p16: build_knowledge_commit_plan
    p3->>p17: commit_knowledge_artifacts
    p10->>p18: capture_context_read
    p11->>p19: canonical_hash
    p14->>p20: validate_reuse_commitment
    p9->>p21: guard_maintenance_owner
    p16->>p22: current_manifest_format
    p9->>p23: governance_writer_lock
    p14->>p24: bind_reuse_commitment
    p9->>p25: storage_writer_lock
    p9->>p26: _capture_spooled_wiki
    p9->>p27: _recovery_directory
    p17->>p28: _commit_sharded
    p0-->>p29: type (src/llm_wiki_cli/api.py:acknowledge_maintenance)(allow_external_src)
    p0-->>p30: core.validate_schema (src/llm_wiki_cli/api.py:acknowledge_maintenance)('maintenance-event-v1', {...})
```

> Call sequence diagram shows 30 of 3027 interactions; 2997 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1023 (1022 omitted); unresolved 1 of 749 (748 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/api.py:acknowledge_maintenance` | 1 | - | external | 2 |
| `src/llm_wiki_cli/services/maintenance_state.py:_detached` | 4 | - | external | 3 |
| `src/llm_wiki_cli/services/maintenance_state.py:_detached` | 4 | [src/llm_wiki_cli/services/maintenance_shapes.py](../modules/maintenance_shapes.md) | internal | 1 |
| `src/llm_wiki_cli/services/maintenance_shapes.py:require` | 7 | [src/llm_wiki_cli/services/maintenance_shapes.py](../modules/maintenance_shapes.md) | internal | 1 |
| `src/llm_wiki_cli/services/maintenance_state.py:maintenance_core` | 11 | [src/llm_wiki_cli/services/maintenance_state.py](../modules/maintenance_state.md) | internal | 1 |
| `src/llm_wiki_cli/api.py:acknowledge_maintenance` | 1 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/maintenance_state.py:_identity` | 18 | - | external | 2 |
| `src/llm_wiki_cli/services/maintenance_state.py:_identity` | 18 | [src/llm_wiki_cli/services/maintenance_shapes.py](../modules/maintenance_shapes.md) | internal | 2 |
> Omission summary shows 8 of 728 groups; 720 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1256; effect analysis evaluated: 870, partial: 56, unavailable: 330. Counts include steps omitted from the displayed trace.

Collector observations for 926 source steps with known totals: observed: 5596, emitted: 5350, omitted: 246. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `acknowledge_maintenance` | `available` | `partial` | `available` | `13` | `10` | `3` |
| `type (src/llm_wiki_cli/api.py:acknowledge_maintenance)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_cli/api.py:acknowledge_maintenance)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_detached` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `deepcopy (src/llm_wiki_cli/services…enance_state.py:_detached)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `MaintenanceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `require` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `MaintenanceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `type (src/llm_wiki_cli/services…enance_state.py:_detached)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…enance_state.py:_detached)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `maintenance_core` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `MaintenanceCore` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. acknowledge_maintenance"]
    s2["2. type (src/llm_wiki_cli/api.py:acknowledge_maintenance)"]
    s3["3. ValueError (src/llm_wiki_cli/api.py:acknowledge_maintenance)"]
    s4["4. _detached"]
    s5["5. deepcopy (src/llm_wiki_cli/services…enance_state.py:_detached)"]
    s6["6. MaintenanceError"]
    s7["7. require"]
    s8["8. MaintenanceError"]
    s9["9. type (src/llm_wiki_cli/services…enance_state.py:_detached)"]
    s10["10. isinstance (src/llm_wiki_cli/services…enance_state.py:_detached)"]
    s11["11. maintenance_core"]
    s12["12. MaintenanceCore"]
    s1 -. "type (src/llm_wiki_cli/api.py:acknowledge_maintenance)(allow_external_src)" .-> s2
    s1 -. "ValueError (src/llm_wiki_cli/api.py:acknowledge_maintenance)('allow_external_src must be a boolean')" .-> s3
    s1 -->|"_detached(expected_basis)"| s4
    s4 -. "deepcopy (src/llm_wiki_cli/services…enance_state.py:_detached)(value)" .-> s5
    s4 -->|"MaintenanceError('schema-invalid', 'maintenance owner must contain strict JSON')"| s6
    s4 -->|"require(..., 'schema-invalid', 'maintenance owner must be an object')"| s7
    s7 -->|"MaintenanceError(code, message)"| s8
    s4 -. "type (src/llm_wiki_cli/services…enance_state.py:_detached)(result)" .-> s9
    s4 -. "isinstance (src/llm_wiki_cli/services…enance_state.py:_detached)(result, dict)" .-> s10
    s1 -->|"maintenance_core(data not statically known)"| s11
    s11 -->|"MaintenanceCore(validate_implementation_evidence)"| s12
    click s1 "../modules/api.md"
    click s4 "../modules/maintenance_state.md"
    click s6 "../modules/maintenance_shapes.md"
    click s7 "../modules/maintenance_shapes.md"
    click s8 "../modules/maintenance_shapes.md"
    click s11 "../modules/maintenance_state.md"
    click s12 "../modules/maintenance_state.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `acknowledge_maintenance` | `src_dir: str`, `wiki_dir: str`, `record_id: str`, `expected_state_hash: str`, `expected_basis: Mapping[str, Any]`, `actor_kind: Literal['agent', 'human']`, `actor_id: str`, `recovery_dir: str \| Path \| None` | `MaintenanceAcknowledgmentResult` | - | `cast(...)` |
| `type (src/llm_wiki_cli/api.py:acknowledge_maintenance)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/api.py:acknowledge_maintenance)` | - | - | - | - |
| `_detached` | `value: object` | - | - | `result` |
| `deepcopy (src/llm_wiki_cli/services…enance_state.py:_detached)` | - | - | - | - |
| `MaintenanceError` | - | - | - | - |
| `require` | `condition`, `code`, `message` | - | - | - |
| `MaintenanceError` | - | - | - | - |
| `type (src/llm_wiki_cli/services…enance_state.py:_detached)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…enance_state.py:_detached)` | - | - | - | - |
| `maintenance_core` | - | `_CORE`, `_CORE` | `_CORE` | `_CORE` |
| `MaintenanceCore` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| acknowledge_maintenance | type (src/llm_wiki_cli/api.py:acknowledge_maintenance) | 1741 | `type(allow_external_src)` |
| acknowledge_maintenance | ValueError (src/llm_wiki_cli/api.py:acknowledge_maintenance) | 1742 | `ValueError('allow_external_src must be a boolean')` |
| acknowledge_maintenance | _detached | 1743 | `_detached(expected_basis)` |
| _detached | deepcopy (src/llm_wiki_cli/services…enance_state.py:_detached) | 964 | `deepcopy(value)` |
| _detached | MaintenanceError | 966 | `MaintenanceError('schema-invalid', 'maintenance owner must contain strict JSON')` |
| _detached | require | 969 | `require(..., 'schema-invalid', 'maintenance owner must be an object')` |
| require | MaintenanceError | 27 | `MaintenanceError(code, message)` |
| _detached | type (src/llm_wiki_cli/services…enance_state.py:_detached) | 970 | `type(result)` |
| _detached | isinstance (src/llm_wiki_cli/services…enance_state.py:_detached) | 972 | `isinstance(result, dict)` |
| acknowledge_maintenance | maintenance_core | 1744 | `maintenance_core(data not statically known)` |
| maintenance_core | MaintenanceCore | 958 | `MaintenanceCore(validate_implementation_evidence)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `acknowledge_maintenance` | `type` | 1741 |
| external_call | `acknowledge_maintenance` | `ValueError` | 1742 |
| external_call | `_detached` | `deepcopy` | 964 |
| external_call | `_detached` | `type` | 970 |
| external_call | `_detached` | `isinstance` | 972 |
| step_limit | `acknowledge_maintenance` | `first 12 steps` | 0 |
| truncated_flow | `acknowledge_maintenance` | `depth limit` | 0 |

## Behavior

This flow starts at `acknowledge_maintenance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
