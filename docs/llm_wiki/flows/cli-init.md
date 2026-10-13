# init

**Entry point:** `run` (`cli`)
**Source:** [init_cmd](../modules/init_cmd.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [filesystem_guard](../modules/filesystem_guard.md), and 14 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [helper_preparation](../modules/helper_preparation.md)
- [init_cmd](../modules/init_cmd.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [paths](../modules/paths.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [services_schema](../modules/services_schema.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
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
    participant p1 as validate_path
    participant p2 as require_safe_wiki_scaffold
    participant p3 as require_safe_config_path
    participant p4 as inspect_config
    participant p5 as resolve_source_selection
    participant p6 as _managed_schema_agents
    participant p7 as require_replaceable_managed_schema
    participant p8 as ensure_source_helpers
    participant p9 as provision_wiki_scaffold
    participant p10 as require_config_inspection_unchanged
    participant p11 as _provision_reference_skill_guarded
    participant p12 as select_render_profile
    participant p13 as build_schema_content
    participant p14 as replace_schema_block_content
    participant p15 as require_managed_schema_profile
    participant p16 as write_config
    participant p17 as unlink_guarded_bytes
    participant p18 as require_committed_config
    participant p19 as get_agent_config_path
    participant p20 as config_requires_manual_recovery
    participant p21 as require_safe_schema_path
    participant p22 as decode_managed_document_bytes
    participant p23 as ManagedSchemaPathError
    participant p24 as ManagedSchemaBlockError
    participant p25 as helper_preparation_failure_hint
    participant p26 as reference_recovery_command
    participant p27 as skills_install_dir
    participant p28 as list_bundled_skills
    participant p29 as getattr (src/llm_wiki_cli/commands/init_cmd.py:run)
    participant p30 as stored.get
    p0->>p1: validate_path
    p0->>p2: require_safe_wiki_scaffold
    p0->>p3: require_safe_config_path
    p0->>p4: inspect_config
    p0->>p5: resolve_source_selection
    p0->>p6: _managed_schema_agents
    p0->>p7: require_replaceable_managed_schema
    p0->>p8: ensure_source_helpers
    p0->>p9: provision_wiki_scaffold
    p0->>p10: require_config_inspection_unchanged
    p0->>p11: _provision_reference_skill_guarded
    p0->>p12: select_render_profile
    p0->>p13: build_schema_content
    p0->>p14: replace_schema_block_content
    p0->>p15: require_managed_schema_profile
    p0->>p16: write_config
    p0->>p17: unlink_guarded_bytes
    p0->>p18: require_committed_config
    p0->>p19: get_agent_config_path
    p0->>p20: config_requires_manual_recovery
    p0->>p21: require_safe_schema_path
    p0->>p22: decode_managed_document_bytes
    p0->>p23: ManagedSchemaPathError
    p0->>p24: ManagedSchemaBlockError
    p0->>p25: helper_preparation_failure_hint
    p0->>p26: reference_recovery_command
    p0->>p27: skills_install_dir
    p0->>p28: list_bundled_skills
    p0-->>p29: getattr (src/llm_wiki_cli/commands/init_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)
    p0-->>p30: stored.get('pending_cleanup_agent')
```

> Call sequence diagram shows 30 of 1892 interactions; 1862 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 782 (781 omitted); unresolved 1 of 448 (447 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/config.py:validate_path` | 3 | - | external | 2 |
| `src/llm_wiki_cli/commands/init_cmd.py:run` | 1 | - | external | 100 |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:require_safe_wiki_scaffold` | 16 | - | external | 3 |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:require_safe_wiki_scaffold` | 16 | [src/llm_wiki_cli/services/wiki_surface.py](../modules/wiki_surface.md) | internal | 1 |
| `src/llm_wiki_cli/services/wiki_surface.py:iter_directory_kinds` | 19 | - | external | 1 |
| `src/llm_wiki_cli/services/wiki_lifecycle.py:require_safe_wiki_scaffold` | 16 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
> Omission summary shows 8 of 403 groups; 395 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/init_cmd.py:run)"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. (…).resolve"]
    s6["6. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s7["7. Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s8["8. Path.cwd (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s10["10. PathValidationError"]
    s11["11. bool (src/llm_wiki_cli/commands/init_cmd.py:run)"]
    s12["12. getattr (src/llm_wiki_cli/commands/init_cmd.py:run)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/init_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s2
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(…).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s7
    s3 -. "Path.cwd (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s3 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s1 -. "bool (src/llm_wiki_cli/commands/init_cmd.py:run)(getattr(...))" .-> s11
    s1 -. "getattr (src/llm_wiki_cli/commands/init_cmd.py:run)(args, 'prepare_extractors', False)" .-> s12
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
    b7["mutation stored.pop"]
    s1 -. "mutation stored.pop" .-> b7
    click s1 "../modules/init_cmd.md"
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
| `run` | `args` | `DEFAULT_WIKI_DIR`, `sys`, `WikiScaffoldPathError`, `sys`, `AgentConfigState`, `sys`, `AgentConfigState`, `AgentConfigState` | `config[...]` | - |
| `getattr (src/llm_wiki_cli/commands/init_cmd.py:run)` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `bool (src/llm_wiki_cli/commands/init_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/init_cmd.py:run)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/init_cmd.py:run) | 96 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | validate_path | 97 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd (src/llm_wiki_cli/config.py:validate_path) | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 138 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 140 | `PathValidationError(...)` |
| run | bool (src/llm_wiki_cli/commands/init_cmd.py:run) | 98 | `bool(getattr(...))` |
| run | getattr (src/llm_wiki_cli/commands/init_cmd.py:run) | 98 | `getattr(args, 'prepare_extractors', False)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 101 |
| output | `print` | `run` | 110 |
| output | `print` | `run` | 123 |
| output | `print` | `run` | 135 |
| output | `print` | `run` | 146 |
| output | `print` | `run` | 154 |
| output | `print` | `run` | 163 |
| mutation | `stored.pop` | `run` | 171 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 96 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| external_call | `run` | `getattr` | 98 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

Initialization validates existing workspace and agent state before creating or
refreshing the wiki scaffold and managed instructions. With
`--prepare-extractors`, it first detects selected helper languages and prepares
missing or stale artifacts in the helper cache. A preparation failure reports
the prerequisite and stops before scaffold or configuration changes. A retry
reuses helpers already prepared successfully. Preparation is opt-in for each
invocation and may download dependencies or compile bundled helpers.
