# evaluate_documentation_native_freshness

**Entry point:** `evaluate_documentation_native_freshness` (`api`)
**Source:** [documentation_native](../modules/documentation_native.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 46 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [documentation_native](../modules/documentation_native.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [go_calls](../modules/go_calls.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [markdown_sections](../modules/markdown_sections.md)
- [normalization_diagnostics](../modules/normalization_diagnostics.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_contracts](../modules/python_contracts.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [python_observations](../modules/python_observations.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [section_ownership](../modules/section_ownership.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [yaml_formats](../modules/yaml_formats.md)
- [yaml_syntax](../modules/yaml_syntax.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as evaluate_documentation_native_freshness
    participant p1 as _native_source_snapshot_preflight
    participant p2 as _generation_input_paths
    participant p3 as _collect_runtime
    participant p4 as _retained_empty_paths
    participant p5 as _runtime_generation_options
    participant p6 as _source_mismatches
    participant p7 as build_runtime_live_evaluation
    participant p8 as evaluate_knowledge_freshness
    participant p9 as RuntimeLiveEvaluationInputs
    participant p10 as DocumentationNativeError
    participant p11 as DocumentationNativeFreshness
    participant p12 as _validated_directory
    participant p13 as retained_empty_module_paths
    participant p14 as runtime_generation_options
    participant p15 as resolve_source_selection
    participant p16 as capture_source_selection_inputs
    participant p17 as source_selection_identity_from_generation_inputs
    participant p18 as parse_knowledge_index
    participant p19 as validate_persisted_source_selection_identity
    participant p20 as _knowledge_index_to_payload_unchecked
    participant p21 as build_source_snapshot
    participant p22 as get_inventory_result
    participant p23 as _evaluate_model_freshness
    participant p24 as has_contract
    participant p25 as get_docker_inventory
    participant p26 as get_yaml_infrastructure_inventory
    participant p27 as _live_source_snapshot_hash
    participant p28 as _producer_evidence
    participant p29 as isinstance (src/llm_wiki_cli/services…entation_native_freshness)
    participant p30 as (…).lstat
    p0->>p1: _native_source_snapshot_preflight
    p0->>p2: _generation_input_paths
    p0->>p3: _collect_runtime
    p0->>p4: _retained_empty_paths
    p0->>p5: _runtime_generation_options
    p0->>p6: _source_mismatches
    p0->>p7: build_runtime_live_evaluation
    p0->>p8: evaluate_knowledge_freshness
    p0->>p9: RuntimeLiveEvaluationInputs
    p0->>p10: DocumentationNativeError
    p0->>p11: DocumentationNativeFreshness
    p1->>p12: _validated_directory
    p4->>p13: retained_empty_module_paths
    p5->>p14: runtime_generation_options
    p1->>p15: resolve_source_selection
    p1->>p16: capture_source_selection_inputs
    p1->>p17: source_selection_identity_from_generation_inputs
    p8->>p18: parse_knowledge_index
    p1->>p19: validate_persisted_source_selection_identity
    p8->>p20: _knowledge_index_to_payload_unchecked
    p1->>p21: build_source_snapshot
    p3->>p22: get_inventory_result
    p8->>p23: _evaluate_model_freshness
    p7->>p24: has_contract
    p3->>p25: get_docker_inventory
    p3->>p26: get_yaml_infrastructure_inventory
    p6->>p27: _live_source_snapshot_hash
    p7->>p28: _producer_evidence
    p0-->>p29: isinstance (src/llm_wiki_cli/services…entation_native_freshness)(knowledge, KnowledgeIndex)
    p0-->>p30: (…).lstat
```

> Call sequence diagram shows 30 of 3543 interactions; 3513 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 989 (988 omitted); unresolved 1 of 895 (894 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_native.py:evaluate_documentation_native_freshness` | 1 | - | external | 9 |
| `src/llm_wiki_cli/services/documentation_native.py:_validated_directory` | 7 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/documentation_native.py:_validated_directory` | 7 | - | external | 3 |
| `src/llm_wiki_cli/services/documentation_native.py:_validated_directory` | 7 | [src/llm_wiki_cli/services/documentation_native.py](../modules/documentation_native.md) | internal | 2 |
| `src/llm_wiki_cli/services/source_selection.py:resolve_source_selection` | 16 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/source_selection.py:resolve_source_selection` | 16 | - | external | 1 |
| `src/llm_wiki_cli/services/source_selection.py:resolve_source_selection` | 16 | [src/llm_wiki_cli/services/source_selection.py](../modules/source_selection.md) | internal | 8 |
| `src/llm_wiki_cli/services/source_selection.py:_override_text` | 20 | - | external | 3 |
> Omission summary shows 8 of 924 groups; 916 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_documentation_native_freshness"]
    s2["2. isinstance (src/llm_wiki_cli/services…entation_native_freshness)"]
    s3["3. TypeError (src/llm_wiki_cli/services…entation_native_freshness)"]
    s4["4. isinstance (src/llm_wiki_cli/services…entation_native_freshness)"]
    s5["5. TypeError (src/llm_wiki_cli/services…entation_native_freshness)"]
    s6["6. _native_source_snapshot_preflight"]
    s7["7. _validated_directory"]
    s8["8. Path(…).expanduser"]
    s9["9. Path (src/llm_wiki_cli/services…e.py:_validated_directory)"]
    s10["10. candidate.lstat"]
    s11["11. DocumentationNativeError"]
    s12["12. stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…entation_native_freshness)(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…entation_native_freshness)('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…entation_native_freshness)(manifest, SyncManifest)" .-> s4
    s1 -. "TypeError (src/llm_wiki_cli/services…entation_native_freshness)('manifest must be a SyncManifest')" .-> s5
    s1 -->|"_native_source_snapshot_preflight(source_root=source_root, manifest=manifest, source_selection=source_selection, operation='native freshness')"| s6
    s6 -->|"_validated_directory(source_root, 'source_root')"| s7
    s7 -. "Path(…).expanduser(data not statically known)" .-> s8
    s7 -. "Path (src/llm_wiki_cli/services…e.py:_validated_directory)(value)" .-> s9
    s7 -. "candidate.lstat(data not statically known)" .-> s10
    s7 -->|"DocumentationNativeError(...)"| s11
    s7 -. "stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)(metadata.st_mode)" .-> s12
    b0["mutation missing_source_paths.add"]
    s1 -. "mutation missing_source_paths.add" .-> b0
    b1["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b1
    b2["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b2
    b3["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b3
    click s1 "../modules/documentation_native.md"
    click s6 "../modules/documentation_native.md"
    click s7 "../modules/documentation_native.md"
    click s11 "../modules/documentation_native.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `evaluate_documentation_native_freshness` | `knowledge: KnowledgeIndex`, `manifest: SyncManifest`, `source_root: str \| Path`, `trust_source_plugins: bool`, `helper_cache_dir: str \| Path \| None`, `source_selection: str \| Path \| None` | `KnowledgeIndex`, `SyncManifest`, `ObservationScope`, `RUNTIME_GENERATION_OPTION_DEFAULTS`, `RUNTIME_GENERATION_OPTION_DEFAULTS`, `PageKind`, `ComputedFreshness` | - | `DocumentationNativeFreshness(...)` |
| `isinstance (src/llm_wiki_cli/services…entation_native_freshness)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…entation_native_freshness)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…entation_native_freshness)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…entation_native_freshness)` | - | - | - | - |
| `_native_source_snapshot_preflight` | `source_root: str \| Path`, `manifest: SyncManifest`, `source_selection: str \| Path \| None`, `operation: str`, `allow_same_path_identity_update: bool` | `SourceSelectionError`, `SourceSnapshotError` | - | `(...)` |
| `_validated_directory` | `value: str \| Path`, `field_name: str` | - | - | `candidate.resolve(...)` |
| `Path(…).expanduser` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…e.py:_validated_directory)` | - | - | - | - |
| `candidate.lstat` | - | - | - | - |
| `DocumentationNativeError` | - | - | - | - |
| `stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| evaluate_documentation_native_freshness | isinstance (src/llm_wiki_cli/services…entation_native_freshness) | 203 | `isinstance(knowledge, KnowledgeIndex)` |
| evaluate_documentation_native_freshness | TypeError (src/llm_wiki_cli/services…entation_native_freshness) | 204 | `TypeError('knowledge must be a KnowledgeIndex')` |
| evaluate_documentation_native_freshness | isinstance (src/llm_wiki_cli/services…entation_native_freshness) | 205 | `isinstance(manifest, SyncManifest)` |
| evaluate_documentation_native_freshness | TypeError (src/llm_wiki_cli/services…entation_native_freshness) | 206 | `TypeError('manifest must be a SyncManifest')` |
| evaluate_documentation_native_freshness | _native_source_snapshot_preflight | 207 | `_native_source_snapshot_preflight(source_root=source_root, manifest=manifest, source_selection=source_selection, operation='native freshness')` |
| _native_source_snapshot_preflight | _validated_directory | 156 | `_validated_directory(source_root, 'source_root')` |
| _validated_directory | Path(…).expanduser | 1123 | `Path(value).expanduser(data not statically known)` |
| _validated_directory | Path (src/llm_wiki_cli/services…e.py:_validated_directory) | 1123 | `Path(value)` |
| _validated_directory | candidate.lstat | 1125 | `candidate.lstat(data not statically known)` |
| _validated_directory | DocumentationNativeError | 1127 | `DocumentationNativeError(...)` |
| _validated_directory | stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory) | 1130 | `stat.S_ISLNK(metadata.st_mode)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `missing_source_paths.add` | `evaluate_documentation_native_freshness` | 244 |
| mutation | `reasons.append` | `evaluate_documentation_native_freshness` | 285 |
| mutation | `reasons.append` | `evaluate_documentation_native_freshness` | 287 |
| mutation | `reasons.append` | `evaluate_documentation_native_freshness` | 297 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `evaluate_documentation_native_freshness` | `isinstance` | 203 |
| external_call | `evaluate_documentation_native_freshness` | `TypeError` | 204 |
| external_call | `evaluate_documentation_native_freshness` | `isinstance` | 205 |
| external_call | `evaluate_documentation_native_freshness` | `TypeError` | 206 |
| unresolved_call | `_validated_directory` | `Path(value).expanduser` | 1123 |
| unresolved_call | `_validated_directory` | `candidate.lstat` | 1125 |
| external_call | `_validated_directory` | `stat.S_ISLNK` | 1130 |
| step_limit | `evaluate_documentation_native_freshness` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_documentation_native_freshness` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_documentation_native_freshness` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
