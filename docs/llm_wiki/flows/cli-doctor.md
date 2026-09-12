# doctor

**Entry point:** `run` (`cli`)
**Source:** [doctor_cmd](../modules/doctor_cmd.md)
**Modules touched:** [capability_diagnostics](../modules/capability_diagnostics.md), [common](../modules/common.md), [config](../modules/config.md), [data_flow](../modules/data_flow.md), and 29 more

**Complete modules touched:**

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
- [immutable](../modules/immutable.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)
    participant p2 as build_capability_doctor
    participant p3 as build_capability_diagnostics
    participant p4 as validate_source_root
    participant p5 as validate_path
    participant p6 as PathValidationError
    participant p7 as (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p8 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p9 as Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    participant p10 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    participant p11 as Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    participant p12 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    participant p13 as candidate.is_absolute
    participant p14 as Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    participant p15 as candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    participant p16 as resolved.is_dir
    participant p17 as os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    participant p18 as windows_current_user_sid
    participant p19 as WindowsSecurityGuardError
    participant p20 as _current_windows_user_sid
    participant p21 as ctypes.WinDLL
    participant p22 as ctypes.POINTER
    participant p23 as wintypes.HANDLE
    p0-->>p1: getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)
    p0->>p2: build_capability_doctor
    p2->>p3: build_capability_diagnostics
    p3->>p4: validate_source_root
    p4->>p5: validate_path
    p5->>p6: PathValidationError
    p5-->>p7: (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    p5-->>p8: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p5-->>p9: Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)
    p5-->>p8: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p5-->>p10: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p5->>p6: PathValidationError
    p4-->>p11: Path(…).expanduser (src/llm_wiki_cli/config.py:validate_source_root)
    p4-->>p12: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p4-->>p13: candidate.is_absolute
    p4-->>p14: Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    p4-->>p15: candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p4->>p6: PathValidationError
    p4-->>p16: resolved.is_dir
    p4->>p6: PathValidationError
    p4-->>p12: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p4-->>p17: os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    p4->>p18: windows_current_user_sid
    p18->>p19: WindowsSecurityGuardError
    p18->>p20: _current_windows_user_sid
    p20-->>p21: ctypes.WinDLL
    p20-->>p21: ctypes.WinDLL
    p20-->>p22: ctypes.POINTER
    p20-->>p22: ctypes.POINTER
    p20-->>p23: wintypes.HANDLE
```

> Call sequence diagram shows 30 of 1162 interactions; 1132 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)"]
    s3["3. build_capability_doctor"]
    s4["4. build_capability_diagnostics"]
    s5["5. validate_source_root"]
    s6["6. validate_path"]
    s7["7. PathValidationError"]
    s8["8. (…).resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s10["10. Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s11["11. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s12["12. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run)(args, 'capabilities', False)" .-> s2
    s1 -->|"build_capability_doctor(…)"| s3
    s3 -->|"build_capability_diagnostics(src_dir, **=...)"| s4
    s4 -->|"validate_source_root(str(...), '--src-dir', allow_external=allow_external_src)"| s5
    s5 -->|"validate_path(path, label)"| s6
    s6 -->|"PathValidationError(...)"| s7
    s6 -. "(…).resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s6 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s9
    s6 -. "Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s10
    s6 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s11
    s6 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["environment_read os.environ.get"]
    s4 -. "environment_read os.environ.get" .-> b3
    b4["mutation providers.append"]
    s4 -. "mutation providers.append" .-> b4
    b5["mutation plugin_states.append"]
    s4 -. "mutation plugin_states.append" .-> b5
    b6["mutation plugin_states.append"]
    s4 -. "mutation plugin_states.append" .-> b6
    b7["mutation unsupported.append"]
    s4 -. "mutation unsupported.append" .-> b7
    click s1 "../modules/doctor_cmd.md"
    click s3 "../modules/capability_diagnostics.md"
    click s4 "../modules/capability_diagnostics.md"
    click s5 "../modules/config.md"
    click s6 "../modules/config.md"
    click s7 "../modules/config.md"
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
| `build_capability_doctor` | `wiki_dir`, `src_dir`, `kwargs` | `DOCTOR_CAPABILITY_VERSION` | - | `{...}` |
| `build_capability_diagnostics` | `src_dir`, `helper_cache_dir`, `source_selection`, `allow_external_src`, `include_tests` | `helpers`, `sys`, `_TOOL_HINTS`, `LANGUAGE_EXTENSIONS`, `sys` | `tools[...]` | `{...}` |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/doctor_cmd.py:run) | 13 | `getattr(args, 'capabilities', False)` |
| run | build_capability_doctor | 16 | `build_capability_doctor(args.wiki_dir, args.src_dir, strict=args.strict, allow_external_src=args.allow_external_src, helper_cache_dir=args.helper_cache_dir, source_selection=args.source_selection, include_tests=args.include_tests, parallel_jobs=args.jobs, job_request=extraction_job_request_from_args(...))` |
| build_capability_doctor | build_capability_diagnostics | 228 | `build_capability_diagnostics(src_dir, **=...)` |
| build_capability_diagnostics | validate_source_root | 40 | `validate_source_root(str(...), '--src-dir', allow_external=allow_external_src)` |
| validate_source_root | validate_path | 158 | `validate_path(path, label)` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | (…).resolve (src/llm_wiki_cli/config.py:validate_path) | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 133 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path) | 134 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 134 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 136 | `resolved.relative_to(cwd)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 21 |
| output | `print` | `run` | 38 |
| output | `print` | `run` | 40 |
| environment_read | `os.environ.get` | `build_capability_diagnostics` | 56 |
| mutation | `providers.append` | `build_capability_diagnostics` | 101 |
| mutation | `plugin_states.append` | `build_capability_diagnostics` | 167 |
| mutation | `plugin_states.append` | `build_capability_diagnostics` | 169 |
| mutation | `unsupported.append` | `build_capability_diagnostics` | 198 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 13 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 134 |
| external_call | `validate_path` | `Path.cwd` | 134 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 136 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
