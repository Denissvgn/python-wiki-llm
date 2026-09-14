# queue

**Entry point:** `run` (`cli`)
**Source:** [queue_cmd](../modules/queue_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [change_selection](../modules/change_selection.md), [common](../modules/common.md), [config](../modules/config.md), and 50 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [change_selection](../modules/change_selection.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [documentation_worklist](../modules/documentation_worklist.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [immutable](../modules/immutable.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
- [maintenance_queue](../modules/maintenance_queue.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)
- [queue_cmd](../modules/queue_cmd.md)
- [runtime_output](../modules/runtime_output.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as build_maintenance_queue
    participant p2 as isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)
    participant p3 as ValueError (src/llm_wiki_cli/services…y:build_maintenance_queue)
    participant p4 as capture_context_read
    participant p5 as isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p6 as TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p7 as callable (src/llm_wiki_cli/services…t.py:capture_context_read)
    participant p8 as validate_source_root
    participant p9 as validate_path
    participant p10 as PathValidationError
    participant p11 as (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p12 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p13 as Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p14 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    participant p15 as Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    participant p16 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    participant p17 as candidate.is_absolute
    participant p18 as Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    participant p19 as candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p0->>p1: build_maintenance_queue
    p1-->>p2: isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)
    p1-->>p2: isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)
    p1-->>p3: ValueError (src/llm_wiki_cli/services…y:build_maintenance_queue)
    p1->>p4: capture_context_read
    p4-->>p5: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p6: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p5: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p6: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p7: callable (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p6: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p5: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p6: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p5: isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4-->>p6: TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)
    p4->>p8: validate_source_root
    p8->>p9: validate_path
    p9->>p10: PathValidationError
    p9-->>p11: (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    p9-->>p12: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p9-->>p13: Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    p9-->>p12: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p9-->>p14: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p9->>p10: PathValidationError
    p8-->>p15: Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    p8-->>p16: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p8-->>p17: candidate.is_absolute
    p8-->>p18: Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    p8-->>p19: candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p8->>p10: PathValidationError
```

> Call sequence diagram shows 30 of 3388 interactions; 3358 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. build_maintenance_queue"]
    s3["3. isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)"]
    s4["4. isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)"]
    s5["5. ValueError (src/llm_wiki_cli/services…y:build_maintenance_queue)"]
    s6["6. capture_context_read"]
    s7["7. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s8["8. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s9["9. isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s10["10. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s11["11. callable (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s12["12. TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)"]
    s1 -->|"build_maintenance_queue(…)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)(limit, bool)" .-> s3
    s2 -. "isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)(limit, int)" .-> s4
    s2 -. "ValueError (src/llm_wiki_cli/services…y:build_maintenance_queue)('Queue limit must be between 1 and 1000')" .-> s5
    s2 -->|"capture_context_read(…)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(read_only, bool)" .-> s7
    s6 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('read_only must be a boolean')" .-> s8
    s6 -. "isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)(allow_external_src, bool)" .-> s9
    s6 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('allow_external_src must be a boolean')" .-> s10
    s6 -. "callable (src/llm_wiki_cli/services…t.py:capture_context_read)(plan_reporter)" .-> s11
    s6 -. "TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)('plan_reporter must be callable or None')" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["mutation global_issues.append"]
    s2 -. "mutation global_issues.append" .-> b1
    click s1 "../modules/queue_cmd.md"
    click s2 "../modules/maintenance_queue.md"
    click s6 "../modules/context_packet.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | - | - | - |
| `build_maintenance_queue` | `src_dir`, `wiki_dir`, `limit`, `allow_external_src`, `source_selection`, `helper_cache_dir` | - | `result[...]`, `result[...]`, `result[...]` | `result` |
| `isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…y:build_maintenance_queue)` | - | - | - | - |
| `capture_context_read` | `src_dir: str`, `wiki_dir: str`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None`, `allow_selection_mismatch: bool` | `PathValidationError`, `DocumentationQueryError`, `context_service`, `InventoryResult`, `SourceSnapshot`, `DocumentationQueryError`, `DocumentationQueryError`, `wiki_surface` | - | `CapturedContextRead(...)` |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `callable (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:capture_context_read)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | build_maintenance_queue | 9 | `build_maintenance_queue(args.src_dir, args.wiki_dir, limit=args.limit, allow_external_src=args.allow_external_src, source_selection=args.source_selection, helper_cache_dir=args.helper_cache_dir)` |
| build_maintenance_queue | isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue) | 175 | `isinstance(limit, bool)` |
| build_maintenance_queue | isinstance (src/llm_wiki_cli/services…y:build_maintenance_queue) | 175 | `isinstance(limit, int)` |
| build_maintenance_queue | ValueError (src/llm_wiki_cli/services…y:build_maintenance_queue) | 176 | `ValueError('Queue limit must be between 1 and 1000')` |
| build_maintenance_queue | capture_context_read | 177 | `capture_context_read(src_dir, wiki_dir, allow_external_src=allow_external_src, read_only=True, strict_wiki_symlinks=True, allow_selection_mismatch=True, source_selection=source_selection, helper_cache_dir=helper_cache_dir)` |
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 703 | `isinstance(read_only, bool)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 704 | `TypeError('read_only must be a boolean')` |
| capture_context_read | isinstance (src/llm_wiki_cli/services…t.py:capture_context_read) | 705 | `isinstance(allow_external_src, bool)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 706 | `TypeError('allow_external_src must be a boolean')` |
| capture_context_read | callable (src/llm_wiki_cli/services…t.py:capture_context_read) | 707 | `callable(plan_reporter)` |
| capture_context_read | TypeError (src/llm_wiki_cli/services…t.py:capture_context_read) | 708 | `TypeError('plan_reporter must be callable or None')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 17 |
| mutation | `global_issues.append` | `build_maintenance_queue` | 233 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_maintenance_queue` | `isinstance` | 175 |
| external_call | `build_maintenance_queue` | `ValueError` | 176 |
| external_call | `capture_context_read` | `isinstance` | 703 |
| external_call | `capture_context_read` | `TypeError` | 704 |
| external_call | `capture_context_read` | `isinstance` | 705 |
| external_call | `capture_context_read` | `TypeError` | 706 |
| external_call | `capture_context_read` | `callable` | 707 |
| external_call | `capture_context_read` | `TypeError` | 708 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
