# build_doctor_report

**Entry point:** `build_doctor_report` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), and 60 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [canonical_pages](../modules/canonical_pages.md)
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
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
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

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_doctor_report
    participant p1 as isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p2 as TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p3 as ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p4 as str (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p5 as validate_path
    participant p6 as validate_source_root
    participant p7 as build_report
    participant p8 as report_schema
    participant p9 as lint.health_details.to_payload
    participant p10 as compose_doctor_report
    participant p11 as PathValidationError
    participant p12 as isinstance (src/llm_wiki_cli/services…t_service.py:build_report)
    participant p13 as bool (src/llm_wiki_cli/services…tibility.py:report_schema)
    participant p14 as isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)
    participant p15 as (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p16 as Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    participant p17 as TypeError (src/llm_wiki_cli/services…t_service.py:build_report)
    participant p18 as details.get
    participant p19 as TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)
    participant p20 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(strict, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('strict must be a boolean')
    p0-->>p3: ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('report_schema must be auto, v1, v3 or v4')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(allow_external_src, bool)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('allow_external_src must be a boolean')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(parallel_jobs, bool)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(parallel_jobs, int)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('parallel_jobs must be an integer')
    p0-->>p3: ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('parallel_jobs must be greater than zero')
    p0-->>p4: str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(wiki_dir)
    p0-->>p4: str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(src_dir)
    p0->>p5: validate_path
    p0->>p6: validate_source_root
    p0-->>p4: str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(source_root)
    p0->>p7: build_report
    p0-->>p4: str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(helper_cache_dir)
    p0->>p8: report_schema
    p0-->>p9: lint.health_details.to_payload
    p0->>p10: compose_doctor_report
    p5->>p11: PathValidationError
    p6->>p5: validate_path
    p7-->>p12: isinstance (src/llm_wiki_cli/services…t_service.py:build_report)(include_health_details, bool)
    p8-->>p13: bool (src/llm_wiki_cli/services…tibility.py:report_schema)(...)
    p10-->>p14: isinstance (src/llm_wiki_cli/services….py:compose_doctor_report)(lint, LintReport)
    p5-->>p15: (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    p6-->>p16: Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    p7-->>p17: TypeError (src/llm_wiki_cli/services…t_service.py:build_report)('include_health_details must be a boolean')
    p8-->>p18: details.get('schema_version')
    p10-->>p19: TypeError (src/llm_wiki_cli/services….py:compose_doctor_report)('lint must be a LintReport')
    p5-->>p20: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
```

> Call sequence diagram shows 30 of 3069 interactions; 3039 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 921 (902 omitted); unresolved 4 of 1000 (996 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_path` | 13 | - | unresolved | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 13 | - | external | 1 |
| `src/llm_wiki_cli/config.py:validate_path` | 13 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 1 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 21 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 21 | - | unresolved | 4 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 21 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 6 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 21 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
| `src/llm_wiki_cli/services/filesystem_guard.py:windows_current_user_sid` | 33 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
> Omission summary shows 8 of 839 groups; 831 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_doctor_report"]
    s2["2. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s3["3. TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s4["4. ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s5["5. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s6["6. TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s7["7. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s8["8. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s9["9. TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s10["10. ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s11["11. str (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s12["12. str (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(strict, bool)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('strict must be a boolean')" .-> s3
    s1 -. "ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('report_schema must be auto, v1, v3 or v4')" .-> s4
    s1 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(allow_external_src, bool)" .-> s5
    s1 -. "TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('allow_external_src must be a boolean')" .-> s6
    s1 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(parallel_jobs, bool)" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(parallel_jobs, int)" .-> s8
    s1 -. "TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('parallel_jobs must be an integer')" .-> s9
    s1 -. "ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('parallel_jobs must be greater than zero')" .-> s10
    s1 -. "str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(wiki_dir)" .-> s11
    s1 -. "str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(src_dir)" .-> s12
    click s1 "../modules/doctor_service.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_doctor_report` | `wiki_dir: str \| Path`, `src_dir: str \| Path`, `strict: bool`, `allow_external_src: bool`, `helper_cache_dir: str \| Path \| None`, `include_tests: Iterable[str] \| None`, `parallel_jobs: int`, `job_request: ExtractionJobRequest \| None` | - | - | `compose_doctor_report(...)` |
| `isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `str (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `str (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 132 | `isinstance(strict, bool)` |
| build_doctor_report | TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 133 | `TypeError('strict must be a boolean')` |
| build_doctor_report | ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 135 | `ValueError('report_schema must be auto, v1, v3 or v4')` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 136 | `isinstance(allow_external_src, bool)` |
| build_doctor_report | TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 137 | `TypeError('allow_external_src must be a boolean')` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 138 | `isinstance(parallel_jobs, bool)` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 138 | `isinstance(parallel_jobs, int)` |
| build_doctor_report | TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 139 | `TypeError('parallel_jobs must be an integer')` |
| build_doctor_report | ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 141 | `ValueError('parallel_jobs must be greater than zero')` |
| build_doctor_report | str (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 143 | `str(wiki_dir)` |
| build_doctor_report | str (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 144 | `str(src_dir)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_doctor_report` | `isinstance` | 132 |
| external_call | `build_doctor_report` | `TypeError` | 133 |
| external_call | `build_doctor_report` | `ValueError` | 135 |
| external_call | `build_doctor_report` | `isinstance` | 136 |
| external_call | `build_doctor_report` | `TypeError` | 137 |
| external_call | `build_doctor_report` | `isinstance` | 138 |
| external_call | `build_doctor_report` | `TypeError` | 139 |
| external_call | `build_doctor_report` | `ValueError` | 141 |
| step_limit | `build_doctor_report` | `first 12 steps` | 0 |
| truncated_flow | `build_doctor_report` | `depth limit` | 0 |

## Behavior

This flow starts at `build_doctor_report` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
