# install_ci_workflow

**Entry point:** `install_ci_workflow` (`api`)
**Source:** [ci_installer](../modules/ci_installer.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md), [config](../modules/config.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 4 more

**Complete modules touched:**

- [ci_installer](../modules/ci_installer.md)
- [config](../modules/config.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as install_ci_workflow
    participant p1 as normalize_action_ref
    participant p2 as isinstance
    participant p3 as fullmatch
    participant p4 as InstallCiError
    participant p5 as lower
    participant p6 as _portable_project_path
    participant p7 as _without_github_expression
    participant p8 as _validated_project_path
    participant p9 as require_repository_relative_path
    participant p10 as strip
    participant p11 as any
    participant p12 as ord
    participant p13 as startswith
    participant p14 as match
    participant p15 as split
    participant p16 as PurePosixPath
    participant p17 as normpath
    participant p18 as require_portable_relative_path
    participant p19 as _default_path_error
    participant p20 as SharedValidationError
    participant p21 as fspath
    participant p22 as encode
    p0->>p1: normalize_action_ref
    p1-->>p2: isinstance
    p1-->>p3: fullmatch
    p1->>p4: InstallCiError
    p1-->>p5: lower
    p0->>p6: _portable_project_path
    p6->>p7: _without_github_expression
    p7->>p4: InstallCiError
    p6->>p8: _validated_project_path
    p8->>p9: require_repository_relative_path
    p9-->>p2: isinstance
    p9-->>p10: strip
    p9-->>p11: any
    p9-->>p12: ord
    p9-->>p12: ord
    p9-->>p13: startswith
    p9-->>p13: startswith
    p9-->>p14: match
    p9-->>p15: split
    p9-->>p16: PurePosixPath
    p9-->>p11: any
    p9-->>p17: normpath
    p9->>p18: require_portable_relative_path
    p18-->>p2: isinstance
    p18->>p19: _default_path_error
    p19->>p20: SharedValidationError
    p18-->>p21: fspath
    p18-->>p2: isinstance
    p18->>p19: _default_path_error
    p18-->>p22: encode
```

> Call sequence diagram shows 30 of 410 interactions; 380 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. install_ci_workflow"]
    s2["2. normalize_action_ref"]
    s3["3. isinstance"]
    s4["4. fullmatch"]
    s5["5. InstallCiError"]
    s6["6. lower"]
    s7["7. _portable_project_path"]
    s8["8. _without_github_expression"]
    s9["9. InstallCiError"]
    s10["10. _validated_project_path"]
    s11["11. require_repository_relative_path"]
    s12["12. isinstance"]
    s1 -->|"normalize_action_ref(action_ref)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "_ACTION_REF_RE.fullmatch(value)" .-> s4
    s2 -->|"InstallCiError('--action-ref must be exactly 40 hexadecimal characters')"| s5
    s2 -. "value.lower(data not statically known)" .-> s6
    s1 -->|"_portable_project_path(src_dir, label='--src-dir', allow_root=True)"| s7
    s7 -->|"_without_github_expression(_validated_project_path(...), label=label)"| s8
    s8 -->|"InstallCiError(...)"| s9
    s7 -->|"_validated_project_path(value, label=label)"| s10
    s10 -->|"require_repository_relative_path(value, text_error=InstallCiError(...), posix_error=InstallCiError(...), normalized_error=InstallCiError(...), absolute_error=I…"| s11
    s11 -. "isinstance(value, str)" .-> s12
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
| `isinstance` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `InstallCiError` | - | - | - | - |
| `lower` | - | - | - | - |
| `_portable_project_path` | `value: object`, `label: str`, `allow_root: bool` | - | - | `'.'`, `_without_github_expression(...)` |
| `_without_github_expression` | `path: str`, `label: str` | - | - | `path` |
| `InstallCiError` | - | - | - | - |
| `_validated_project_path` | `value: object`, `label: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `require_portable_relative_path(...)` |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| install_ci_workflow | normalize_action_ref | 292 | `normalize_action_ref(action_ref)` |
| normalize_action_ref | isinstance | 63 | `isinstance(value, str)` |
| normalize_action_ref | fullmatch | 63 | `_ACTION_REF_RE.fullmatch(value)` |
| normalize_action_ref | InstallCiError | 64 | `InstallCiError('--action-ref must be exactly 40 hexadecimal characters')` |
| normalize_action_ref | lower | 65 | `value.lower(data not statically known)` |
| install_ci_workflow | _portable_project_path | 293 | `_portable_project_path(src_dir, label='--src-dir', allow_root=True)` |
| _portable_project_path | _without_github_expression | 100 | `_without_github_expression(_validated_project_path(...), label=label)` |
| _without_github_expression | InstallCiError | 93 | `InstallCiError(...)` |
| _portable_project_path | _validated_project_path | 101 | `_validated_project_path(value, label=label)` |
| _validated_project_path | require_repository_relative_path | 69 | `require_repository_relative_path(value, text_error=InstallCiError(...), posix_error=InstallCiError(...), normalized_error=InstallCiError(...), absolute_error=InstallCiError(...), separator_error=InstallCiError(...), control_error=InstallCiError(...), reject_delete_character=True, leading_backslash_is_absolute=True, portability_error=InstallCiError(...))` |
| require_repository_relative_path | isinstance | 256 | `isinstance(value, str)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `target.read_bytes` | `install_ci_workflow` | 323 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `normalize_action_ref` | `isinstance` | 63 |
| unresolved_call | `normalize_action_ref` | `_ACTION_REF_RE.fullmatch` | 63 |
| unresolved_call | `normalize_action_ref` | `value.lower` | 65 |
| unresolved_call | `require_repository_relative_path` | `isinstance` | 256 |
| step_limit | `install_ci_workflow` | `first 12 steps` | 0 |

## Behavior

This flow starts at `install_ci_workflow` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
