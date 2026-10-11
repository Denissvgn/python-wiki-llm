# doctor

**Entry point:** `run` (`cli`)
**Source:** [doctor_cmd](../modules/doctor_cmd.md)
**Modules touched:** [analysis_compatibility](../modules/analysis_compatibility.md), [capability_diagnostics](../modules/capability_diagnostics.md), [common](../modules/common.md), [config](../modules/config.md), and 38 more

**Complete modules touched:**

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [capability_diagnostics](../modules/capability_diagnostics.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [doctor_cmd](../modules/doctor_cmd.md)
- [doctor_service](../modules/doctor_service.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [health_contract](../modules/health_contract.md)
- [health_details](../modules/health_details.md)
- [health_policy](../modules/health_policy.md)
- [health_summary](../modules/health_summary.md)
- [immutable](../modules/immutable.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [runtime_output](../modules/runtime_output.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as build_capability_doctor
    participant p2 as extraction_job_request_from_args
    participant p3 as render_capability_doctor
    participant p4 as render_doctor_text
    participant p5 as build_doctor_report
    participant p6 as build_capability_diagnostics
    participant p7 as _render_doctor_payload
    participant p8 as validate_source_root
    participant p9 as build_source_snapshot
    participant p10 as resolve_helper_cache_root
    participant p11 as get_prepared_typescript_root
    participant p12 as get_prepared_binary
    participant p13 as helper_preparation_argv
    participant p14 as build_report
    participant p15 as detailed_health_rows
    participant p16 as compose_doctor_report
    participant p17 as read_lock
    participant p18 as validate_plugin
    participant p19 as plugin_store
    participant p20 as validate_path
    participant p21 as _validate_capture_options
    participant p22 as lock_path
    participant p23 as _manifest_root
    participant p24 as _manifest_current
    participant p25 as _ensure_no_reserved_plugin_sources
    participant p26 as _resolve_snapshot_selection
    participant p27 as _normalize_only_files
    participant p28 as _new_lint_report
    participant p29 as getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)
    participant p30 as report.to_payload (src/llm_wiki_cli/commands/doctor_cmd.py:run)
    p0->>p1: build_capability_doctor
    p0->>p2: extraction_job_request_from_args
    p0->>p3: render_capability_doctor
    p0->>p4: render_doctor_text
    p0->>p5: build_doctor_report
    p1->>p6: build_capability_diagnostics
    p3->>p7: _render_doctor_payload
    p6->>p8: validate_source_root
    p6->>p9: build_source_snapshot
    p6->>p10: resolve_helper_cache_root
    p6->>p11: get_prepared_typescript_root
    p6->>p12: get_prepared_binary
    p6->>p13: helper_preparation_argv
    p5->>p14: build_report
    p7->>p15: detailed_health_rows
    p5->>p16: compose_doctor_report
    p6->>p17: read_lock
    p6->>p18: validate_plugin
    p6->>p19: plugin_store
    p8->>p20: validate_path
    p9->>p21: _validate_capture_options
    p17->>p22: lock_path
    p18->>p23: _manifest_root
    p11->>p24: _manifest_current
    p18->>p25: _ensure_no_reserved_plugin_sources
    p9->>p26: _resolve_snapshot_selection
    p9->>p27: _normalize_only_files
    p14->>p28: _new_lint_report
    p0-->>p29: getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)(args, 'report_schema', 'auto')
    p0-->>p30: report.to_payload (src/llm_wiki_cli/commands/doctor_cmd.py:run)(report_schema=report_schema)
```

> Call sequence diagram shows 30 of 1348 interactions; 1318 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 404 (403 omitted); unresolved 1 of 412 (411 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/commands/doctor_cmd.py:run` | 1 | - | external | 22 |
| `src/llm_wiki_cli/config.py:validate_path` | 9 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 9 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 9 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 8 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 8 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 8 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 6 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 8 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
> Omission summary shows 8 of 365 groups; 357 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)"]
    s3["3. ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run)"]
    s4["4. getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)"]
    s5["5. ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run)"]
    s6["6. build_capability_doctor"]
    s7["7. build_capability_diagnostics"]
    s8["8. validate_source_root"]
    s9["9. validate_path"]
    s10["10. PathValidationError"]
    s11["11. (…).resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s12["12. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)(args, 'report_schema', 'auto')" .-> s2
    s1 -. "ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run)('--report-schema must be v1 or v3')" .-> s3
    s1 -. "getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)(args, 'capabilities', False)" .-> s4
    s1 -. "ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run)('--capabilities and --report-schema are mutually exclusive')" .-> s5
    s1 -->|"build_capability_doctor(…)"| s6
    s6 -->|"build_capability_diagnostics(src_dir, **=...)"| s7
    s7 -->|"validate_source_root(str(...), '--src-dir', allow_external=allow_external_src)"| s8
    s8 -->|"validate_path(path, label)"| s9
    s9 -->|"PathValidationError(...)"| s10
    s9 -. "(…).resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s11
    s9 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["mutation argv.append"]
    s6 -. "mutation argv.append" .-> b3
    b4["mutation argv.extend"]
    s6 -. "mutation argv.extend" .-> b4
    b5["mutation argv.extend"]
    s6 -. "mutation argv.extend" .-> b5
    b6["mutation providers.append"]
    s7 -. "mutation providers.append" .-> b6
    b7["mutation plugin_states.append"]
    s7 -. "mutation plugin_states.append" .-> b7
    click s1 "../modules/doctor_cmd.md"
    click s6 "../modules/capability_diagnostics.md"
    click s7 "../modules/capability_diagnostics.md"
    click s8 "../modules/config.md"
    click s9 "../modules/config.md"
    click s10 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR` | - | `none` |
| `getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run)` | - | - | - | - |
| `build_capability_doctor` | `wiki_dir`, `src_dir`, `kwargs` | `sys`, `DOCTOR_CAPABILITY_VERSION` | - | `{...}` |
| `build_capability_diagnostics` | `src_dir`, `helper_cache_dir`, `source_selection`, `allow_external_src`, `include_tests` | `helpers`, `_LANGUAGE_LABELS`, `sys`, `helpers`, `LANGUAGE_EXTENSIONS`, `sys` | `tools[...]` | `{...}` |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run) | 13 | `getattr(args, 'report_schema', 'auto')` |
| run | ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run) | 15 | `ValueError('--report-schema must be v1 or v3')` |
| run | getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run) | 16 | `getattr(args, 'capabilities', False)` |
| run | ValueError (src/llm_wiki_cli/commands/doctor_cmd.py:run) | 18 | `ValueError('--capabilities and --report-schema are mutually exclusive')` |
| run | build_capability_doctor | 21 | `build_capability_doctor(args.wiki_dir, args.src_dir, strict=args.strict, allow_external_src=args.allow_external_src, helper_cache_dir=args.helper_cache_dir, source_selection=args.source_selection, include_tests=args.include_tests, parallel_jobs=args.jobs, job_request=extraction_job_request_from_args(...))` |
| build_capability_doctor | build_capability_diagnostics | 236 | `build_capability_diagnostics(src_dir, **=...)` |
| build_capability_diagnostics | validate_source_root | 41 | `validate_source_root(str(...), '--src-dir', allow_external=allow_external_src)` |
| validate_source_root | validate_path | 160 | `validate_path(path, label)` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve (src/llm_wiki_cli/config.py:validate_path) | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 26 |
| output | `print` | `run` | 45 |
| output | `print` | `run` | 47 |
| mutation | `argv.append` | `build_capability_doctor` | 270 |
| mutation | `argv.extend` | `build_capability_doctor` | 272 |
| mutation | `argv.extend` | `build_capability_doctor` | 274 |
| mutation | `providers.append` | `build_capability_diagnostics` | 126 |
| mutation | `plugin_states.append` | `build_capability_diagnostics` | 193 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 13 |
| external_call | `run` | `ValueError` | 15 |
| external_call | `run` | `getattr` | 16 |
| external_call | `run` | `ValueError` | 18 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
