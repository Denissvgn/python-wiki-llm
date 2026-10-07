# build_knowledge_generation_plan

**Entry point:** `build_knowledge_generation_plan` (`api`)
**Source:** [knowledge_generation](../modules/knowledge_generation.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 33 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
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
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [progress](../modules/progress.md)
- [python_implementation](../modules/python_implementation.md)
- [section_ownership](../modules/section_ownership.md)
- [storage_spool](../modules/storage_spool.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_generation_plan
    participant p1 as isinstance (src/llm_wiki_cli/services…wledge_generation_plan, 1)
    participant p2 as TypeError (src/llm_wiki_cli/services…knowledge_generation_plan)
    participant p3 as _knowledge_validation_operation
    participant p4 as Path(…).absolute
    participant p5 as Path (src/llm_wiki_cli/services…knowledge_generation_plan)
    participant p6 as _build_knowledge_generation_plan
    participant p7 as KnowledgeGenerationError
    participant p8 as isinstance (src/llm_wiki_cli/services…edge_validation_operation)
    participant p9 as _validated_inventory
    participant p10 as wiki_root.is_absolute
    participant p11 as _validated_source_hashes
    participant p12 as TypeError (src/llm_wiki_cli/services…edge_validation_operation)
    participant p13 as _validated_consumed_inputs
    participant p14 as _IndexValidationOperation
    participant p15 as _validated_page_maps
    participant p16 as _INDEX_VALIDATION_OPERATION.set
    participant p17 as _exact_source_mapping
    participant p18 as object.__setattr__ (src/llm_wiki_cli/services…edge_validation_operation)
    participant p19 as _INDEX_VALIDATION_OPERATION.reset
    participant p20 as isinstance (src/llm_wiki_cli/services…knowledge_generation_plan)
    participant p21 as _build_evidence_baselines
    participant p22 as _validated_evidence_page_paths
    participant p23 as min (src/llm_wiki_cli/services…knowledge_generation_plan)
    participant p24 as _preserve_unchanged_unknown_baselines
    participant p25 as _mark_untrusted_evidence
    participant p26 as previous.evidence_baselines.get (src/llm_wiki_cli/services…knowledge_generation_plan)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…wledge_generation_plan, 1)(inputs, KnowledgeGenerationInputs)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…knowledge_generation_plan)('inputs must be a KnowledgeGenerationInputs')
    p0->>p3: _knowledge_validation_operation
    p0-->>p4: Path(…).absolute
    p0-->>p5: Path (src/llm_wiki_cli/services…knowledge_generation_plan)(inputs.wiki_dir)
    p0->>p6: _build_knowledge_generation_plan
    p0->>p7: KnowledgeGenerationError
    p3-->>p8: isinstance (src/llm_wiki_cli/services…edge_validation_operation)(wiki_root, Path)
    p6->>p9: _validated_inventory
    p3-->>p10: wiki_root.is_absolute
    p6->>p11: _validated_source_hashes
    p3-->>p12: TypeError (src/llm_wiki_cli/services…edge_validation_operation)('validation operation requires an absolute wiki root')
    p6->>p13: _validated_consumed_inputs
    p3->>p14: _IndexValidationOperation
    p6->>p15: _validated_page_maps
    p3-->>p16: _INDEX_VALIDATION_OPERATION.set(operation)
    p6->>p17: _exact_source_mapping
    p3-->>p18: object.__setattr__ (src/llm_wiki_cli/services…edge_validation_operation)(operation, '_active', False)
    p6->>p17: _exact_source_mapping
    p3-->>p19: _INDEX_VALIDATION_OPERATION.reset(token)
    p6-->>p20: isinstance (src/llm_wiki_cli/services…knowledge_generation_plan)(previous, SyncManifest)
    p6->>p7: KnowledgeGenerationError
    p6->>p21: _build_evidence_baselines
    p6->>p22: _validated_evidence_page_paths
    p6->>p22: _validated_evidence_page_paths
    p6-->>p23: min (src/llm_wiki_cli/services…knowledge_generation_plan)(overlapping_page_paths)
    p6->>p7: KnowledgeGenerationError
    p6->>p24: _preserve_unchanged_unknown_baselines
    p6->>p25: _mark_untrusted_evidence
    p6-->>p26: previous.evidence_baselines.get (src/llm_wiki_cli/services…knowledge_generation_plan)(page_path)
```

> Call sequence diagram shows 30 of 4562 interactions; 4532 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 1445 (1437 omitted); unresolved 5 of 1052 (1047 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_generation.py:_validated_inventory` | 15 | - | external | 7 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_validated_inventory` | 15 | [src/llm_wiki_cli/services/knowledge_generation.py](../modules/knowledge_generation.md) | internal | 6 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_validated_inventory` | 15 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_validated_source_hashes` | 32 | [src/llm_wiki_cli/services/knowledge_generation.py](../modules/knowledge_generation.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_exact_source_mapping` | 33 | - | external | 10 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_exact_source_mapping` | 33 | [src/llm_wiki_cli/services/knowledge_generation.py](../modules/knowledge_generation.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_raise_page_map_parity` | 41 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_generation.py:_raise_page_map_parity` | 41 | [src/llm_wiki_cli/services/knowledge_generation.py](../modules/knowledge_generation.md) | internal | 2 |
> Omission summary shows 8 of 1089 groups; 1081 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_knowledge_generation_plan"]
    s2["2. isinstance (src/llm_wiki_cli/services…wledge_generation_plan, 1)"]
    s3["3. TypeError (src/llm_wiki_cli/services…knowledge_generation_plan)"]
    s4["4. _knowledge_validation_operation"]
    s5["5. isinstance (src/llm_wiki_cli/services…edge_validation_operation)"]
    s6["6. wiki_root.is_absolute"]
    s7["7. TypeError (src/llm_wiki_cli/services…edge_validation_operation)"]
    s8["8. _IndexValidationOperation"]
    s9["9. _INDEX_VALIDATION_OPERATION.set"]
    s10["10. object.__setattr__ (src/llm_wiki_cli/services…edge_validation_operation)"]
    s11["11. _INDEX_VALIDATION_OPERATION.reset"]
    s12["12. Path(…).absolute"]
    s1 -. "isinstance (src/llm_wiki_cli/services…wledge_generation_plan, 1)(inputs, KnowledgeGenerationInputs)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…knowledge_generation_plan)('inputs must be a KnowledgeGenerationInputs')" .-> s3
    s1 -->|"_knowledge_validation_operation(...)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…edge_validation_operation)(wiki_root, Path)" .-> s5
    s4 -. "wiki_root.is_absolute(data not statically known)" .-> s6
    s4 -. "TypeError (src/llm_wiki_cli/services…edge_validation_operation)('validation operation requires an absolute wiki root')" .-> s7
    s4 -->|"_IndexValidationOperation(wiki_root)"| s8
    s4 -. "_INDEX_VALIDATION_OPERATION.set(operation)" .-> s9
    s4 -. "object.__setattr__ (src/llm_wiki_cli/services…edge_validation_operation)(operation, '_active', False)" .-> s10
    s4 -. "_INDEX_VALIDATION_OPERATION.reset(token)" .-> s11
    s1 -. "Path(…).absolute(data not statically known)" .-> s12
    click s1 "../modules/knowledge_generation.md"
    click s4 "../modules/knowledge_index.md"
    click s8 "../modules/knowledge_index.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_generation_plan` | `inputs: KnowledgeGenerationInputs` | `KnowledgeGenerationInputs`, `KnowledgeGenerationError`, `KnowledgeArtifactError`, `KnowledgeEnvelopeError`, `KnowledgeGraphError`, `KnowledgeIndexBuildError`, `KnowledgeLinkError`, `SyncManifestError` | - | `_build_knowledge_generation_plan(...)` |
| `isinstance (src/llm_wiki_cli/services…wledge_generation_plan, 1)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…knowledge_generation_plan)` | - | - | - | - |
| `_knowledge_validation_operation` | `wiki_root: Path` | `Path` | - | - |
| `isinstance (src/llm_wiki_cli/services…edge_validation_operation)` | - | - | - | - |
| `wiki_root.is_absolute` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…edge_validation_operation)` | - | - | - | - |
| `_IndexValidationOperation` | - | - | - | - |
| `_INDEX_VALIDATION_OPERATION.set` | - | - | - | - |
| `object.__setattr__ (src/llm_wiki_cli/services…edge_validation_operation)` | - | - | - | - |
| `_INDEX_VALIDATION_OPERATION.reset` | - | - | - | - |
| `Path(…).absolute` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_generation_plan | isinstance (src/llm_wiki_cli/services…wledge_generation_plan, 1) | 184 | `isinstance(inputs, KnowledgeGenerationInputs)` |
| build_knowledge_generation_plan | TypeError (src/llm_wiki_cli/services…knowledge_generation_plan) | 185 | `TypeError('inputs must be a KnowledgeGenerationInputs')` |
| build_knowledge_generation_plan | _knowledge_validation_operation | 187 | `_knowledge_validation_operation(...)` |
| _knowledge_validation_operation | isinstance (src/llm_wiki_cli/services…edge_validation_operation) | 318 | `isinstance(wiki_root, Path)` |
| _knowledge_validation_operation | wiki_root.is_absolute | 318 | `wiki_root.is_absolute(data not statically known)` |
| _knowledge_validation_operation | TypeError (src/llm_wiki_cli/services…edge_validation_operation) | 319 | `TypeError('validation operation requires an absolute wiki root')` |
| _knowledge_validation_operation | _IndexValidationOperation | 320 | `_IndexValidationOperation(wiki_root)` |
| _knowledge_validation_operation | _INDEX_VALIDATION_OPERATION.set | 321 | `_INDEX_VALIDATION_OPERATION.set(operation)` |
| _knowledge_validation_operation | object.__setattr__ (src/llm_wiki_cli/services…edge_validation_operation) | 325 | `object.__setattr__(operation, '_active', False)` |
| _knowledge_validation_operation | _INDEX_VALIDATION_OPERATION.reset | 326 | `_INDEX_VALIDATION_OPERATION.reset(token)` |
| build_knowledge_generation_plan | Path(…).absolute | 187 | `Path(inputs.wiki_dir).absolute(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_knowledge_generation_plan` | `isinstance` | 184 |
| external_call | `build_knowledge_generation_plan` | `TypeError` | 185 |
| external_call | `_knowledge_validation_operation` | `isinstance` | 318 |
| unresolved_call | `_knowledge_validation_operation` | `wiki_root.is_absolute` | 318 |
| external_call | `_knowledge_validation_operation` | `TypeError` | 319 |
| external_call | `_knowledge_validation_operation` | `object.__setattr__` | 325 |
| unresolved_call | `_knowledge_validation_operation` | `_INDEX_VALIDATION_OPERATION.reset` | 326 |
| unresolved_call | `build_knowledge_generation_plan` | `Path(inputs.wiki_dir).absolute` | 187 |
| step_limit | `build_knowledge_generation_plan` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_generation_plan` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_generation_plan` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
