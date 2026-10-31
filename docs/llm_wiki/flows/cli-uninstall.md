# uninstall

**Entry point:** `run` (`cli`)
**Source:** [uninstall_cmd](../modules/uninstall_cmd.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md), [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), and 6 more

**Complete modules touched:**

- [ci_installer](../modules/ci_installer.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [legacy_hooks](../modules/legacy_hooks.md)
- [paths](../modules/paths.md)
- [services_schema](../modules/services_schema.md)
- [skills](../modules/skills.md)
- [uninstall_cmd](../modules/uninstall_cmd.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as validate_path
    participant p2 as _preflight_hooks
    participant p3 as _preflight_agent_schemas
    participant p4 as _preflight_reference_skills
    participant p5 as _preflight_wiki_removal
    participant p6 as _preflight_runtime_artifacts
    participant p7 as _preflight_ci_workflow
    participant p8 as _remove_hooks
    participant p9 as _clean_agent_schemas
    participant p10 as _remove_ci_workflow
    participant p11 as _validate_hook_plan
    participant p12 as _validate_runtime_plan
    participant p13 as _validate_reference_plan
    participant p14 as _remove_runtime_artifacts
    participant p15 as _remove_wiki_dir
    participant p16 as _remove_reference_skill
    participant p17 as display_project_path
    participant p18 as _confirm
    participant p19 as _validate_schema_plan
    participant p20 as UnsafeUninstallPathError
    participant p21 as inspect_legacy_hooks
    participant p22 as require_safe_schema_path
    participant p23 as verify_reference_skill
    participant p24 as _runtime_artifact_paths
    participant p25 as remove_legacy_hooks
    participant p26 as windows_object_identity
    participant p27 as _path_contains
    participant p28 as classify_managed_schema_block
    participant p29 as getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run)
    participant p30 as wiki_dir.exists
    p0->>p1: validate_path
    p0->>p2: _preflight_hooks
    p0->>p3: _preflight_agent_schemas
    p0->>p4: _preflight_reference_skills
    p0->>p5: _preflight_wiki_removal
    p0->>p6: _preflight_runtime_artifacts
    p0->>p7: _preflight_ci_workflow
    p0->>p8: _remove_hooks
    p0->>p9: _clean_agent_schemas
    p0->>p10: _remove_ci_workflow
    p0->>p11: _validate_hook_plan
    p0->>p12: _validate_runtime_plan
    p0->>p13: _validate_reference_plan
    p0->>p14: _remove_runtime_artifacts
    p0->>p15: _remove_wiki_dir
    p0->>p16: _remove_reference_skill
    p0->>p17: display_project_path
    p0->>p18: _confirm
    p0->>p19: _validate_schema_plan
    p0->>p20: UnsafeUninstallPathError
    p2->>p21: inspect_legacy_hooks
    p3->>p22: require_safe_schema_path
    p4->>p23: verify_reference_skill
    p6->>p24: _runtime_artifact_paths
    p8->>p25: remove_legacy_hooks
    p4->>p26: windows_object_identity
    p6->>p27: _path_contains
    p3->>p28: classify_managed_schema_block
    p0-->>p29: getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)
    p5-->>p30: wiki_dir.exists
```

> Call sequence diagram shows 30 of 1173 interactions; 1143 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 543 (542 omitted); unresolved 1 of 243 (242 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | - | external | 2 |
| `src/llm_wiki_cli/commands/uninstall_cmd.py:run` | 1 | - | external | 40 |
| `src/llm_wiki_cli/services/legacy_hooks.py:inspect_legacy_hooks` | 16 | [src/llm_wiki_cli/services/legacy_hooks.py](../modules/legacy_hooks.md) | internal | 8 |
| `src/llm_wiki_cli/services/legacy_hooks.py:_hook_directories` | 17 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/legacy_hooks.py:_hook_directories` | 17 | - | external | 7 |
| `src/llm_wiki_cli/services/legacy_hooks.py:_hook_directories` | 17 | [src/llm_wiki_cli/services/legacy_hooks.py](../modules/legacy_hooks.md) | internal | 6 |
> Omission summary shows 8 of 252 groups; 244 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 388; effect analysis evaluated: 261, partial: 16, unavailable: 111. Counts include steps omitted from the displayed trace.

Collector observations for 277 source steps with known totals: observed: 1664, emitted: 1579, omitted: 85. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `run` | `available` | `partial` | `available` | `50` | `20` | `30` |
| `getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `validate_path` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `PathValidationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `(…).resolve` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `resolved.relative_to` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `PathValidationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `str (src/llm_wiki_cli/commands/uninstall_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_cli/commands/uninstall_cmd.py:run)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run)"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. (…).resolve"]
    s6["6. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s7["7. Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s8["8. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. resolved.relative_to"]
    s10["10. PathValidationError"]
    s11["11. str (src/llm_wiki_cli/commands/uninstall_cmd.py:run)"]
    s12["12. Path (src/llm_wiki_cli/commands/uninstall_cmd.py:run)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s2
    s1 -->|"validate_path(str(...), '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(…).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s7
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s3 -. "resolved.relative_to(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s1 -. "str (src/llm_wiki_cli/commands/uninstall_cmd.py:run)(wiki_dir_arg)" .-> s11
    s1 -. "Path (src/llm_wiki_cli/commands/uninstall_cmd.py:run)(wiki_dir_arg)" .-> s12
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
    b6["output print"]
    s1 -. "output print" .-> b6
    b7["output print"]
    s1 -. "output print" .-> b7
    click s1 "../modules/uninstall_cmd.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `ReferenceSkillState`, `BUNDLED_SKILLS_ROOT`, `REFERENCE_SKILL_ID`, `ManagedSchemaBlockError`, `ManagedSchemaPathError`, `UnsafeUninstallPathError`, `sys` | - | `none`, `none`, `none` |
| `getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run)` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `str (src/llm_wiki_cli/commands/uninstall_cmd.py:run)` | - | - | - | - |
| `Path (src/llm_wiki_cli/commands/uninstall_cmd.py:run)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/uninstall_cmd.py:run) | 811 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 812 | `validate_path(str(...), '--wiki-dir')` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to | 138 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 140 | `PathValidationError(...)` |
| run | str (src/llm_wiki_cli/commands/uninstall_cmd.py:run) | 812 | `str(wiki_dir_arg)` |
| run | Path (src/llm_wiki_cli/commands/uninstall_cmd.py:run) | 813 | `Path(wiki_dir_arg)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 839 |
| output | `print` | `run` | 843 |
| output | `print` | `run` | 846 |
| output | `print` | `run` | 847 |
| output | `print` | `run` | 850 |
| output | `print` | `run` | 853 |
| output | `print` | `run` | 856 |
| output | `print` | `run` | 859 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 811 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
