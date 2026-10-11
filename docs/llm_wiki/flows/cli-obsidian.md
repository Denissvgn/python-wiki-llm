# obsidian

**Entry point:** `run` (`cli`)
**Source:** [obsidian_cmd](../modules/obsidian_cmd.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 50 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [obsidian](../modules/obsidian.md)
- [obsidian_cmd](../modules/obsidian_cmd.md)
- [packages](../modules/packages.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_contracts](../modules/python_contracts.md)
- [python_implementation](../modules/python_implementation.md)
- [python_observations](../modules/python_observations.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)
    participant p2 as validate_path
    participant p3 as bool (src/llm_wiki_cli/commands/obsidian_cmd.py:run)
    participant p4 as validate_source_root
    participant p5 as str (src/llm_wiki_cli/commands/obsidian_cmd.py:run)
    participant p6 as validate_obsidian_export_source_selection
    participant p7 as _knowledge_projection
    participant p8 as export_obsidian_vault
    participant p9 as _print_report
    participant p10 as check_obsidian_vault
    participant p11 as SystemExit
    participant p12 as install_obsidian_plugin
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'obsidian_action', None)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'format', 'text')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'src_dir', '.')
    p0->>p2: validate_path
    p0-->>p3: bool (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(getattr(...))
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'allow_external_src', False)
    p0->>p4: validate_source_root
    p0-->>p5: str (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(source_root)
    p0->>p6: validate_obsidian_export_source_selection
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'source_selection', None)
    p0->>p7: _knowledge_projection
    p0->>p8: export_obsidian_vault
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'vault_dir')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'notes_dir', DEFAULT_NOTES_DIR)
    p0-->>p3: bool (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(getattr(...))
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'dry_run', False)
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'knowledge_metadata', None)
    p0->>p9: _print_report
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)
    p0->>p2: validate_path
    p0->>p7: _knowledge_projection
    p0->>p10: check_obsidian_vault
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'vault_dir')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'knowledge_metadata', None)
    p0->>p9: _print_report
    p0-->>p11: SystemExit(1)
    p0->>p12: install_obsidian_plugin
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'vault_dir')
    p0-->>p1: getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'plugin_dir', DEFAULT_PLUGIN_SOURCE)
```

> Call sequence diagram shows 30 of 3165 interactions; 3135 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 19 of 949 (930 omitted); unresolved 0 of 860 (860 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_path` | 6 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 6 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 6 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 16 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 7 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 16 | - | unresolved | 5 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 16 | - | external | 11 |
| `src/llm_wiki_cli/config.py:validate_source_root` | 16 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 1 |
| `src/llm_wiki_cli/services/filesystem_guard.py:windows_current_user_sid` | 28 | [src/llm_wiki_cli/services/filesystem_guard.py](../modules/filesystem_guard.md) | internal | 2 |
> Omission summary shows 8 of 773 groups; 765 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)"]
    s3["3. getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)"]
    s4["4. getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)"]
    s5["5. getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)"]
    s6["6. validate_path"]
    s7["7. PathValidationError"]
    s8["8. (…).resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s10["10. Path.cwd().resolve"]
    s11["11. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s12["12. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'obsidian_action', None)" .-> s2
    s1 -. "getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'format', 'text')" .-> s3
    s1 -. "getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s4
    s1 -. "getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)(args, 'src_dir', '.')" .-> s5
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s6
    s6 -->|"PathValidationError(...)"| s7
    s6 -. "(…).resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s6 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s9
    s6 -. "Path.cwd().resolve(data not statically known)" .-> s10
    s6 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s11
    s6 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    click s1 "../modules/obsidian_cmd.md"
    click s6 "../modules/config.md"
    click s7 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `DEFAULT_NOTES_DIR`, `DEFAULT_WIKI_DIR`, `DEFAULT_PLUGIN_SOURCE`, `ObsidianError`, `sys`, `sys` | - | `none`, `none`, `none` |
| `getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run)` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run) | 74 | `getattr(args, 'obsidian_action', None)` |
| run | getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run) | 75 | `getattr(args, 'format', 'text')` |
| run | getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run) | 79 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr (src/llm_wiki_cli/commands/obsidian_cmd.py:run) | 80 | `getattr(args, 'src_dir', '.')` |
| run | validate_path | 81 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve (src/llm_wiki_cli/config.py:validate_path) | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 138 | `resolved.relative_to(cwd)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 132 |
| output | `print` | `run` | 135 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 74 |
| external_call | `run` | `getattr` | 75 |
| external_call | `run` | `getattr` | 79 |
| external_call | `run` | `getattr` | 80 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Dispatches one of three explicit actions. `export` validates the current source
selection and writes or previews a derived vault mirror; `check` compares an
existing mirror and exits nonzero on mismatches; `install-plugin` copies the
packaged plugin into the vault. Optional knowledge metadata is projected under
the selected disclosure profile before export, and the canonical wiki is never
replaced by mirror content.
