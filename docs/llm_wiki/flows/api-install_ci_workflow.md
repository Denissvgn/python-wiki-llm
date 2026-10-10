# install_ci_workflow

**Entry point:** `install_ci_workflow` (`api`)
**Source:** [ci_installer](../modules/ci_installer.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md), [common](../modules/common.md), [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), and 12 more

**Complete modules touched:**

- [ci_installer](../modules/ci_installer.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as install_ci_workflow
    participant p1 as normalize_action_ref
    participant p2 as _portable_project_path
    participant p3 as Path.cwd().resolve
    participant p4 as Path.cwd (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    participant p5 as Path(…).resolve (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    participant p6 as Path (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    participant p7 as InstallCiError
    participant p8 as root.is_dir (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    participant p9 as _project_directory
    participant p10 as classify_wiki_lifecycle
    participant p11 as _validate_default_selection_contract
    participant p12 as render_managed_workflow
    participant p13 as _validate_workflow_target
    participant p14 as target.exists (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    participant p15 as target.read_bytes
    participant p16 as _normalize_newlines
    participant p17 as InstallCiResult
    participant p18 as is_unmodified_managed_workflow
    participant p19 as write_bytes_atomic
    participant p20 as isinstance (src/llm_wiki_cli/services…r.py:normalize_action_ref)
    participant p21 as _without_github_expression
    participant p22 as locate_exact_repository_path
    p0->>p1: normalize_action_ref
    p0->>p2: _portable_project_path
    p0->>p2: _portable_project_path
    p0-->>p3: Path.cwd().resolve
    p0-->>p4: Path.cwd (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    p0-->>p5: Path(…).resolve (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    p0-->>p6: Path (src/llm_wiki_cli/services…er.py:install_ci_workflow)(project_root)
    p0->>p7: InstallCiError
    p0-->>p8: root.is_dir (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    p0->>p7: InstallCiError
    p0->>p9: _project_directory
    p0->>p9: _project_directory
    p0->>p10: classify_wiki_lifecycle
    p0->>p7: InstallCiError
    p0->>p11: _validate_default_selection_contract
    p0->>p12: render_managed_workflow
    p0->>p13: _validate_workflow_target
    p0-->>p14: target.exists (src/llm_wiki_cli/services…er.py:install_ci_workflow)
    p0-->>p15: target.read_bytes
    p0->>p7: InstallCiError
    p0->>p16: _normalize_newlines
    p0->>p17: InstallCiResult
    p0->>p18: is_unmodified_managed_workflow
    p0->>p7: InstallCiError
    p0->>p19: write_bytes_atomic
    p0->>p7: InstallCiError
    p0->>p17: InstallCiResult
    p1-->>p20: isinstance (src/llm_wiki_cli/services…r.py:normalize_action_ref)(value, str)
    p2->>p21: _without_github_expression
    p9->>p22: locate_exact_repository_path
```

> Call sequence diagram shows 30 of 730 interactions; 700 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 217 (214 omitted); unresolved 5 of 173 (168 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/ci_installer.py:normalize_action_ref` | 2 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/ci_installer.py:normalize_action_ref` | 2 | [src/llm_wiki_cli/services/ci_installer.py](../modules/ci_installer.md) | internal | 1 |
| `src/llm_wiki_cli/services/ci_installer.py:_without_github_expression` | 8 | [src/llm_wiki_cli/services/ci_installer.py](../modules/ci_installer.md) | internal | 1 |
| `src/llm_wiki_cli/services/ci_installer.py:_portable_project_path` | 7 | [src/llm_wiki_cli/services/ci_installer.py](../modules/ci_installer.md) | internal | 1 |
| `src/llm_wiki_cli/services/ci_installer.py:_validated_project_path` | 10 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 11 | - | external | 7 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 4 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 13 | - | external | 6 |
> Omission summary shows 8 of 207 groups; 199 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. install_ci_workflow"]
    s2["2. normalize_action_ref"]
    s3["3. isinstance (src/llm_wiki_cli/services…r.py:normalize_action_ref)"]
    s4["4. _ACTION_REF_RE.fullmatch"]
    s5["5. InstallCiError"]
    s6["6. value.lower"]
    s7["7. _portable_project_path"]
    s8["8. _without_github_expression"]
    s9["9. InstallCiError"]
    s10["10. _validated_project_path"]
    s11["11. require_repository_relative_path"]
    s12["12. isinstance (src/llm_wiki_cli/services…_repository_relative_path)"]
    s1 -->|"normalize_action_ref(action_ref)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…r.py:normalize_action_ref)(value, str)" .-> s3
    s2 -. "_ACTION_REF_RE.fullmatch(value)" .-> s4
    s2 -->|"InstallCiError('--action-ref must be exactly 40 hexadecimal characters')"| s5
    s2 -. "value.lower(data not statically known)" .-> s6
    s1 -->|"_portable_project_path(src_dir, label='--src-dir', allow_root=True)"| s7
    s7 -->|"_without_github_expression(_validated_project_path(...), label=label)"| s8
    s8 -->|"InstallCiError(...)"| s9
    s7 -->|"_validated_project_path(value, label=label)"| s10
    s10 -->|"require_repository_relative_path(…)"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)" .-> s12
    b0["filesystem_read target.read_bytes"]
    s1 -. "filesystem_read target.read_bytes" .-> b0
    click s1 "../modules/ci_installer.md"
    click s2 "../modules/ci_installer.md"
    click s5 "../modules/ci_installer.md"
    click s7 "../modules/ci_installer.md"
    click s8 "../modules/ci_installer.md"
    click s9 "../modules/ci_installer.md"
    click s10 "../modules/ci_installer.md"
    click s11 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `install_ci_workflow` | `action_ref: str`, `src_dir: str`, `wiki_dir: str`, `dry_run: bool`, `force: bool`, `project_root: str \| Path \| None` | `WikiLifecycleState`, `MANIFEST_FILENAME`, `MANAGED_WORKFLOW_PATH`, `MANAGED_WORKFLOW_PATH`, `MANAGED_WORKFLOW_PATH`, `MANAGED_WORKFLOW_PATH`, `MANAGED_WORKFLOW_PATH` | - | `InstallCiResult(...)`, `InstallCiResult(...)` |
| `normalize_action_ref` | `value: object` | - | - | `value.lower(...)` |
| `isinstance (src/llm_wiki_cli/services…r.py:normalize_action_ref)` | - | - | - | - |
| `_ACTION_REF_RE.fullmatch` | - | - | - | - |
| `InstallCiError` | - | - | - | - |
| `value.lower` | - | - | - | - |
| `_portable_project_path` | `value: object`, `label: str`, `allow_root: bool` | - | - | `'.'`, `_without_github_expression(...)` |
| `_without_github_expression` | `path: str`, `label: str` | - | - | `path` |
| `InstallCiError` | - | - | - | - |
| `_validated_project_path` | `value: object`, `label: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| install_ci_workflow | normalize_action_ref | 297 | `normalize_action_ref(action_ref)` |
| normalize_action_ref | isinstance (src/llm_wiki_cli/services…r.py:normalize_action_ref) | 63 | `isinstance(value, str)` |
| normalize_action_ref | _ACTION_REF_RE.fullmatch | 63 | `_ACTION_REF_RE.fullmatch(value)` |
| normalize_action_ref | InstallCiError | 64 | `InstallCiError('--action-ref must be exactly 40 hexadecimal characters')` |
| normalize_action_ref | value.lower | 65 | `value.lower(data not statically known)` |
| install_ci_workflow | _portable_project_path | 298 | `_portable_project_path(src_dir, label='--src-dir', allow_root=True)` |
| _portable_project_path | _without_github_expression | 100 | `_without_github_expression(_validated_project_path(...), label=label)` |
| _without_github_expression | InstallCiError | 93 | `InstallCiError(...)` |
| _portable_project_path | _validated_project_path | 101 | `_validated_project_path(value, label=label)` |
| _validated_project_path | require_repository_relative_path | 69 | `require_repository_relative_path(value, text_error=InstallCiError(...), posix_error=InstallCiError(...), normalized_error=InstallCiError(...), absolute_error=InstallCiError(...), separator_error=InstallCiError(...), control_error=InstallCiError(...), reject_delete_character=True, leading_backslash_is_absolute=True, portability_error=InstallCiError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…_repository_relative_path) | 299 | `isinstance(value, str)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `target.read_bytes` | `install_ci_workflow` | 328 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_action_ref` | `isinstance` | 63 |
| unresolved_call | `normalize_action_ref` | `_ACTION_REF_RE.fullmatch` | 63 |
| unresolved_call | `normalize_action_ref` | `value.lower` | 65 |
| external_call | `require_repository_relative_path` | `isinstance` | 299 |
| step_limit | `install_ci_workflow` | `first 12 steps` | 0 |
| truncated_flow | `install_ci_workflow` | `depth limit` | 0 |

## Behavior

This flow starts at `install_ci_workflow` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
