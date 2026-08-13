# doctor

**Entry point:** `run` (`cli`)
**Source:** [doctor_cmd](../modules/doctor_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [config](../modules/config.md), [data_flow](../modules/data_flow.md), and 30 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [doctor_cmd](../modules/doctor_cmd.md)
- [doctor_service](../modules/doctor_service.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [lint_service](../modules/lint_service.md)
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
    participant p0 as run
    participant p1 as build_doctor_report
    participant p2 as isinstance
    participant p3 as TypeError
    participant p4 as ValueError
    participant p5 as str
    participant p6 as validate_path
    participant p7 as PathValidationError
    participant p8 as resolve
    participant p9 as cwd
    participant p10 as relative_to
    participant p11 as validate_source_root
    participant p12 as expanduser
    participant p13 as Path
    participant p14 as is_absolute
    participant p15 as is_dir
    p0->>p1: build_doctor_report
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1-->>p2: isinstance
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1-->>p4: ValueError
    p1-->>p5: str
    p1-->>p5: str
    p1->>p6: validate_path
    p6->>p7: PathValidationError
    p6-->>p8: resolve
    p6-->>p9: cwd
    p6-->>p8: resolve
    p6-->>p9: cwd
    p6-->>p10: relative_to
    p6->>p7: PathValidationError
    p1->>p11: validate_source_root
    p11->>p6: validate_path
    p11-->>p12: expanduser
    p11-->>p13: Path
    p11-->>p14: is_absolute
    p11-->>p9: cwd
    p11-->>p8: resolve
    p11->>p7: PathValidationError
    p11-->>p15: is_dir
    p11->>p7: PathValidationError
    p11-->>p13: Path
```

> Call sequence diagram shows 30 of 1415 interactions; 1385 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. build_doctor_report"]
    s3["3. isinstance"]
    s4["4. TypeError"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. isinstance"]
    s8["8. isinstance"]
    s9["9. TypeError"]
    s10["10. ValueError"]
    s11["11. str"]
    s12["12. str"]
    s1 -->|"build_doctor_report(getattr(...), getattr(...), strict=bool(...), allow_external_src=bool(...), helper_cache_dir=getattr(...), include_tests=getattr(...), para…"| s2
    s2 -. "isinstance(strict, bool)" .-> s3
    s2 -. "TypeError('strict must be a boolean')" .-> s4
    s2 -. "isinstance(allow_external_src, bool)" .-> s5
    s2 -. "TypeError('allow_external_src must be a boolean')" .-> s6
    s2 -. "isinstance(parallel_jobs, bool)" .-> s7
    s2 -. "isinstance(parallel_jobs, int)" .-> s8
    s2 -. "TypeError('parallel_jobs must be an integer')" .-> s9
    s2 -. "ValueError('parallel_jobs must be greater than zero')" .-> s10
    s2 -. "str(wiki_dir)" .-> s11
    s2 -. "str(src_dir)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    click s1 "../modules/doctor_cmd.md"
    click s2 "../modules/doctor_service.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR` | - | - |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | build_doctor_report | 13 | `build_doctor_report(getattr(...), getattr(...), strict=bool(...), allow_external_src=bool(...), helper_cache_dir=getattr(...), include_tests=getattr(...), parallel_jobs=getattr(...), job_request=extraction_job_request_from_args(...), source_selection=getattr(...))` |
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

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 25 |
| output | `print` | `run` | 27 |

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
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
