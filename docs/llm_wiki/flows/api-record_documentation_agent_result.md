# record_documentation_agent_result

**Entry point:** `record_documentation_agent_result` (`api`)
**Source:** [record](../modules/record.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [config](../modules/config.md), and 52 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_claim_evidence](../modules/documentation_claim_evidence.md)
- [documentation_native](../modules/documentation_native.md)
- [documentation_policy](../modules/documentation_policy.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [documentation_review](../modules/documentation_review.md)
- [documentation_run_contracts](../modules/documentation_run_contracts.md)
- [documentation_run_schema](../modules/documentation_run_schema.md)
- [documentation_wiki_input](../modules/documentation_wiki_input.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [integrity](../modules/integrity.md)
- [inventory_cache](../modules/inventory_cache.md)
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
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [record](../modules/record.md)
- [refresh](../modules/refresh.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [team](../modules/team.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [workspace](../modules/workspace.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as record_documentation_agent_result
    participant p1 as _resolve_workspace_root_argument
    participant p2 as Path
    participant p3 as abspath
    participant p4 as fspath
    participant p5 as expanduser
    participant p6 as lexists
    participant p7 as lstat
    participant p8 as DocumentationIntegrityError
    participant p9 as bool
    participant p10 as getattr
    participant p11 as S_ISLNK
    participant p12 as S_ISDIR
    participant p13 as resolve
    participant p14 as _assert_existing_workspace_layout_safe
    participant p15 as _assert_safe_workspace_directory
    p0->>p1: _resolve_workspace_root_argument
    p1-->>p2: Path
    p1-->>p3: abspath
    p1-->>p4: fspath
    p1-->>p5: expanduser
    p1-->>p2: Path
    p1-->>p6: lexists
    p1-->>p7: lstat
    p1->>p8: DocumentationIntegrityError
    p1-->>p9: bool
    p1-->>p10: getattr
    p1-->>p9: bool
    p1-->>p10: getattr
    p1-->>p11: S_ISLNK
    p1->>p8: DocumentationIntegrityError
    p1-->>p12: S_ISDIR
    p1->>p8: DocumentationIntegrityError
    p1-->>p13: resolve
    p1-->>p6: lexists
    p1->>p14: _assert_existing_workspace_layout_safe
    p14-->>p6: lexists
    p14->>p15: _assert_safe_workspace_directory
    p15-->>p7: lstat
    p15->>p8: DocumentationIntegrityError
    p15-->>p9: bool
    p15-->>p10: getattr
    p15-->>p9: bool
    p15-->>p10: getattr
    p15-->>p11: S_ISLNK
    p15->>p8: DocumentationIntegrityError
```

> Call sequence diagram shows 30 of 5425 interactions; 5395 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. record_documentation_agent_result"]
    s2["2. _resolve_workspace_root_argument"]
    s3["3. Path"]
    s4["4. abspath"]
    s5["5. fspath"]
    s6["6. expanduser"]
    s7["7. Path"]
    s8["8. lexists"]
    s9["9. lstat"]
    s10["10. DocumentationIntegrityError"]
    s11["11. bool"]
    s12["12. getattr"]
    s1 -->|"_resolve_workspace_root_argument(workspace)"| s2
    s2 -. "Path(os.path.abspath(...))" .-> s3
    s2 -. "os.path.abspath(os.fspath(...))" .-> s4
    s2 -. "os.fspath(...)" .-> s5
    s2 -. "Path(workspace).expanduser(data not statically known)" .-> s6
    s2 -. "Path(workspace)" .-> s7
    s2 -. "os.path.lexists(requested)" .-> s8
    s2 -. "requested.lstat(data not statically known)" .-> s9
    s2 -->|"DocumentationIntegrityError(...)"| s10
    s2 -. "bool(getattr(...))" .-> s11
    s2 -. "getattr(entry_stat, 'st_reparse_tag', 0)" .-> s12
    b0["filesystem_read result_path.read_bytes"]
    s1 -. "filesystem_read result_path.read_bytes" .-> b0
    b1["mutation run.validation_results.append"]
    s1 -. "mutation run.validation_results.append" .-> b1
    b2["mutation run.validation_results.append"]
    s1 -. "mutation run.validation_results.append" .-> b2
    click s1 "../modules/record.md"
    click s2 "../modules/workspace.md"
    click s10 "../modules/documentation_run_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `record_documentation_agent_result` | `workspace: str \| Path`, `result: DocumentationAgentResult \| Mapping[str, Any]` | - | - | `run`, `run`, `run`, `run`, `run`, `run`, `run` |
| `_resolve_workspace_root_argument` | `workspace: str \| Path` | - | - | `resolved` |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `fspath` | - | - | - | - |
| `expanduser` | - | - | - | - |
| `Path` | - | - | - | - |
| `lexists` | - | - | - | - |
| `lstat` | - | - | - | - |
| `DocumentationIntegrityError` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| record_documentation_agent_result | _resolve_workspace_root_argument | 781 | `_resolve_workspace_root_argument(workspace)` |
| _resolve_workspace_root_argument | Path | 102 | `Path(os.path.abspath(...))` |
| _resolve_workspace_root_argument | abspath | 102 | `os.path.abspath(os.fspath(...))` |
| _resolve_workspace_root_argument | fspath | 102 | `os.fspath(...)` |
| _resolve_workspace_root_argument | expanduser | 102 | `Path(workspace).expanduser(data not statically known)` |
| _resolve_workspace_root_argument | Path | 102 | `Path(workspace)` |
| _resolve_workspace_root_argument | lexists | 103 | `os.path.lexists(requested)` |
| _resolve_workspace_root_argument | lstat | 105 | `requested.lstat(data not statically known)` |
| _resolve_workspace_root_argument | DocumentationIntegrityError | 107 | `DocumentationIntegrityError(...)` |
| _resolve_workspace_root_argument | bool | 110 | `bool(getattr(...))` |
| _resolve_workspace_root_argument | getattr | 110 | `getattr(entry_stat, 'st_reparse_tag', 0)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `result_path.read_bytes` | `record_documentation_agent_result` | 1018 |
| mutation | `run.validation_results.append` | `record_documentation_agent_result` | 1039 |
| mutation | `run.validation_results.append` | `record_documentation_agent_result` | 1100 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.abspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.fspath` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `Path(workspace).expanduser` | 102 |
| unresolved_call | `_resolve_workspace_root_argument` | `os.path.lexists` | 103 |
| unresolved_call | `_resolve_workspace_root_argument` | `requested.lstat` | 105 |
| unresolved_call | `_resolve_workspace_root_argument` | `getattr` | 110 |
| step_limit | `record_documentation_agent_result` | `first 12 steps` | 0 |
| truncated_flow | `record_documentation_agent_result` | `depth limit` | 0 |

## Behavior

This flow starts at `record_documentation_agent_result` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
