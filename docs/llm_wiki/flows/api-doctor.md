# doctor

**Entry point:** `doctor` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [config](../modules/config.md), and 35 more

**Complete modules touched:**

- [api](../modules/api.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [doctor_service](../modules/doctor_service.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
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
- [progress](../modules/progress.md)
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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as doctor
    participant p1 as build_doctor_report
    participant p2 as isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p3 as TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p4 as ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p5 as str (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    participant p6 as validate_path
    participant p7 as PathValidationError
    participant p8 as (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p9 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p10 as Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p11 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    participant p12 as validate_source_root
    participant p13 as Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    participant p14 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    participant p15 as candidate.is_absolute
    participant p16 as Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    participant p17 as candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    participant p18 as resolved.is_dir
    p0->>p1: build_doctor_report
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p3: TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p3: TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p3: TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p4: ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p5: str (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1-->>p5: str (src/llm_wiki_cli/services…ce.py:build_doctor_report)
    p1->>p6: validate_path
    p6->>p7: PathValidationError
    p6-->>p8: (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    p6-->>p9: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p6-->>p10: Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    p6-->>p9: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p6-->>p11: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p6->>p7: PathValidationError
    p1->>p12: validate_source_root
    p12->>p6: validate_path
    p12-->>p13: Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    p12-->>p14: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p12-->>p15: candidate.is_absolute
    p12-->>p16: Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    p12-->>p17: candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p12->>p7: PathValidationError
    p12-->>p18: resolved.is_dir
    p12->>p7: PathValidationError
    p12-->>p14: Path (src/llm_wiki_cli/config.py:validate_source_root)
```

> Call sequence diagram shows 30 of 1479 interactions; 1449 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. doctor"]
    s2["2. build_doctor_report"]
    s3["3. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s4["4. TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s5["5. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s6["6. TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s7["7. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s8["8. isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s9["9. TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s10["10. ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s11["11. str (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s12["12. str (src/llm_wiki_cli/services…ce.py:build_doctor_report)"]
    s1 -->|"build_doctor_report(wiki_dir, src_dir, strict=strict, allow_external_src=allow_external_src, source_selection=source_selection)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(strict, bool)" .-> s3
    s2 -. "TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('strict must be a boolean')" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(allow_external_src, bool)" .-> s5
    s2 -. "TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('allow_external_src must be a boolean')" .-> s6
    s2 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(parallel_jobs, bool)" .-> s7
    s2 -. "isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)(parallel_jobs, int)" .-> s8
    s2 -. "TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('parallel_jobs must be an integer')" .-> s9
    s2 -. "ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report)('parallel_jobs must be greater than zero')" .-> s10
    s2 -. "str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(wiki_dir)" .-> s11
    s2 -. "str (src/llm_wiki_cli/services…ce.py:build_doctor_report)(src_dir)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/doctor_service.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `doctor` | `src_dir: str`, `wiki_dir: str`, `strict: bool`, `allow_external_src: bool`, `source_selection: str \| Path \| None` | `DoctorResult` | - | `cast(...)` |
| `build_doctor_report` | `wiki_dir: str \| Path`, `src_dir: str \| Path`, `strict: bool`, `allow_external_src: bool`, `helper_cache_dir: str \| Path \| None`, `include_tests: Iterable[str] \| None`, `parallel_jobs: int`, `job_request: ExtractionJobRequest \| None` | - | - | `compose_doctor_report(...)` |
| `isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report)` | - | - | - | - |
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
| doctor | build_doctor_report | 1114 | `build_doctor_report(wiki_dir, src_dir, strict=strict, allow_external_src=allow_external_src, source_selection=source_selection)` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 124 | `isinstance(strict, bool)` |
| build_doctor_report | TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 125 | `TypeError('strict must be a boolean')` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 126 | `isinstance(allow_external_src, bool)` |
| build_doctor_report | TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 127 | `TypeError('allow_external_src must be a boolean')` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 128 | `isinstance(parallel_jobs, bool)` |
| build_doctor_report | isinstance (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 128 | `isinstance(parallel_jobs, int)` |
| build_doctor_report | TypeError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 129 | `TypeError('parallel_jobs must be an integer')` |
| build_doctor_report | ValueError (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 131 | `ValueError('parallel_jobs must be greater than zero')` |
| build_doctor_report | str (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 133 | `str(wiki_dir)` |
| build_doctor_report | str (src/llm_wiki_cli/services…ce.py:build_doctor_report) | 134 | `str(src_dir)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_doctor_report` | `isinstance` | 124 |
| external_call | `build_doctor_report` | `TypeError` | 125 |
| external_call | `build_doctor_report` | `isinstance` | 126 |
| external_call | `build_doctor_report` | `TypeError` | 127 |
| external_call | `build_doctor_report` | `isinstance` | 128 |
| external_call | `build_doctor_report` | `TypeError` | 129 |
| external_call | `build_doctor_report` | `ValueError` | 131 |
| step_limit | `doctor` | `first 12 steps` | 0 |
| truncated_flow | `doctor` | `depth limit` | 0 |

## Behavior

This flow starts at `doctor` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
