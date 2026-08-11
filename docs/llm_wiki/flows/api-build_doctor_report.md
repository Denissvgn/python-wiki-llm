# build_doctor_report

**Entry point:** `build_doctor_report` (`api`)
**Source:** [doctor_service](../modules/doctor_service.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [config](../modules/config.md), [data_flow](../modules/data_flow.md), and 35 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [doctor_service](../modules/doctor_service.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
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
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis](../modules/sync_analysis.md)
- [team](../modules/team.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_doctor_report
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as ValueError
    participant p4 as str
    participant p5 as validate_path
    participant p6 as PathValidationError
    participant p7 as resolve
    participant p8 as cwd
    participant p9 as relative_to
    participant p10 as validate_source_root
    participant p11 as expanduser
    participant p12 as Path
    participant p13 as is_absolute
    participant p14 as is_dir
    participant p15 as abspath
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: ValueError
    p0-->>p4: str
    p0-->>p4: str
    p0->>p5: validate_path
    p5->>p6: PathValidationError
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p9: relative_to
    p5->>p6: PathValidationError
    p0->>p10: validate_source_root
    p10->>p5: validate_path
    p10-->>p11: expanduser
    p10-->>p12: Path
    p10-->>p13: is_absolute
    p10-->>p8: cwd
    p10-->>p7: resolve
    p10->>p6: PathValidationError
    p10-->>p14: is_dir
    p10->>p6: PathValidationError
    p10-->>p12: Path
    p10-->>p15: abspath
```

> Call sequence diagram shows 30 of 2486 interactions; 2456 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_doctor_report"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. isinstance"]
    s7["7. isinstance"]
    s8["8. TypeError"]
    s9["9. ValueError"]
    s10["10. str"]
    s11["11. str"]
    s12["12. validate_path"]
    s1 -. "isinstance(strict, bool)" .-> s2
    s1 -. "TypeError('strict must be a boolean')" .-> s3
    s1 -. "isinstance(allow_external_src, bool)" .-> s4
    s1 -. "TypeError('allow_external_src must be a boolean')" .-> s5
    s1 -. "isinstance(parallel_jobs, bool)" .-> s6
    s1 -. "isinstance(parallel_jobs, int)" .-> s7
    s1 -. "TypeError('parallel_jobs must be an integer')" .-> s8
    s1 -. "ValueError('parallel_jobs must be greater than zero')" .-> s9
    s1 -. "str(wiki_dir)" .-> s10
    s1 -. "str(src_dir)" .-> s11
    s1 -->|"validate_path(wiki_text, '--wiki-dir')"| s12
    click s1 "../modules/doctor_service.md"
    click s12 "../modules/config.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_doctor_report` | `wiki_dir: str \| Path`, `src_dir: str \| Path`, `strict: bool`, `allow_external_src: bool`, `helper_cache_dir: str \| Path \| None`, `include_tests: Iterable[str] \| None`, `parallel_jobs: int`, `job_request: ExtractionJobRequest \| None` | - | - | `compose_doctor_report(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `str` | - | - | - | - |
| `str` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_doctor_report | isinstance | 124 | `isinstance(strict, bool)` |
| build_doctor_report | TypeError | 125 | `TypeError('strict must be a boolean')` |
| build_doctor_report | isinstance | 126 | `isinstance(allow_external_src, bool)` |
| build_doctor_report | TypeError | 127 | `TypeError('allow_external_src must be a boolean')` |
| build_doctor_report | isinstance | 128 | `isinstance(parallel_jobs, bool)` |
| build_doctor_report | isinstance | 128 | `isinstance(parallel_jobs, int)` |
| build_doctor_report | TypeError | 129 | `TypeError('parallel_jobs must be an integer')` |
| build_doctor_report | ValueError | 131 | `ValueError('parallel_jobs must be greater than zero')` |
| build_doctor_report | str | 133 | `str(wiki_dir)` |
| build_doctor_report | str | 134 | `str(src_dir)` |
| build_doctor_report | validate_path | 135 | `validate_path(wiki_text, '--wiki-dir')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_doctor_report` | `isinstance` | 124 |
| unresolved_call | `build_doctor_report` | `TypeError` | 125 |
| unresolved_call | `build_doctor_report` | `isinstance` | 126 |
| unresolved_call | `build_doctor_report` | `TypeError` | 127 |
| unresolved_call | `build_doctor_report` | `isinstance` | 128 |
| unresolved_call | `build_doctor_report` | `TypeError` | 129 |
| unresolved_call | `build_doctor_report` | `ValueError` | 131 |
| step_limit | `build_doctor_report` | `first 12 steps` | 0 |
| truncated_flow | `build_doctor_report` | `depth limit` | 0 |

## Behavior

This flow starts at `build_doctor_report` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
