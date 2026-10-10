# bootstrap

**Entry point:** `run` (`cli`)
**Source:** [bootstrap_runtime](../modules/bootstrap_runtime.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), [common](../modules/common.md), and 38 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [flow_overview](../modules/flow_overview.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [module_maps](../modules/module_maps.md)
- [paths](../modules/paths.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)
- [relationships](../modules/relationships.md)
- [services_dependencies](../modules/services_dependencies.md)
- [services_schema](../modules/services_schema.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as _bootstrap_run_options_from_args
    participant p2 as _execute_bootstrap_options
    participant p3 as SystemExit
    participant p4 as print (src/llm_wiki_cli/services/bootstrap_runtime.py:run)
    participant p5 as Path (src/llm_wiki_cli/services…rap_run_options_from_args)
    participant p6 as guard_maintenance_owner
    participant p7 as validate_path
    participant p8 as _preflight_public_bootstrap
    participant p9 as str (src/llm_wiki_cli/services…rap_run_options_from_args)
    participant p10 as validate_source_root
    participant p11 as _preflight_bootstrap_source_selection
    participant p12 as getattr (src/llm_wiki_cli/services…rap_run_options_from_args)
    participant p13 as maintenance_write_operation
    participant p14 as _execute_bootstrap_options_locked
    participant p15 as bool (src/llm_wiki_cli/services…rap_run_options_from_args)
    participant p16 as _BootstrapRunOptions
    p0->>p1: _bootstrap_run_options_from_args
    p0->>p2: _execute_bootstrap_options
    p0-->>p3: SystemExit(1)
    p0-->>p4: print (src/llm_wiki_cli/services/bootstrap_runtime.py:run)(..., file=sys.stderr)
    p0-->>p3: SystemExit(2)
    p1-->>p5: Path (src/llm_wiki_cli/services…rap_run_options_from_args)(args.wiki_dir)
    p2->>p6: guard_maintenance_owner
    p1->>p7: validate_path
    p2->>p8: _preflight_public_bootstrap
    p1-->>p9: str (src/llm_wiki_cli/services…rap_run_options_from_args)(wiki_dir)
    p2->>p8: _preflight_public_bootstrap
    p1->>p10: validate_source_root
    p2->>p11: _preflight_bootstrap_source_selection
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'allow_external_src', False)
    p2->>p13: maintenance_write_operation
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'openapi_file', None)
    p2->>p14: _execute_bootstrap_options_locked
    p1-->>p15: bool (src/llm_wiki_cli/services…rap_run_options_from_args)(...)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'api_contracts', False)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'depth', 'full')
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'format', 'text')
    p1->>p16: _BootstrapRunOptions
    p1-->>p9: str (src/llm_wiki_cli/services…rap_run_options_from_args)(src_root)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'skip_workflows', False)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'skip_flows', False)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'skip_data_flow', False)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'skip_dependencies', False)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'dependency_graph_detail', 'auto')
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'source_adapter', False)
    p1-->>p12: getattr (src/llm_wiki_cli/services…rap_run_options_from_args)(args, 'helper_cache_dir', None)
```

> Call sequence diagram shows 30 of 2909 interactions; 2879 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 961 (942 omitted); unresolved 0 of 881 (881 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_path` | 4 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 4 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 4 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 7 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 13 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
| `src/llm_wiki_cli/services/filesystem_guard.py:windows_current_user_sid` | 25 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
> Omission summary shows 8 of 631 groups; 623 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. _bootstrap_run_options_from_args"]
    s3["3. Path (src/llm_wiki_cli/services…rap_run_options_from_args)"]
    s4["4. validate_path"]
    s5["5. PathValidationError"]
    s6["6. (…).resolve"]
    s7["7. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s8["8. Path.cwd().resolve"]
    s9["9. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s10["10. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s11["11. PathValidationError"]
    s12["12. str (src/llm_wiki_cli/services…rap_run_options_from_args)"]
    s1 -->|"_bootstrap_run_options_from_args(args)"| s2
    s2 -. "Path (src/llm_wiki_cli/services…rap_run_options_from_args)(args.wiki_dir)" .-> s3
    s2 -->|"validate_path(str(...), '--wiki-dir')"| s4
    s4 -->|"PathValidationError(...)"| s5
    s4 -. "(…).resolve(data not statically known)" .-> s6
    s4 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s7
    s4 -. "Path.cwd().resolve(data not statically known)" .-> s8
    s4 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s9
    s4 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s10
    s4 -->|"PathValidationError(...)"| s11
    s2 -. "str (src/llm_wiki_cli/services…rap_run_options_from_args)(wiki_dir)" .-> s12
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
| `run` | `args` | `BootstrapExtractionError`, `BootstrapContractError`, `sys` | - | - |
| `_bootstrap_run_options_from_args` | `args` | `sys`, `sys` | - | `_BootstrapRunOptions(...)` |
| `Path (src/llm_wiki_cli/services…rap_run_options_from_args)` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `str (src/llm_wiki_cli/services…rap_run_options_from_args)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | _bootstrap_run_options_from_args | 6448 | `_bootstrap_run_options_from_args(args)` |
| _bootstrap_run_options_from_args | Path (src/llm_wiki_cli/services…rap_run_options_from_args) | 4522 | `Path(args.wiki_dir)` |
| _bootstrap_run_options_from_args | validate_path | 4523 | `validate_path(str(...), '--wiki-dir')` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 138 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 140 | `PathValidationError(...)` |
| _bootstrap_run_options_from_args | str (src/llm_wiki_cli/services…rap_run_options_from_args) | 4523 | `str(wiki_dir)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 6454 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Validates first-use options and the source/wiki boundaries, then delegates to
the deterministic bootstrap service. The target must be empty or the untouched
init scaffold; existing managed or custom content is rejected before
extraction. A successful run writes the selected wiki surfaces and consistent
generated artifacts, then prints either progress text or the structured
bootstrap result.
