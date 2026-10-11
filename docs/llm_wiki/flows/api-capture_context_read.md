# capture_context_read

**Entry point:** `capture_context_read` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [common](../modules/common.md), [config](../modules/config.md), and 58 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
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
- [go_calls](../modules/go_calls.md)
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
- [knowledge_generation](../modules/knowledge_generation.md)
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
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [python_bindings](../modules/python_bindings.md)
- [python_calls](../modules/python_calls.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as capture_context_read
    participant p1 as isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p2 as TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p3 as callable (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p4 as validate_source_root
    participant p5 as validate_path
    participant p6 as source_root.is_dir (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p7 as ContextPacketUnavailableError
    participant p8 as resolve_source_selection
    participant p9 as capture_source_selection_inputs
    participant p10 as validate_live_query_source_selection
    participant p11 as ProtocolRequestError
    participant p12 as str (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p13 as build_source_snapshot
    participant p14 as _guard_windows_inputs
    participant p15 as _assert_source_unchanged
    participant p16 as _source_anchor
    participant p17 as context_service.get_inventory
    p0-->>p1: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(read_only, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('read_only must be a boolean')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(allow_external_src, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('allow_external_src must be a boolean')
    p0-->>p3: callable (src/llm_wiki_cli/services…t.py:capture_context_read)(plan_reporter)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('plan_reporter must be callable or None')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(allow_selection_mismatch, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('allow_selection_mismatch must be a boolean')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(strict_wiki_symlinks, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('strict_wiki_symlinks must be a boolean')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(capture_implementation_observations, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('capture_implementation_observations must be a boolean')
    p0->>p4: validate_source_root
    p0->>p5: validate_path
    p0-->>p6: source_root.is_dir (src/llm_wiki_cli/services…t.py:capture_context_read)
    p0->>p7: ContextPacketUnavailableError
    p0->>p8: resolve_source_selection
    p0->>p9: capture_source_selection_inputs
    p0->>p10: validate_live_query_source_selection
    p0->>p11: ProtocolRequestError
    p0-->>p12: str (src/llm_wiki_cli/services…t.py:capture_context_read)(exc)
    p0->>p11: ProtocolRequestError
    p0-->>p12: str (src/llm_wiki_cli/services…t.py:capture_context_read)(exc)
    p0->>p13: build_source_snapshot
    p0->>p14: _guard_windows_inputs
    p0->>p15: _assert_source_unchanged
    p0->>p16: _source_anchor
    p0-->>p17: context_service.get_inventory(…)
    p0-->>p12: str (src/llm_wiki_cli/services…t.py:capture_context_read)(source_root)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(collected, InventoryResult)
```

> Call sequence diagram shows 30 of 5261 interactions; 5231 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 1663 (1647 omitted); unresolved 2 of 1716 (1714 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_source_root` | 14 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 7 |
| `src/llm_wiki_cli/config.py:validate_path` | 15 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 15 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 15 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 14 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 14 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 14 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
| `src/llm_wiki_cli/services/filesystem_guard.py:windows_current_user_sid` | 33 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
> Omission summary shows 8 of 1332 groups; 1324 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. capture_context_read"]
    s2["2. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s3["3. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s4["4. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s5["5. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s6["6. callable (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s7["7. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s8["8. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s9["9. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s10["10. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s11["11. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s12["12. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(read_only, bool)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('read_only must be a boolean')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(allow_external_src, bool)" .-> s4
    s1 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('allow_external_src must be a boolean')" .-> s5
    s1 -. "callable (src/llm_wiki_cli/services…t.py:capture_context_read)(plan_reporter)" .-> s6
    s1 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('plan_reporter must be callable or None')" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(allow_selection_mismatch, bool)" .-> s8
    s1 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('allow_selection_mismatch must be a boolean')" .-> s9
    s1 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(strict_wiki_symlinks, bool)" .-> s10
    s1 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('strict_wiki_symlinks must be a boolean')" .-> s11
    s1 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(capture_implementation_observations, bool)" .-> s12
    click s1 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `capture_context_read` | `src_dir: str`, `wiki_dir: str`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None`, `allow_selection_mismatch: bool` | `PathValidationError`, `DocumentationQueryError`, `context_service`, `os`, `InventoryResult`, `SourceSnapshot`, `DocumentationQueryError`, `DocumentationQueryError` | `capture_options[...]`, `capture_options[...]`, `capture_options[...]`, `capture_options[...]`, `capture_options[...]`, `wiki_options[...]`, `wiki_options[...]`, `wiki_check_options[...]` | `captured` |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `callable (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 762 | `isinstance(read_only, bool)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 763 | `TypeError('read_only must be a boolean')` |
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 764 | `isinstance(allow_external_src, bool)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 765 | `TypeError('allow_external_src must be a boolean')` |
| capture_context_read | callable (src/llm_wiki_cli/services…t.py:capture_context_read) | 766 | `callable(plan_reporter)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 767 | `TypeError('plan_reporter must be callable or None')` |
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 768 | `isinstance(allow_selection_mismatch, bool)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 769 | `TypeError('allow_selection_mismatch must be a boolean')` |
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 770 | `isinstance(strict_wiki_symlinks, bool)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 771 | `TypeError('strict_wiki_symlinks must be a boolean')` |
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 772 | `isinstance(capture_implementation_observations, bool)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `capture_context_read` | `isinstance` | 762 |
| external_call | `capture_context_read` | `TypeError` | 763 |
| external_call | `capture_context_read` | `isinstance` | 764 |
| external_call | `capture_context_read` | `TypeError` | 765 |
| external_call | `capture_context_read` | `callable` | 766 |
| external_call | `capture_context_read` | `TypeError` | 767 |
| external_call | `capture_context_read` | `isinstance` | 768 |
| external_call | `capture_context_read` | `TypeError` | 769 |
| external_call | `capture_context_read` | `isinstance` | 770 |
| external_call | `capture_context_read` | `TypeError` | 771 |
| external_call | `capture_context_read` | `isinstance` | 772 |
| step_limit | `capture_context_read` | `first 12 steps` | 0 |

## Behavior

This flow starts at `capture_context_read` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
