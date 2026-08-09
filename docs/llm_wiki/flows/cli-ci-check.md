# ci-check

**Entry point:** `run` (`cli`)
**Source:** [ci_check_cmd](../modules/ci_check_cmd.md)
**Modules touched:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [ci_check_cmd](../modules/ci_check_cmd.md), [common](../modules/common.md), [config](../modules/config.md), and 36 more

**Complete modules touched:**

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [ci_check_cmd](../modules/ci_check_cmd.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
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
- [metrics](../modules/metrics.md)
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
    participant p0 as run
    participant p1 as getattr
    participant p2 as Path
    participant p3 as bool
    participant p4 as validate_source_root
    participant p5 as validate_path
    participant p6 as PathValidationError
    participant p7 as resolve
    participant p8 as cwd
    participant p9 as relative_to
    participant p10 as expanduser
    participant p11 as is_absolute
    participant p12 as is_dir
    participant p13 as abspath
    participant p14 as windows_current_user_sid
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p2: Path
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p3: bool
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0->>p4: validate_source_root
    p4->>p5: validate_path
    p5->>p6: PathValidationError
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p9: relative_to
    p5->>p6: PathValidationError
    p4-->>p10: expanduser
    p4-->>p2: Path
    p4-->>p11: is_absolute
    p4-->>p8: cwd
    p4-->>p7: resolve
    p4->>p6: PathValidationError
    p4-->>p12: is_dir
    p4->>p6: PathValidationError
    p4-->>p2: Path
    p4-->>p13: abspath
    p4->>p14: windows_current_user_sid
```

> Call sequence diagram shows 30 of 2580 interactions; 2550 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. getattr"]
    s5["5. Path"]
    s6["6. getattr"]
    s7["7. getattr"]
    s8["8. getattr"]
    s9["9. bool"]
    s10["10. getattr"]
    s11["11. getattr"]
    s12["12. validate_source_root"]
    s1 -. "getattr(args, 'src_dir', '.')" .-> s2
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s3
    s1 -. "getattr(args, 'format', 'text')" .-> s4
    s1 -. "Path(getattr(...))" .-> s5
    s1 -. "getattr(args, 'report', DEFAULT_REPORT)" .-> s6
    s1 -. "getattr(args, 'helper_cache_dir', None)" .-> s7
    s1 -. "getattr(args, 'include_tests', None)" .-> s8
    s1 -. "bool(getattr(...))" .-> s9
    s1 -. "getattr(args, 'allow_external_src', False)" .-> s10
    s1 -. "getattr(args, 'source_selection', None)" .-> s11
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)"| s12
    b0["filesystem_write report_path.write_text"]
    s1 -. "filesystem_write report_path.write_text" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    click s1 "../modules/ci_check_cmd.md"
    click s12 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `DEFAULT_REPORT`, `print_extraction_job_plan`, `sys` | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `Path` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `bool` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 41 | `getattr(args, 'src_dir', '.')` |
| run | getattr | 42 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr | 43 | `getattr(args, 'format', 'text')` |
| run | Path | 44 | `Path(getattr(...))` |
| run | getattr | 44 | `getattr(args, 'report', DEFAULT_REPORT)` |
| run | getattr | 45 | `getattr(args, 'helper_cache_dir', None)` |
| run | getattr | 46 | `getattr(args, 'include_tests', None)` |
| run | bool | 47 | `bool(getattr(...))` |
| run | getattr | 47 | `getattr(args, 'allow_external_src', False)` |
| run | getattr | 48 | `getattr(args, 'source_selection', None)` |
| run | validate_source_root | 50 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_write | `report_path.write_text` | `run` | 77 |
| output | `print` | `run` | 79 |
| output | `print` | `run` | 80 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 41 |
| unresolved_call | `run` | `getattr` | 42 |
| unresolved_call | `run` | `getattr` | 43 |
| unresolved_call | `run` | `getattr` | 44 |
| unresolved_call | `run` | `getattr` | 45 |
| unresolved_call | `run` | `getattr` | 46 |
| unresolved_call | `run` | `getattr` | 47 |
| unresolved_call | `run` | `getattr` | 48 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Runs the lint report builder with strict validation unconditionally. It writes
a Markdown report to the requested artifact path, emits text, Markdown, or JSON
to the console, and records best-effort local metrics. The report is written
even when issues are found, then the command exits nonzero if the strict result
does not pass.
