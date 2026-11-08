# install-ci

**Entry point:** `run` (`cli`)
**Source:** [install_ci_cmd](../modules/install_ci_cmd.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md), [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), [current_contracts](../modules/current_contracts.md), and 15 more

**Complete modules touched:**

- [ci_installer](../modules/ci_installer.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [current_contracts](../modules/current_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [install_ci_cmd](../modules/install_ci_cmd.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [publication_config](../modules/publication_config.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as install_documentation_ci_workflow
    participant p2 as install_ci_workflow
    participant p3 as InstallCiError
    participant p4 as _project_root
    participant p5 as normalize_action_ref
    participant p6 as _portable_project_path
    participant p7 as classify_wiki_lifecycle
    participant p8 as _project_directory
    participant p9 as render_managed_workflow
    participant p10 as load_publication_config
    participant p11 as _validate_default_selection_contract
    participant p12 as publication_path
    participant p13 as publication_control_overlap
    participant p14 as _install_workflow
    participant p15 as _documentation_workflow
    participant p16 as _without_github_expression
    participant p17 as locate_exact_repository_path
    participant p18 as _consumer_root
    participant p19 as _validate_workflow_target
    participant p20 as _validated_project_path
    participant p21 as _relative_path
    participant p22 as SyncManifest.load
    participant p23 as is_pristine_wiki_target
    participant p24 as resolve_source_selection
    participant p25 as validate_persisted_source_selection_identity
    participant p26 as is_unmodified_managed_workflow
    participant p27 as read_publication_json
    participant p28 as ensure_guarded_directory
    participant p29 as getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)
    participant p30 as authored.extend
    p0->>p1: install_documentation_ci_workflow
    p0->>p2: install_ci_workflow
    p0->>p3: InstallCiError
    p1->>p4: _project_root
    p1->>p5: normalize_action_ref
    p1->>p6: _portable_project_path
    p2->>p7: classify_wiki_lifecycle
    p1->>p8: _project_directory
    p2->>p9: render_managed_workflow
    p1->>p10: load_publication_config
    p1->>p11: _validate_default_selection_contract
    p1->>p12: publication_path
    p1->>p13: publication_control_overlap
    p1->>p14: _install_workflow
    p1->>p15: _documentation_workflow
    p6->>p16: _without_github_expression
    p8->>p17: locate_exact_repository_path
    p10->>p18: _consumer_root
    p14->>p19: _validate_workflow_target
    p6->>p20: _validated_project_path
    p10->>p21: _relative_path
    p11->>p22: SyncManifest.load
    p7->>p23: is_pristine_wiki_target
    p11->>p24: resolve_source_selection
    p11->>p25: validate_persisted_source_selection_identity
    p14->>p26: is_unmodified_managed_workflow
    p10->>p27: read_publication_json
    p14->>p28: ensure_guarded_directory
    p0-->>p29: getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'profile', 'integrity')
    p1-->>p30: authored.extend(...)
```

> Call sequence diagram shows 30 of 1301 interactions; 1271 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 446 (445 omitted); unresolved 1 of 296 (295 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/commands/install_ci_cmd.py:run` | 1 | - | external | 15 |
| `src/llm_wiki_cli/services/ci_installer.py:install_documentation_ci_workflow` | 9 | - | external | 3 |
| `src/llm_wiki_cli/services/ci_installer.py:install_documentation_ci_workflow` | 9 | [src/llm_wiki_cli/services/ci_installer.py](../modules/ci_installer.md) | internal | 15 |
| `src/llm_wiki_cli/services/ci_installer.py:_project_root` | 13 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/ci_installer.py:_project_root` | 13 | - | external | 2 |
| `src/llm_wiki_cli/services/ci_installer.py:_project_root` | 13 | [src/llm_wiki_cli/services/ci_installer.py](../modules/ci_installer.md) | internal | 2 |
| `src/llm_wiki_cli/services/ci_installer.py:normalize_action_ref` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/ci_installer.py:normalize_action_ref` | 20 | - | unresolved | 2 |
> Omission summary shows 8 of 281 groups; 273 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 560; effect analysis evaluated: 315, partial: 18, unavailable: 227. Counts include steps omitted from the displayed trace.

Collector observations for 333 source steps with known totals: observed: 1910, emitted: 1849, omitted: 61. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `run` | `available` | `evaluated` | `available` | `14` | `14` | `0` |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InstallCiError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `install_documentation_ci_workflow` | `available` | `partial` | `available` | `24` | `19` | `5` |
| `any (src/llm_wiki_cli/services…documentation_ci_workflow)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services…documentation_ci_workflow)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InstallCiError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)"]
    s3["3. getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)"]
    s4["4. getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)"]
    s5["5. getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)"]
    s6["6. getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)"]
    s7["7. getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)"]
    s8["8. InstallCiError"]
    s9["9. install_documentation_ci_workflow"]
    s10["10. any (src/llm_wiki_cli/services…documentation_ci_workflow)"]
    s11["11. type (src/llm_wiki_cli/services…documentation_ci_workflow)"]
    s12["12. InstallCiError"]
    s1 -. "getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'profile', 'integrity')" .-> s2
    s1 -. "getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'src_dir', '.')" .-> s3
    s1 -. "getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'dry_run', False)" .-> s4
    s1 -. "getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'force', False)" .-> s5
    s1 -. "getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'require_ready', False)" .-> s6
    s1 -. "getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s7
    s1 -->|"InstallCiError('--wiki-dir applies to the integrity profile; set architecture.root in --config')"| s8
    s1 -->|"install_documentation_ci_workflow(…)"| s9
    s9 -. "any (src/llm_wiki_cli/services…documentation_ci_workflow)(...)" .-> s10
    s9 -. "type (src/llm_wiki_cli/services…documentation_ci_workflow)(value)" .-> s11
    s9 -->|"InstallCiError('require_ready, force and dry_run must be booleans')"| s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    b6["mutation authored.extend"]
    s9 -. "mutation authored.extend" .-> b6
    b7["mutation protected.append"]
    s9 -. "mutation protected.append" .-> b7
    click s1 "../modules/install_ci_cmd.md"
    click s8 "../modules/ci_installer.md"
    click s9 "../modules/ci_installer.md"
    click s12 "../modules/ci_installer.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `PUBLICATION_CONFIG_PATH`, `DEFAULT_WIKI_DIR`, `InstallCiError`, `sys` | - | `none`, `none` |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run)` | - | - | - | - |
| `InstallCiError` | - | - | - | - |
| `install_documentation_ci_workflow` | `action_ref: str`, `config: str`, `working_directory: str`, `src_dir: str`, `target_dir: str \| None`, `baseline: str \| None`, `reviews: str \| None`, `previous_receipt: str \| None` | `DOCUMENTATION_WORKFLOW_PATH`, `PublicationConfigError`, `DOCUMENTATION_WORKFLOW_PATH` | `inputs[...]`, `inputs[...]`, `inputs[...]` | `_install_workflow(...)` |
| `any (src/llm_wiki_cli/services…documentation_ci_workflow)` | - | - | - | - |
| `type (src/llm_wiki_cli/services…documentation_ci_workflow)` | - | - | - | - |
| `InstallCiError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run) | 17 | `getattr(args, 'profile', 'integrity')` |
| run | getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run) | 18 | `getattr(args, 'src_dir', '.')` |
| run | getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run) | 19 | `getattr(args, 'dry_run', False)` |
| run | getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run) | 20 | `getattr(args, 'force', False)` |
| run | getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run) | 21 | `getattr(args, 'require_ready', False)` |
| run | getattr (src/llm_wiki_cli/commands/install_ci_cmd.py:run) | 24 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | InstallCiError | 25 | `InstallCiError('--wiki-dir applies to the integrity profile; set architecture.root in --config')` |
| run | install_documentation_ci_workflow | 28 | `install_documentation_ci_workflow(action_ref=args.action_ref, src_dir=src_dir, dry_run=dry_run, force=force, config=..., working_directory=..., target_dir=args.target_dir, baseline=args.baseline, reviews=args.reviews, previous_receipt=args.previous_receipt, candidate_review=args.candidate_review, require_ready=require_ready)` |
| install_documentation_ci_workflow | any (src/llm_wiki_cli/services…documentation_ci_workflow) | 365 | `any(...)` |
| install_documentation_ci_workflow | type (src/llm_wiki_cli/services…documentation_ci_workflow) | 365 | `type(value)` |
| install_documentation_ci_workflow | InstallCiError | 366 | `InstallCiError('require_ready, force and dry_run must be booleans')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 68 |
| output | `print` | `run` | 72 |
| output | `print` | `run` | 77 |
| output | `print` | `run` | 78 |
| output | `print` | `run` | 82 |
| output | `print` | `run` | 83 |
| mutation | `authored.extend` | `install_documentation_ci_workflow` | 397 |
| mutation | `protected.append` | `install_documentation_ci_workflow` | 405 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 17 |
| external_call | `run` | `getattr` | 18 |
| external_call | `run` | `getattr` | 19 |
| external_call | `run` | `getattr` | 20 |
| external_call | `run` | `getattr` | 21 |
| external_call | `run` | `getattr` | 24 |
| external_call | `install_documentation_ci_workflow` | `any` | 365 |
| external_call | `install_documentation_ci_workflow` | `type` | 365 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

The command requires an initialized managed wiki whose persisted source-selection
identity is compatible with default profile discovery. It accepts only a complete
40-character action commit and portable, exact-case project-relative source and
wiki paths, then writes only `.github/workflows/llm-wiki-integrity.yml`.

An identical workflow is a byte-preserving no-op. A checksum-valid workflow
previously installed by the command can be updated, while an unmanaged or locally
modified target is preserved unless `--force` is explicit. `--dry-run` reports the
planned create or update without writing. Validation and write failures return a
nonzero CLI status.
