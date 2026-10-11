# ci-check

**Entry point:** `run` (`cli`)
**Source:** [ci_check_cmd](../modules/ci_check_cmd.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), and 68 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [canonical_pages](../modules/canonical_pages.md)
- [ci_check_cmd](../modules/ci_check_cmd.md)
- [ci_report](../modules/ci_report.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [doctor_service](../modules/doctor_service.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [health_contract](../modules/health_contract.md)
- [health_details](../modules/health_details.md)
- [health_policy](../modules/health_policy.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
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
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [metrics](../modules/metrics.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_contracts](../modules/python_contracts.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [python_observations](../modules/python_observations.md)
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
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)
    participant p2 as RuntimeOutputError
    participant p3 as bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)
    participant p4 as validate_source_root
    participant p5 as str (src/llm_wiki_cli/commands/ci_check_cmd.py:run)
    participant p6 as validate_path
    participant p7 as cache_options_from_args
    participant p8 as _report_destination
    participant p9 as prepare_cache_options
    participant p10 as replace (src/llm_wiki_cli/commands/ci_check_cmd.py:run)
    participant p11 as time.monotonic
    participant p12 as extraction_job_request_from_args
    participant p13 as build_report
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'storage_git_base', None)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'storage_git_head', None)
    p0->>p2: RuntimeOutputError
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'src_dir', '.')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'format', 'text')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'report_schema', 'auto')
    p0->>p2: RuntimeOutputError
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'helper_cache_dir', None)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'include_tests', None)
    p0-->>p3: bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(getattr(...))
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'allow_external_src', False)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'source_selection', None)
    p0->>p4: validate_source_root
    p0-->>p5: str (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(src_root)
    p0->>p6: validate_path
    p0->>p7: cache_options_from_args
    p0->>p8: _report_destination
    p0->>p9: prepare_cache_options
    p0-->>p10: replace (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(cache_options, stats_enabled=True)
    p0-->>p11: time.monotonic
    p0->>p12: extraction_job_request_from_args
    p0->>p13: build_report
    p0-->>p3: bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(getattr(...))
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'knowledge_drift_report', False)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'jobs', 1)
    p0-->>p3: bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(getattr(...))
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'no_plugins', False)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'comparison_policy', 'auto')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'storage_check', False)
```

> Call sequence diagram shows 30 of 4323 interactions; 4293 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 21 of 1328 (1307 omitted); unresolved 0 of 1300 (1300 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_source_root` | 15 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 7 |
| `src/llm_wiki_cli/config.py:validate_path` | 16 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 16 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 16 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 15 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 15 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 15 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
| `src/llm_wiki_cli/services/filesystem_guard.py:windows_current_user_sid` | 34 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
> Omission summary shows 8 of 1106 groups; 1098 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s3["3. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s4["4. RuntimeOutputError"]
    s5["5. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s6["6. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s7["7. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s8["8. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s9["9. RuntimeOutputError"]
    s10["10. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s11["11. getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s12["12. bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'storage_git_base', None)" .-> s2
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'storage_git_head', None)" .-> s3
    s1 -->|"RuntimeOutputError('Storage Git checks require both --storage-git-base and --storage-git-head')"| s4
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'src_dir', '.')" .-> s5
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s6
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'format', 'text')" .-> s7
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'report_schema', 'auto')" .-> s8
    s1 -->|"RuntimeOutputError('--report-schema must be v1, v2 or v3')"| s9
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'helper_cache_dir', None)" .-> s10
    s1 -. "getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(args, 'include_tests', None)" .-> s11
    s1 -. "bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)(getattr(...))" .-> s12
    b0["mutation report.issues.append"]
    s1 -. "mutation report.issues.append" .-> b0
    b1["mutation report.issues.append"]
    s1 -. "mutation report.issues.append" .-> b1
    b2["mutation report.diagnostics.append"]
    s1 -. "mutation report.diagnostics.append" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    click s1 "../modules/ci_check_cmd.md"
    click s4 "../modules/runtime_output.md"
    click s9 "../modules/runtime_output.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `print_extraction_job_plan`, `sys`, `sys` | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `RuntimeOutputError` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `RuntimeOutputError` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |
| `bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 98 | `getattr(args, 'storage_git_base', None)` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 99 | `getattr(args, 'storage_git_head', None)` |
| run | RuntimeOutputError | 101 | `RuntimeOutputError('Storage Git checks require both --storage-git-base and --storage-git-head')` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 102 | `getattr(args, 'src_dir', '.')` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 103 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 104 | `getattr(args, 'format', 'text')` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 105 | `getattr(args, 'report_schema', 'auto')` |
| run | RuntimeOutputError | 107 | `RuntimeOutputError('--report-schema must be v1, v2 or v3')` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 108 | `getattr(args, 'helper_cache_dir', None)` |
| run | getattr (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 109 | `getattr(args, 'include_tests', None)` |
| run | bool (src/llm_wiki_cli/commands/ci_check_cmd.py:run) | 110 | `bool(getattr(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `report.issues.append` | `run` | 152 |
| mutation | `report.issues.append` | `run` | 155 |
| mutation | `report.diagnostics.append` | `run` | 158 |
| output | `print` | `run` | 183 |
| output | `print` | `run` | 197 |
| output | `print` | `run` | 204 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 98 |
| external_call | `run` | `getattr` | 99 |
| external_call | `run` | `getattr` | 102 |
| external_call | `run` | `getattr` | 103 |
| external_call | `run` | `getattr` | 104 |
| external_call | `run` | `getattr` | 105 |
| external_call | `run` | `getattr` | 108 |
| external_call | `run` | `getattr` | 109 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Runs strict validation unconditionally and emits text, Markdown or JSON to the console. By default it attempts a Markdown report, or uses an explicit `--report` destination; `--no-report` suppresses that artifact without disabling checks. A selected report is attempted even when validation finds issues. Blocking check findings or a required explicit report-write failure cause a nonzero exit; local metrics remain best effort.
