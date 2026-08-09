# install-ci

**Entry point:** `run` (`cli`)
**Source:** [install_ci_cmd](../modules/install_ci_cmd.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md), [config](../modules/config.md), [install_ci_cmd](../modules/install_ci_cmd.md), [io](../modules/io.md), and 4 more

**Complete modules touched:**

- [ci_installer](../modules/ci_installer.md)
- [config](../modules/config.md)
- [install_ci_cmd](../modules/install_ci_cmd.md)
- [io](../modules/io.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as install_ci_workflow
    participant p2 as normalize_action_ref
    participant p3 as isinstance
    participant p4 as fullmatch
    participant p5 as InstallCiError
    participant p6 as lower
    participant p7 as _portable_project_path
    participant p8 as _without_github_expression
    participant p9 as _validated_project_path
    participant p10 as require_repository_relative_path
    participant p11 as strip
    participant p12 as any
    participant p13 as ord
    participant p14 as startswith
    participant p15 as match
    participant p16 as split
    participant p17 as PurePosixPath
    participant p18 as normpath
    participant p19 as require_portable_relative_path
    participant p20 as _default_path_error
    participant p21 as fspath
    participant p22 as encode
    p0->>p1: install_ci_workflow
    p1->>p2: normalize_action_ref
    p2-->>p3: isinstance
    p2-->>p4: fullmatch
    p2->>p5: InstallCiError
    p2-->>p6: lower
    p1->>p7: _portable_project_path
    p7->>p8: _without_github_expression
    p8->>p5: InstallCiError
    p7->>p9: _validated_project_path
    p9->>p10: require_repository_relative_path
    p10-->>p3: isinstance
    p10-->>p11: strip
    p10-->>p12: any
    p10-->>p13: ord
    p10-->>p13: ord
    p10-->>p14: startswith
    p10-->>p14: startswith
    p10-->>p15: match
    p10-->>p16: split
    p10-->>p17: PurePosixPath
    p10-->>p12: any
    p10-->>p18: normpath
    p10->>p19: require_portable_relative_path
    p19-->>p3: isinstance
    p19->>p20: _default_path_error
    p19-->>p21: fspath
    p19-->>p3: isinstance
    p19->>p20: _default_path_error
    p19-->>p22: encode
```

> Call sequence diagram shows 30 of 383 interactions; 353 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. install_ci_workflow"]
    s3["3. normalize_action_ref"]
    s4["4. isinstance"]
    s5["5. fullmatch"]
    s6["6. InstallCiError"]
    s7["7. lower"]
    s8["8. _portable_project_path"]
    s9["9. _without_github_expression"]
    s10["10. InstallCiError"]
    s11["11. _validated_project_path"]
    s12["12. require_repository_relative_path"]
    s1 -->|"install_ci_workflow(action_ref=getattr(...), src_dir=getattr(...), wiki_dir=getattr(...), dry_run=bool(...), force=bool(...))"| s2
    s2 -->|"normalize_action_ref(action_ref)"| s3
    s3 -. "isinstance(value, str)" .-> s4
    s3 -. "_ACTION_REF_RE.fullmatch(value)" .-> s5
    s3 -->|"InstallCiError('--action-ref must be exactly 40 hexadecimal characters')"| s6
    s3 -. "value.lower(data not statically known)" .-> s7
    s2 -->|"_portable_project_path(src_dir, label='--src-dir', allow_root=True)"| s8
    s8 -->|"_without_github_expression(_validated_project_path(...), label=label)"| s9
    s9 -->|"InstallCiError(...)"| s10
    s8 -->|"_validated_project_path(value, label=label)"| s11
    s11 -->|"require_repository_relative_path(value, text_error=InstallCiError(...), posix_error=InstallCiError(...), normalized_error=InstallCiError(...), absolute_error=I…"| s12
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
    b6["filesystem_read target.read_bytes"]
    s2 -. "filesystem_read target.read_bytes" .-> b6
    click s1 "../modules/install_ci_cmd.md"
    click s2 "../modules/ci_installer.md"
    click s3 "../modules/ci_installer.md"
    click s6 "../modules/ci_installer.md"
    click s8 "../modules/ci_installer.md"
    click s9 "../modules/ci_installer.md"
    click s10 "../modules/ci_installer.md"
    click s11 "../modules/ci_installer.md"
    click s12 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `InstallCiError`, `sys` | - | `none`, `none` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | install_ci_workflow | 13 | `install_ci_workflow(action_ref=getattr(...), src_dir=getattr(...), wiki_dir=getattr(...), dry_run=bool(...), force=bool(...))` |
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

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 21 |
| output | `print` | `run` | 25 |
| output | `print` | `run` | 30 |
| output | `print` | `run` | 31 |
| output | `print` | `run` | 35 |
| output | `print` | `run` | 36 |
| filesystem_read | `target.read_bytes` | `install_ci_workflow` | 323 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `normalize_action_ref` | `isinstance` | 63 |
| unresolved_call | `normalize_action_ref` | `_ACTION_REF_RE.fullmatch` | 63 |
| unresolved_call | `normalize_action_ref` | `value.lower` | 65 |
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
