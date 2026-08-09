# bootstrap

**Entry point:** `run` (`cli`)
**Source:** [bootstrap_runtime](../modules/bootstrap_runtime.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), [common](../modules/common.md), and 39 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [diagrams](../modules/diagrams.md)
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
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [markdown_sections](../modules/markdown_sections.md)
- [module_maps](../modules/module_maps.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [relationships](../modules/relationships.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [services_schema](../modules/services_schema.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _bootstrap_run_options_from_args
    participant p2 as Path
    participant p3 as validate_path
    participant p4 as PathValidationError
    participant p5 as resolve
    participant p6 as cwd
    participant p7 as relative_to
    participant p8 as str
    participant p9 as validate_source_root
    participant p10 as expanduser
    participant p11 as is_absolute
    participant p12 as is_dir
    participant p13 as abspath
    participant p14 as windows_current_user_sid
    participant p15 as WindowsSecurityGuardError
    participant p16 as _current_windows_user_sid
    participant p17 as WinDLL
    participant p18 as POINTER
    p0->>p1: _bootstrap_run_options_from_args
    p1-->>p2: Path
    p1->>p3: validate_path
    p3->>p4: PathValidationError
    p3-->>p5: resolve
    p3-->>p6: cwd
    p3-->>p5: resolve
    p3-->>p6: cwd
    p3-->>p7: relative_to
    p3->>p4: PathValidationError
    p1-->>p8: str
    p1->>p9: validate_source_root
    p9->>p3: validate_path
    p9-->>p10: expanduser
    p9-->>p2: Path
    p9-->>p11: is_absolute
    p9-->>p6: cwd
    p9-->>p5: resolve
    p9->>p4: PathValidationError
    p9-->>p12: is_dir
    p9->>p4: PathValidationError
    p9-->>p2: Path
    p9-->>p13: abspath
    p9->>p14: windows_current_user_sid
    p14->>p15: WindowsSecurityGuardError
    p14->>p16: _current_windows_user_sid
    p16-->>p17: WinDLL
    p16-->>p17: WinDLL
    p16-->>p18: POINTER
    p16-->>p18: POINTER
```

> Call sequence diagram shows 30 of 4058 interactions; 4028 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _bootstrap_run_options_from_args"]
    s3["3. Path"]
    s4["4. validate_path"]
    s5["5. PathValidationError"]
    s6["6. resolve"]
    s7["7. cwd"]
    s8["8. resolve"]
    s9["9. cwd"]
    s10["10. relative_to"]
    s11["11. PathValidationError"]
    s12["12. str"]
    s1 -->|"_bootstrap_run_options_from_args(args)"| s2
    s2 -. "Path(args.wiki_dir)" .-> s3
    s2 -->|"validate_path(str(...), '--wiki-dir')"| s4
    s4 -->|"PathValidationError(...)"| s5
    s4 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s6
    s4 -. "Path.cwd(data not statically known)" .-> s7
    s4 -. "Path.cwd().resolve(data not statically known)" .-> s8
    s4 -. "Path.cwd(data not statically known)" .-> s9
    s4 -. "resolved.relative_to(cwd)" .-> s10
    s4 -->|"PathValidationError(...)"| s11
    s2 -. "str(wiki_dir)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    click s1 "../modules/bootstrap_runtime.md"
    click s2 "../modules/bootstrap_runtime.md"
    click s4 "../modules/config.md"
    click s5 "../modules/config.md"
    click s11 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `BootstrapExtractionError`, `BootstrapContractError`, `options.progress_stream` | - | - |
| `_bootstrap_run_options_from_args` | `args` | `sys` | - | `_BootstrapRunOptions(...)` |
| `Path` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `str` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _bootstrap_run_options_from_args | 6058 | `_bootstrap_run_options_from_args(args)` |
| _bootstrap_run_options_from_args | Path | 4189 | `Path(args.wiki_dir)` |
| _bootstrap_run_options_from_args | validate_path | 4190 | `validate_path(str(...), '--wiki-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 134 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 136 | `PathValidationError(...)` |
| _bootstrap_run_options_from_args | str | 4190 | `str(wiki_dir)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 6064 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 134 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Validates first-use options and the source/wiki boundaries, then delegates to
the deterministic bootstrap service. The target must be empty or the untouched
init scaffold; existing managed or custom content is rejected before
extraction. A successful run writes the selected wiki surfaces and consistent
generated artifacts, then prints either progress text or the structured
bootstrap result.
