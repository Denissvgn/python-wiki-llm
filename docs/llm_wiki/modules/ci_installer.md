# ci_installer Module

**Path:** `src/llm_wiki_cli/services/ci_installer.py`

## Description

Portable installation of the managed integrity and documentation CI workflows.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory` |
| `.io` | `first_unsafe_path_component` |
| `.publication_config` | `PUBLICATION_CONFIG_PATH`, `PublicationConfigError`, `load_publication_config`, `publication_control_overlap`, `publication_path`, `publication_source_root` |
| `.source_selection` | `SourceSelectionError`, `locate_exact_repository_path`, `resolve_source_selection`, `validate_persisted_source_selection_identity` |
| `.sync_manifest` | `MANIFEST_FILENAME`, `SyncManifest`, `SyncManifestError` |
| `.validation` | `require_repository_relative_path` |
| `.wiki_lifecycle` | `WikiLifecycleState`, `classify_wiki_lifecycle` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `hashlib` | `hashlib` |
| `hmac` | `hmac` |
| `json` | `json` |
| `pathlib` | `Path` |
| `re` | `re` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/commands/install_ci_cmd.py"]
    n2["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n3["src/llm_wiki_cli/services/ci_installer.py"]
    n4["src/llm_wiki_cli/services/filesystem_guard.py"]
    n5["src/llm_wiki_cli/services/io.py"]
    n6["src/llm_wiki_cli/services/publication_config.py"]
    n7["src/llm_wiki_cli/services/source_selection.py"]
    n8["src/llm_wiki_cli/services/sync_manifest.py"]
    n9["src/llm_wiki_cli/services/validation.py"]
    n10["src/llm_wiki_cli/services/wiki_lifecycle.py"]
    n0 --> n3
    n0 --> n7
    n0 --> n9
    n1 --> n3
    n1 --> n6
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n3 --> n10
    n6 --> n7
    n6 --> n9
    n7 --> n9
    n8 --> n4
    n8 --> n5
    n8 --> n7
    n8 --> n9
    n10 --> n4
    n10 --> n5
    n10 --> n8
    click n0 "../modules/api.md"
    click n1 "../modules/install_ci_cmd.md"
    click n2 "../modules/uninstall_cmd.md"
    click n3 "../modules/ci_installer.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/io.md"
    click n6 "../modules/publication_config.md"
    click n7 "../modules/source_selection.md"
    click n8 "../modules/sync_manifest.md"
    click n9 "../modules/validation.md"
    click n10 "../modules/wiki_lifecycle.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [install_ci_cmd](../modules/install_ci_cmd.md) |
| Inbound | [uninstall_cmd](../modules/uninstall_cmd.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [validation](../modules/validation.md) |
| Outbound | [wiki_lifecycle](../modules/wiki_lifecycle.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [InstallCiError](../entities/InstallCiError.md) | 54 | `ValueError` | Raised when a portable CI workflow cannot be installed safely. |
| [InstallCiResult](../entities/InstallCiResult.md) | 59 | — | Outcome of one workflow installation attempt. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `normalize_action_ref` | `(value: object) -> str` | — | Return a canonical immutable Git commit for the reusable action. |
| `_validated_project_path` | `(value: object, *, label: str) -> str` | — | — |
| `_without_github_expression` | `(path: str, *, label: str) -> str` | — | — |
| `_portable_project_path` | `(value: object, *, label: str, allow_root: bool) -> str` | — | — |
| `_project_directory` | `(project_root: Path, relative_path: str, *, label: str) -> Path` | — | — |
| `_validate_default_selection_contract` | `(source_root: Path, wiki_dir: Path) -> None` | — | Prove the managed wiki can use default source-selection discovery. |
| `_workflow_body` | `(*, action_ref: str, src_dir: str, wiki_dir: str) -> str` | — | — |
| `render_managed_workflow` | `(*, action_ref: str, src_dir: str = '.', wiki_dir: str = 'docs/llm_wiki') -> bytes` | — | Render deterministic workflow bytes with a self-verifying owner marker. |
| `_with_ownership_checksum` | `(body: str, schema: str = MANAGED_WORKFLOW_SCHEMA) -> bytes` | — | — |
| `_normalize_newlines` | `(content: bytes) -> bytes \| None` | — | — |
| `is_unmodified_managed_workflow` | `(content: bytes, *, workflow_path: Path \| None = None) -> bool` | — | Return whether bytes carry a valid installer ownership checksum. |
| `_validate_workflow_target` | `(project_root: Path, workflow_path: Path) -> Path` | — | — |
| `install_ci_workflow` | `(*, action_ref: str, src_dir: str = '.', wiki_dir: str = 'docs/llm_wiki', dry_run: bool = False, force: bool = False, project_root: str \| Path \| None = None) -> InstallCiResult` | — | Create or safely update the repository's managed integrity workflow. |
| `install_documentation_ci_workflow` | `(*, action_ref: str, config: str = PUBLICATION_CONFIG_PATH, working_directory: str = '.', src_dir: str \| None = None, target_dir: str \| None = None, baseline: str \| None = None, reviews: str \| None = None, previous_receipt: str \| None = None, candidate_review: str \| None = None, require_ready: bool = False, dry_run: bool = False, force: bool = False, project_root: str \| Path \| None = None) -> InstallCiResult` | — | Install a read-only candidate workflow for a configured consumer project. |
| `_documentation_workflow` | `(action_ref: str, inputs: dict[str, str]) -> bytes` | — | — |
| `_project_root` | `(project_root: str \| Path \| None) -> Path` | — | — |
| `_install_workflow` | `(root: Path, workflow_path: Path, desired: bytes, canonical_ref: str, *, dry_run: bool, force: bool) -> InstallCiResult` | — | — |
