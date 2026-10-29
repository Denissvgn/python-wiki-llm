# load_snapshot_knowledge_observability

**Entry point:** `load_snapshot_knowledge_observability` (`api`)
**Source:** [knowledge_observability](../modules/knowledge_observability.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [bootstrap_recovery](../modules/bootstrap_recovery.md), [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), and 38 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
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
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [paths](../modules/paths.md)
- [section_ownership](../modules/section_ownership.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_snapshot_knowledge_observability
    participant p1 as resolve_source_selection
    participant p2 as capture_source_selection_inputs
    participant p3 as SyncManifest.load
    participant p4 as validate_persisted_source_selection_identity
    participant p5 as build_source_snapshot
    participant p6 as _snapshot_result
    participant p7 as _degraded_snapshot_view
    participant p8 as _knowledge_projection_declared
    participant p9 as evaluate_surface_index
    participant p10 as load_knowledge_state
    participant p11 as _snapshot_error_view
    participant p12 as _with_current_source_selection
    participant p13 as build_knowledge_read_view
    participant p14 as KnowledgeLoadResult
    participant p15 as source_selection_identity_from_generation_inputs
    participant p16 as _validate_capture_options
    participant p17 as _resolve_snapshot_selection
    participant p18 as source_selection_inputs_from_generation_inputs
    participant p19 as collect_wiki_pages
    participant p20 as _override_text
    participant p21 as _new_snapshot_buckets
    participant p22 as _normalize_only_files
    participant p23 as summarize_knowledge_view
    participant p24 as _page_entries
    participant p25 as _collect_source_selection_controls
    participant p26 as _source_maps
    participant p27 as _locate_exact_path
    participant p28 as _selection_inputs_from_buckets
    participant p29 as time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability)
    participant p30 as Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection)
    p0->>p1: resolve_source_selection
    p0->>p2: capture_source_selection_inputs
    p0->>p3: SyncManifest.load
    p0->>p4: validate_persisted_source_selection_identity
    p0->>p5: build_source_snapshot
    p0->>p6: _snapshot_result
    p0->>p7: _degraded_snapshot_view
    p0->>p8: _knowledge_projection_declared
    p0->>p9: evaluate_surface_index
    p0->>p10: load_knowledge_state
    p0->>p11: _snapshot_error_view
    p0->>p12: _with_current_source_selection
    p0->>p13: build_knowledge_read_view
    p0->>p14: KnowledgeLoadResult
    p4->>p15: source_selection_identity_from_generation_inputs
    p5->>p16: _validate_capture_options
    p2->>p17: _resolve_snapshot_selection
    p4->>p18: source_selection_inputs_from_generation_inputs
    p9->>p19: collect_wiki_pages
    p1->>p20: _override_text
    p2->>p21: _new_snapshot_buckets
    p5->>p22: _normalize_only_files
    p6->>p23: summarize_knowledge_view
    p9->>p24: _page_entries
    p2->>p25: _collect_source_selection_controls
    p9->>p26: _source_maps
    p1->>p27: _locate_exact_path
    p2->>p28: _selection_inputs_from_buckets
    p0-->>p29: time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability)
    p1-->>p30: Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection)
```

> Call sequence diagram shows 30 of 2604 interactions; 2574 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 798 (797 omitted); unresolved 1 of 656 (655 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_observability.py:load_snapshot_knowledge_observability` | 1 | - | external | 1 |
| `src/llm_wiki_cli/services/source_selection.py:resolve_source_selection` | 4 | - | external | 1 |
| `src/llm_wiki_cli/services/source_selection.py:resolve_source_selection` | 4 | [src/llm_wiki_cli/services/source_selection.py](../modules/source_selection.md) | internal | 6 |
| `src/llm_wiki_cli/services/source_selection.py:_override_text` | 8 | - | external | 3 |
| `src/llm_wiki_cli/services/source_selection.py:_override_text` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/source_selection.py:_override_text` | 8 | [src/llm_wiki_cli/services/source_selection.py](../modules/source_selection.md) | internal | 3 |
| `src/llm_wiki_cli/services/source_selection.py:_selection_path` | 15 | [src/llm_wiki_cli/services/source_selection.py](../modules/source_selection.md) | internal | 4 |
| `src/llm_wiki_cli/services/source_selection.py:_require_selection_path` | 16 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 707 groups; 699 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1151; effect analysis evaluated: 642, partial: 47, unavailable: 462. Counts include steps omitted from the displayed trace.

Collector observations for 689 source steps with known totals: observed: 4178, emitted: 3782, omitted: 396. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `load_snapshot_knowledge_observability` | `available` | `evaluated` | `available` | `12` | `12` | `0` |
| `time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_cli/services…t_knowledge_observability)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `resolve_source_selection` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_cli/services…:resolve_source_selection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `SourceSelectionError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_override_text` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_cli/services…lection.py:_override_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `override.as_posix` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `os.fspath (src/llm_wiki_cli/services…lection.py:_override_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `SourceSelectionError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. load_snapshot_knowledge_observability"]
    s2["2. time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability)"]
    s3["3. Path (src/llm_wiki_cli/services…t_knowledge_observability)"]
    s4["4. resolve_source_selection"]
    s5["5. Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection)"]
    s6["6. Path (src/llm_wiki_cli/services…:resolve_source_selection)"]
    s7["7. SourceSelectionError"]
    s8["8. _override_text"]
    s9["9. isinstance (src/llm_wiki_cli/services…lection.py:_override_text)"]
    s10["10. override.as_posix"]
    s11["11. os.fspath (src/llm_wiki_cli/services…lection.py:_override_text)"]
    s12["12. SourceSelectionError"]
    s1 -. "time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability)(data not statically known)" .-> s2
    s1 -. "Path (src/llm_wiki_cli/services…t_knowledge_observability)(wiki_dir)" .-> s3
    s1 -->|"resolve_source_selection(effective_src_dir, source_selection)"| s4
    s4 -. "Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection)(data not statically known)" .-> s5
    s4 -. "Path (src/llm_wiki_cli/services…:resolve_source_selection)(root)" .-> s6
    s4 -->|"SourceSelectionError('source_root', 'must resolve to a repository path')"| s7
    s4 -->|"_override_text(override)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…lection.py:_override_text)(override, Path)" .-> s9
    s8 -. "override.as_posix(data not statically known)" .-> s10
    s8 -. "os.fspath (src/llm_wiki_cli/services…lection.py:_override_text)(override)" .-> s11
    s8 -->|"SourceSelectionError('source_selection', 'override must be a repository-relative path')"| s12
    click s1 "../modules/knowledge_observability.md"
    click s4 "../modules/source_selection.md"
    click s7 "../modules/source_selection.md"
    click s8 "../modules/source_selection.md"
    click s12 "../modules/source_selection.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_snapshot_knowledge_observability` | `wiki_dir: str \| Path`, `src_dir: str \| Path \| None`, `source_selection: str \| Path \| None` | `SourceSelectionError`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeStateLoadError` | - | `_snapshot_result(...)`, `_snapshot_result(...)`, `_snapshot_result(...)`, `_snapshot_result(...)`, `_snapshot_result(...)` |
| `time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…t_knowledge_observability)` | - | - | - | - |
| `resolve_source_selection` | `root: str \| Path`, `override: str \| Path \| None` | `SOURCE_SELECTION_PATH` | - | `None`, `None`, `policy` |
| `Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…:resolve_source_selection)` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |
| `_override_text` | `override: str \| Path` | `Path` | - | `_selection_path(...)` |
| `isinstance (src/llm_wiki_cli/services…lection.py:_override_text)` | - | - | - | - |
| `override.as_posix` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…lection.py:_override_text)` | - | - | - | - |
| `SourceSelectionError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_snapshot_knowledge_observability | time.perf_counter (src/llm_wiki_cli/services…t_knowledge_observability) | 546 | `time.perf_counter(data not statically known)` |
| load_snapshot_knowledge_observability | Path (src/llm_wiki_cli/services…t_knowledge_observability) | 547 | `Path(wiki_dir)` |
| load_snapshot_knowledge_observability | resolve_source_selection | 552 | `resolve_source_selection(effective_src_dir, source_selection)` |
| resolve_source_selection | Path(…).resolve (src/llm_wiki_cli/services…:resolve_source_selection) | 606 | `Path(root).resolve(data not statically known)` |
| resolve_source_selection | Path (src/llm_wiki_cli/services…:resolve_source_selection) | 606 | `Path(root)` |
| resolve_source_selection | SourceSelectionError | 608 | `SourceSelectionError('source_root', 'must resolve to a repository path')` |
| resolve_source_selection | _override_text | 615 | `_override_text(override)` |
| _override_text | isinstance (src/llm_wiki_cli/services…lection.py:_override_text) | 583 | `isinstance(override, Path)` |
| _override_text | override.as_posix | 583 | `override.as_posix(data not statically known)` |
| _override_text | os.fspath (src/llm_wiki_cli/services…lection.py:_override_text) | 583 | `os.fspath(override)` |
| _override_text | SourceSelectionError | 585 | `SourceSelectionError('source_selection', 'override must be a repository-relative path')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `load_snapshot_knowledge_observability` | `time.perf_counter` | 546 |
| unresolved_call | `resolve_source_selection` | `Path(root).resolve` | 606 |
| external_call | `_override_text` | `isinstance` | 583 |
| unresolved_call | `_override_text` | `override.as_posix` | 583 |
| external_call | `_override_text` | `os.fspath` | 583 |
| step_limit | `load_snapshot_knowledge_observability` | `first 12 steps` | 0 |
| truncated_flow | `load_snapshot_knowledge_observability` | `depth limit` | 0 |

## Behavior

This flow starts at `load_snapshot_knowledge_observability` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
