# build_runtime_knowledge_plan

**Entry point:** `build_runtime_knowledge_plan` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), and 38 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
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
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
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
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
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
    participant p0 as build_runtime_knowledge_plan
    participant p1 as isinstance (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p2 as TypeError (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p3 as capture_committed_knowledge
    participant p4 as replace (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p5 as committed_state.require_for
    participant p6 as _prepared_runtime_governance
    participant p7 as inputs.source_snapshot.hashes_for
    participant p8 as _producer_evidence
    participant p9 as _manifest_extractor_refs
    participant p10 as with_source_selection_generation_input
    participant p11 as _runtime_manifest_generation_inputs
    participant p12 as KnowledgeGenerationError
    participant p13 as next_manifest.with_generation_state
    participant p14 as infrastructure_evidence_by_page
    participant p15 as _infrastructure_extractor_component
    participant p16 as prepare_runtime_generation_options
    participant p17 as committed_state.captured_bytes.get
    participant p18 as json.loads (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p19 as previous_maintenance[…].values
    participant p20 as confirmed_missing_source_paths
    participant p21 as frozenset (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p22 as Path (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p23 as (…).exists (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p24 as (…).is_symlink (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p25 as ACTIVE_WRITE_BASIS.get
    participant p26 as dict (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    participant p27 as _stabilize_revision_only_noop
    participant p28 as KnowledgeGenerationInputs
    participant p29 as runtime_consumed_inputs
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)(inputs, RuntimeKnowledgeInputs)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)('inputs must be a RuntimeKnowledgeInputs')
    p0->>p3: capture_committed_knowledge
    p0-->>p4: replace (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)(inputs, committed_state=committed_state)
    p0-->>p5: committed_state.require_for(inputs.target_wiki_dir)
    p0->>p6: _prepared_runtime_governance
    p0-->>p7: inputs.source_snapshot.hashes_for(inputs.inventory)
    p0->>p8: _producer_evidence
    p0->>p9: _manifest_extractor_refs
    p0->>p10: with_source_selection_generation_input
    p0->>p11: _runtime_manifest_generation_inputs
    p0->>p12: KnowledgeGenerationError
    p0-->>p13: next_manifest.with_generation_state(surfaces=next_manifest.surfaces, generation_inputs=generation_inputs)
    p0->>p14: infrastructure_evidence_by_page
    p0->>p15: _infrastructure_extractor_component
    p0->>p16: prepare_runtime_generation_options
    p0-->>p17: committed_state.captured_bytes.get(ADOPTION_FILENAME)
    p0-->>p18: json.loads (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)(marker_bytes)
    p0-->>p19: previous_maintenance[…].values
    p0->>p20: confirmed_missing_source_paths
    p0-->>p21: frozenset (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    p0-->>p19: previous_maintenance[…].values
    p0-->>p22: Path (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)(inputs.target_wiki_dir)
    p0-->>p23: (…).exists (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    p0-->>p24: (…).is_symlink (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)
    p0-->>p25: ACTIVE_WRITE_BASIS.get
    p0-->>p26: dict (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)(operation_basis.expected)
    p0->>p27: _stabilize_revision_only_noop
    p0->>p28: KnowledgeGenerationInputs
    p0->>p29: runtime_consumed_inputs
```

> Call sequence diagram shows 30 of 3736 interactions; 3706 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 1187 (1180 omitted); unresolved 9 of 846 (837 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_orchestration.py:capture_committed_knowledge` | 4 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/knowledge_orchestration.py:capture_committed_knowledge` | 4 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_orchestration.py:capture_committed_knowledge` | 4 | [src/llm_wiki_cli/services/maintenance_protocol.py](../modules/maintenance_protocol.md) | internal | 1 |
| `src/llm_wiki_cli/services/maintenance_protocol.py:guard_maintenance_owner` | 7 | [src/llm_wiki_cli/services/knowledge_storage_io.py](../modules/knowledge_storage_io.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 8 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_absolute_path` | 8 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 11 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 11 | - | unresolved | 5 |
> Omission summary shows 8 of 881 groups; 873 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_runtime_knowledge_plan"]
    s2["2. isinstance (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)"]
    s3["3. TypeError (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)"]
    s4["4. capture_committed_knowledge"]
    s5["5. Path(…).resolve (src/llm_wiki_cli/services…pture_committed_knowledge)"]
    s6["6. Path (src/llm_wiki_cli/services…pture_committed_knowledge)"]
    s7["7. guard_maintenance_owner"]
    s8["8. _absolute_path"]
    s9["9. Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)"]
    s10["10. os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)"]
    s11["11. first_unsafe_path_component"]
    s12["12. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)(inputs, RuntimeKnowledgeInputs)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)('inputs must be a RuntimeKnowledgeInputs')" .-> s3
    s1 -->|"capture_committed_knowledge(inputs.target_wiki_dir, inputs.previous_manifest)"| s4
    s4 -. "Path(…).resolve (src/llm_wiki_cli/services…pture_committed_knowledge)(data not statically known)" .-> s5
    s4 -. "Path (src/llm_wiki_cli/services…pture_committed_knowledge)(wiki_dir)" .-> s6
    s4 -->|"guard_maintenance_owner(root, manifest)"| s7
    s7 -->|"_absolute_path(Path(...))"| s8
    s8 -. "Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)(os.path.abspath(...))" .-> s9
    s8 -. "os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)(path)" .-> s10
    s8 -->|"first_unsafe_path_component(path)"| s11
    s11 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s12
    b0["mutation captured.update"]
    s4 -. "mutation captured.update" .-> b0
    b1["mutation pending_parts.pop"]
    s11 -. "mutation pending_parts.pop" .-> b1
    click s1 "../modules/knowledge_orchestration.md"
    click s4 "../modules/knowledge_orchestration.md"
    click s7 "../modules/maintenance_protocol.md"
    click s8 "../modules/knowledge_storage_io.md"
    click s11 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_runtime_knowledge_plan` | `inputs: RuntimeKnowledgeInputs` | `RuntimeKnowledgeInputs`, `SourceSelectionError`, `__version__`, `KNOWLEDGE_SCHEMA_VERSION`, `WIKI_SURFACE_INDEX_SCHEMA_VERSION`, `SYNC_ANALYSIS_EXTENSION` | - | `_stabilize_revision_only_noop(...)` |
| `isinstance (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ld_runtime_knowledge_plan)` | - | - | - | - |
| `capture_committed_knowledge` | `wiki_dir: str \| Path`, `manifest: SyncManifest \| None` | `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `MANIFEST_FILENAME`, `MANIFEST_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KnowledgeArtifactError`, `KnowledgeArtifactError` | `captured[...]`, `captured[...]` | `state` |
| `Path(…).resolve (src/llm_wiki_cli/services…pture_committed_knowledge)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…pture_committed_knowledge)` | - | - | - | - |
| `guard_maintenance_owner` | `wiki_dir: str \| Path`, `manifest` | - | - | `None`, `None`, `marker` |
| `_absolute_path` | `path: Path` | - | - | `path` |
| `Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_runtime_knowledge_plan | isinstance (src/llm_wiki_cli/services…ld_runtime_knowledge_plan) | 393 | `isinstance(inputs, RuntimeKnowledgeInputs)` |
| build_runtime_knowledge_plan | TypeError (src/llm_wiki_cli/services…ld_runtime_knowledge_plan) | 394 | `TypeError('inputs must be a RuntimeKnowledgeInputs')` |
| build_runtime_knowledge_plan | capture_committed_knowledge | 397 | `capture_committed_knowledge(inputs.target_wiki_dir, inputs.previous_manifest)` |
| capture_committed_knowledge | Path(…).resolve (src/llm_wiki_cli/services…pture_committed_knowledge) | 239 | `Path(wiki_dir).resolve(data not statically known)` |
| capture_committed_knowledge | Path (src/llm_wiki_cli/services…pture_committed_knowledge) | 239 | `Path(wiki_dir)` |
| capture_committed_knowledge | guard_maintenance_owner | 242 | `guard_maintenance_owner(root, manifest)` |
| guard_maintenance_owner | _absolute_path | 104 | `_absolute_path(Path(...))` |
| _absolute_path | Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path) | 49 | `Path(os.path.abspath(...))` |
| _absolute_path | os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path) | 49 | `os.path.abspath(path)` |
| _absolute_path | first_unsafe_path_component | 50 | `first_unsafe_path_component(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `captured.update` | `capture_committed_knowledge` | 268 |
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_runtime_knowledge_plan` | `isinstance` | 393 |
| external_call | `build_runtime_knowledge_plan` | `TypeError` | 394 |
| unresolved_call | `capture_committed_knowledge` | `Path(wiki_dir).resolve` | 239 |
| external_call | `_absolute_path` | `os.path.abspath` | 49 |
| step_limit | `build_runtime_knowledge_plan` | `first 12 steps` | 0 |
| truncated_flow | `build_runtime_knowledge_plan` | `depth limit` | 0 |

## Behavior

This flow starts at `build_runtime_knowledge_plan` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
