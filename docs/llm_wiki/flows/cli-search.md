# search

**Entry point:** `run` (`cli`)
**Source:** [search_cmd](../modules/search_cmd.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), and 31 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [markdown_sections](../modules/markdown_sections.md)
- [search_cmd](../modules/search_cmd.md)
- [search_discovery](../modules/search_discovery.md)
- [search_discovery_capture](../modules/search_discovery_capture.md)
- [search_lexical](../modules/search_lexical.md)
- [search_rank](../modules/search_rank.md)
- [search_service](../modules/search_service.md)
- [search_source](../modules/search_source.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)
- [workflow_profile](../modules/workflow_profile.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as validate_source_root
    participant p2 as search_wiki (src/llm_wiki_cli/api.py)
    participant p3 as validate_path
    participant p4 as search_wiki (src/llm_wiki_cli/services/search_service.py)
    participant p5 as windows_current_user_sid
    participant p6 as _current_windows_user_sid
    participant p7 as normalize_search
    participant p8 as search_prevalidated_roots
    participant p9 as normalize_documentation_query_limit
    participant p10 as resolve_source_selection
    participant p11 as capture_source_selection_inputs
    participant p12 as validate_live_query_source_selection
    participant p13 as build_source_snapshot
    participant p14 as search_records
    participant p15 as page_records
    participant p16 as _page_membership
    participant p17 as captured_manifest
    participant p18 as _windows_sid_string
    participant p19 as capture_source_index
    participant p20 as capture_discovery
    participant p21 as enrich_search
    participant p22 as source_snapshot_matches_current_files
    participant p23 as SyncManifest.load
    participant p24 as _validate_capture_options
    participant p25 as rank_pages (src/llm_wiki_cli/services/search_rank.py)
    participant p26 as _object
    participant p27 as rank_pages (src/llm_wiki_cli/services/search_lexical.py)
    participant p28 as _resolve_snapshot_selection
    participant p29 as getattr (src/llm_wiki_cli/commands/search_cmd.py:run)
    participant p30 as Path(…).expanduser
    p0->>p1: validate_source_root
    p0->>p2: search_wiki (src/llm_wiki_cli/api.py)
    p0->>p3: validate_path
    p2->>p4: search_wiki (src/llm_wiki_cli/services/search_service.py)
    p1->>p5: windows_current_user_sid
    p5->>p6: _current_windows_user_sid
    p4->>p7: normalize_search
    p4->>p8: search_prevalidated_roots
    p7->>p9: normalize_documentation_query_limit
    p8->>p10: resolve_source_selection
    p8->>p11: capture_source_selection_inputs
    p8->>p12: validate_live_query_source_selection
    p8->>p13: build_source_snapshot
    p8->>p14: search_records
    p8->>p15: page_records
    p8->>p16: _page_membership
    p8->>p17: captured_manifest
    p6->>p18: _windows_sid_string
    p8->>p19: capture_source_index
    p8->>p20: capture_discovery
    p8->>p21: enrich_search
    p8->>p22: source_snapshot_matches_current_files
    p12->>p23: SyncManifest.load
    p13->>p24: _validate_capture_options
    p14->>p25: rank_pages (src/llm_wiki_cli/services/search_rank.py)
    p21->>p26: _object
    p14->>p27: rank_pages (src/llm_wiki_cli/services/search_lexical.py)
    p11->>p28: _resolve_snapshot_selection
    p0-->>p29: getattr (src/llm_wiki_cli/commands/search_cmd.py:run)(args, 'include_source', False)
    p1-->>p30: Path(…).expanduser
```

> Call sequence diagram shows 30 of 1274 interactions; 1244 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 517 (516 omitted); unresolved 1 of 345 (344 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_source_root` | 2 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 7 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 2 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 2 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/filesystem_guard.py:windows_current_user_sid` | 21 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
| `src/llm_wiki_cli/services/filesystem_guard.py:_current_windows_user_sid` | 23 | - | external | 19 |
> Omission summary shows 8 of 219 groups; 211 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. validate_source_root"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. (…).resolve"]
    s6["6. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s7["7. Path.cwd().resolve"]
    s8["8. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s10["10. PathValidationError"]
    s11["11. Path(…).expanduser"]
    s12["12. Path (src/llm_wiki_cli/config.py:validate_source_root)"]
    s1 -->|"validate_source_root(args.src_dir, '--src-dir', allow_external=args.allow_external_src)"| s2
    s2 -->|"validate_path(path, label)"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(…).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve(data not statically known)" .-> s7
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s3 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s2 -. "Path(…).expanduser(data not statically known)" .-> s11
    s2 -. "Path (src/llm_wiki_cli/config.py:validate_source_root)(path)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    click s1 "../modules/search_cmd.md"
    click s2 "../modules/config.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `Path(…).expanduser` | - | - | - | - |
| `Path (src/llm_wiki_cli/config.py:validate_source_root)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | validate_source_root | 10 | `validate_source_root(args.src_dir, '--src-dir', allow_external=args.allow_external_src)` |
| validate_source_root | validate_path | 160 | `validate_path(path, label)` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 138 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 140 | `PathValidationError(...)` |
| validate_source_root | Path(…).expanduser | 163 | `Path(path).expanduser(data not statically known)` |
| validate_source_root | Path (src/llm_wiki_cli/config.py:validate_source_root) | 163 | `Path(path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 24 |
| output | `print` | `run` | 27 |
| output | `print` | `run` | 28 |
| output | `print` | `run` | 29 |
| output | `print` | `run` | 31 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| unresolved_call | `validate_source_root` | `Path(path).expanduser` | 163 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.

The command validates the query options and configured roots, then delegates to
the shared search service. Default ranked discovery scores captured canonical
text with section-local relevance and qualified one-hop declaration leads.
Literal identities retain precedence; a declared flow link establishes neither
runtime invocation nor source correctness. Legacy ranked and substring modes
keep their separate matching contracts. Source-text indexing remains explicit.
