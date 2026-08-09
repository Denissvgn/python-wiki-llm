# documentation_wiki_input Module

**Path:** `src/llm_wiki_cli/services/documentation_wiki_input.py`

## Description

Read-only adoption of an existing canonical LLM Wiki.

The importer is deliberately independent from command modules.  It validates the
entire input before creating the workspace copy, copies regular files without
text decoding or newline normalization, and records enough provenance for the
documentation-run service to persist ``wiki-input.json`` later.

## Imports

| Source | Symbols |
|--------|---------|
| `.documentation_native` | `evaluate_documentation_native_freshness` |
| `.filesystem_guard` | `WindowsDirectoryGuardError`, `_WindowsDirectoryGuardUnavailableError`, `WindowsFileGuardError`, `WindowsIdentityUnavailableError`, `WindowsObjectIdentity`, `_WindowsPathHandleMetadata`, `fresh_no_follow_stat`, `guard_windows_directory_chain`, `open_windows_readonly_file`, `windows_object_identity`, `windows_object_identity_from_values`, `_windows_path_handle_metadata` |
| `.knowledge_artifacts` | `KNOWLEDGE_INDEX_FILENAME`, `KnowledgeArtifactError`, `ValidatedKnowledgeArtifacts`, `validate_knowledge_artifacts`, `validate_surface_index_bytes` |
| `.knowledge_envelope` | `KnowledgeEnvelopeError`, `hash_markdown_snapshot` |
| `.knowledge_model` | `ComputedFreshness` |
| `.knowledge_observability` | `knowledge_freshness_hint` |
| `.source_selection` | `SOURCE_SELECTION_GENERATION_INPUT_KEY`, `SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY`, `SourceSelectionError`, `resolve_source_selection`, `source_selection_identity_from_generation_inputs`, `source_selection_inputs_from_generation_inputs` |
| `.source_snapshot` | `SourceSnapshot`, `build_source_snapshot`, `capture_source_selection_inputs` |
| `.sync_manifest` | `LEGACY_MANIFEST_VERSION`, `MANIFEST_VERSION`, `ManifestArtifactHashes`, `SyncManifest`, `SyncManifestError` |
| `.validation` | `is_portable_relative_path`, `path_is_within`, `paths_overlap`, `require_portable_relative_path` |
| `.wiki_media` | `iter_markdown_link_targets`, `local_link_path`, `strip_fenced_code_blocks` |
| `.wiki_surface` | `is_safe_page_id`, `iter_page_kinds` |
| `.wiki_surface_index` | `SURFACE_INDEX_FILENAME`, `WIKI_SURFACE_INDEX_SCHEMA_VERSION` |
| `__future__` | `annotations` |
| `contextlib` | `ExitStack`, `contextmanager` |
| `dataclasses` | `dataclass`, `field` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path`, `PurePosixPath` |
| `re` | `re` |
| `shutil` | `shutil` |
| `stat` | `stat` |
| `typing` | `Any`, `Iterator`, `Mapping` |
| `urllib.parse` | `urlsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/documentation_wiki_input.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (4) |
| Outbound | `src` (13) |

> All 17 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [DocumentationWikiInputError](../entities/DocumentationWikiInputError.md) | 211 | `ValueError` | Raised when a wiki cannot be adopted without weakening isolation. |
| [DocumentationWikiSnapshot](../entities/DocumentationWikiSnapshot.md) | 231 | — | Typed provenance for an adopted, byte-preserved wiki snapshot. |
| [_InputFile](../entities/InputFile.md) | 351 | — | — |
| [_HashedInputFile](../entities/HashedInputFile.md) | 364 | — | — |
| [_InputTree](../entities/InputTree.md) | 370 | — | — |
| [_ValidatedWikiMetadata](../entities/ValidatedWikiMetadata.md) | 402 | — | One fully classified metadata form built only from guarded input bytes. |
| [_MarkdownInspection](../entities/MarkdownInspection.md) | 438 | — | — |
| [_InputResourceBudget](../entities/InputResourceBudget.md) | 447 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `documentation_wiki_input_resource_limits` | `() -> dict[str, int]` | — | Return the fixed resource policy applied to every input-tree pass. |
| `_raise_input_resource_limit` | `(*, category: str, message: str, path: str, diagnostic: str) -> None` | — | — |
| `_assert_input_files_resource_bounds` | `(files: tuple[_InputFile, ...]) -> None` | — | — |
| `_assert_input_tree_resource_bounds` | `(input_tree: _InputTree) -> None` | — | — |
| `fingerprint_documentation_wiki_input` | `(input_wiki_dir: str \| Path) -> str` | — | Return the secure tree hash used by existing-wiki adoption. |
| `adopt_documentation_wiki_snapshot` | `(input_wiki_dir: str \| Path, workspace_wiki_dir: str \| Path, *, source_root: str \| Path \| None = None, source_selection: str \| Path \| None = None, freshness_policy: str = 'require-current') -> DocumentationWikiSnapshot` | — | Validate and copy an existing LLM Wiki into an isolated workspace. |
| `_adopt_documentation_wiki_snapshot_with_runtime` | `(input_wiki_dir: str \| Path, workspace_wiki_dir: str \| Path, *, source_root: str \| Path \| None, source_selection: str \| Path \| None, freshness_policy: str, trust_source_plugins: bool, helper_cache_dir: str \| Path \| None) -> DocumentationWikiSnapshot` | — | Adopt with controller-approved native live-evaluation inputs. |
| `_adopt_validated_wiki_snapshot` | `(input_root: Path, workspace_root: Path, *, source_root: Path \| None, source_selection: str \| Path \| None, freshness_policy: str, root_descriptor: int \| None, trust_source_plugins: bool, helper_cache_dir: str \| Path \| None) -> DocumentationWikiSnapshot` | — | Adopt from already validated roots while the input root remains pinned. |
| `_validate_freshness_policy` | `(policy: str) -> None` | — | — |
| `_validate_input_root` | `(path: str \| Path) -> tuple[Path, os.stat_result]` | — | — |
| `_validate_workspace_root` | `(path: str \| Path) -> Path` | — | — |
| `_validate_source_root` | `(path: str \| Path \| None) -> Path \| None` | — | — |
| `_validate_root_isolation` | `(input_root: Path, workspace_root: Path, source_root: Path \| None) -> None` | — | — |
| `_paths_overlap` | `(left: Path, right: Path) -> bool` | — | — |
| `_is_relative_to` | `(path: Path, root: Path) -> bool` | — | — |
| `_supports_secure_input_fd_traversal` | `() -> bool` | — | — |
| `_uses_windows_guarded_input_fallback` | `() -> bool` | — | — |
| `_input_directory_open_flags` | `(*, root: bool = False) -> int` | — | — |
| `_open_input_root_descriptor` | `(root: Path, *, expected_identity: os.stat_result) -> Iterator[int \| None]` | `@contextmanager` | Pin a POSIX input root for the complete validation/copy transaction. |
| `_assert_input_root_path_binding` | `(root: Path, descriptor: int) -> None` | — | — |
| `_assert_input_directory` | `(entry_stat: os.stat_result, *, path: str) -> None` | — | — |
| `_assert_same_input_identity` | `(expected: os.stat_result, actual: os.stat_result, *, path: str, operation: str) -> None` | — | — |
| `_assert_windows_input_identity` | `(expected: os.stat_result, actual: os.stat_result, *, path: str, operation: str) -> None` | — | — |
| `_stable_input_metadata` | `(entry_stat: os.stat_result) -> tuple[int, int, int, int]` | — | — |
| `_assert_stable_input_metadata` | `(before: os.stat_result, after: os.stat_result, *, path: str) -> None` | — | — |
| `_assert_windows_path_handle_metadata` | `(path_metadata: _WindowsPathHandleMetadata, handle_metadata: _WindowsPathHandleMetadata, *, path: str, operation: str) -> None` | — | — |
| `_collect_input_tree` | `(root: Path, *, enforce_content_policy: bool, root_descriptor: int \| None = None) -> _InputTree` | — | — |
| `_collect_input_tree_descriptor` | `(root: Path, root_descriptor: int, *, enforce_content_policy: bool) -> _InputTree` | — | Inventory an input tree without resolving any child through a pathname. |
| `_open_input_directory_at` | `(parent_descriptor: int, name: str, relative_path: str, *, inspected: os.stat_result) -> int` | — | — |
| `_assert_input_regular` | `(entry_stat: os.stat_result, *, path: str) -> None` | — | — |
| `_open_input_regular_at` | `(parent_descriptor: int, name: str, relative_path: str, *, inspected: os.stat_result) -> tuple[int, os.stat_result]` | — | — |
| `_hash_input_file_at` | `(parent_descriptor: int, name: str, relative_path: str, *, inspected: os.stat_result) -> _HashedInputFile` | — | — |
| `_open_windows_input_leaf` | `(path: Path, relative_path: str, *, expected_stat: os.stat_result \| None = None, expected_entry: _InputFile \| None = None)` | `@contextmanager` | Open a fallback input leaf while its Windows parent chain is pinned. |
| `_open_input_entry` | `(entry: _InputFile)` | `@contextmanager` | Open an inventoried file through its pinned input root when available. |
| `_validate_portable_relative_path` | `(relative: PurePosixPath, seen: dict[str, str]) -> None` | — | — |
| `_is_reparse_point` | `(entry_stat: os.stat_result) -> bool` | — | — |
| `_is_rejected_content` | `(relative: PurePosixPath, entry_stat: os.stat_result) -> bool` | — | — |
| `_ensure_resolved_inside` | `(path: Path, root: Path, relative_path: str) -> None` | — | — |
| `_hash_regular_file` | `(path: Path, relative_path: str, *, expected_size: int \| None = None, maximum_bytes: int \| None = None, expected_stat: os.stat_result \| None = None, windows_guarded: bool = False) -> _HashedInputFile` | — | — |
| `_open_regular_file` | `(path: Path, relative_path: str)` | — | — |
| `_tree_hash` | `(files: tuple[_InputFile, ...]) -> str` | — | — |
| `_load_and_validate_metadata` | `(files: Mapping[str, _InputFile]) -> _ValidatedWikiMetadata` | — | — |
| `_read_json_object` | `(entry: _InputFile, label: str) -> dict[str, Any]` | — | — |
| `_decode_json_object` | `(raw: bytes, entry: _InputFile, label: str) -> dict[str, Any]` | — | — |
| `_read_verified_bytes` | `(entry: _InputFile) -> bytes` | — | — |
| `_validated_manifest_version` | `(manifest: Mapping[str, Any]) -> int` | — | — |
| `_validated_sync_manifest` | `(manifest: Mapping[str, Any]) -> SyncManifest` | — | — |
| `_validate_legacy_manifest` | `(manifest: Mapping[str, Any]) -> None` | — | — |
| `_validate_generation_inputs` | `(generation_inputs: Mapping[str, Any]) -> None` | — | — |
| `_validated_native_surface` | `(surface_bytes: bytes) -> Mapping[str, Any]` | — | — |
| `_validated_native_artifacts` | `(*, surface_bytes: bytes, knowledge_bytes: bytes, manifest: SyncManifest) -> ValidatedKnowledgeArtifacts` | — | — |
| `_validate_native_marker` | `(marker: ManifestArtifactHashes, validated: ValidatedKnowledgeArtifacts) -> None` | — | — |
| `_validate_native_page_parity` | `(surface: Mapping[str, Any], files: Mapping[str, _InputFile]) -> Mapping[str, _InputFile]` | — | — |
| `_canonical_markdown_entries` | `(files: Mapping[str, _InputFile]) -> dict[str, _InputFile]` | — | — |
| `_validate_native_markdown_snapshot` | `(canonical_markdown: Mapping[str, _InputFile], files: Mapping[str, _InputFile], validated: ValidatedKnowledgeArtifacts) -> None` | — | — |
| `_validate_surface_index` | `(surface: Mapping[str, Any], files: Mapping[str, _InputFile]) -> None` | — | — |
| `_is_safe_posix_relative` | `(value: str) -> bool` | — | — |
| `_is_sha256` | `(value: object) -> bool` | — | — |
| `_unknown_entries` | `(files: tuple[_InputFile, ...]) -> tuple[str, ...]` | — | — |
| `_is_known_wiki_path` | `(relative_path: str) -> bool` | — | — |
| `_inspect_markdown` | `(files: tuple[_InputFile, ...]) -> _MarkdownInspection` | — | — |
| `_assert_semantic_markdown_resource_bounds` | `(markdown_files: tuple[_InputFile, ...]) -> int` | — | — |
| `_generated_marker_record` | `(content: str, match: re.Match[str]) -> dict[str, Any]` | — | — |
| `_hash_text_span` | `(content: str, start: int, end: int) -> tuple[str, int]` | — | — |
| `_build_generated_marker_evidence` | `(marker_counts: Mapping[str, int], captured_markers: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]` | — | — |
| `_generated_marker_evidence_payload` | `(marker_counts: Mapping[str, int], captured_markers: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]` | — | — |
| `_validate_markdown_link_targets` | `(relative_path: str, content: str) -> None` | — | — |
| `_semantic_page_records` | `(files: tuple[_InputFile, ...], surface: Mapping[str, Any] \| None, *, generated_marker_counts: Mapping[str, int]) -> tuple[Mapping[str, Any], ...]` | — | — |
| `_resolve_metadata_freshness` | `(metadata: _ValidatedWikiMetadata, *, source_root: Path \| None, source_selection: str \| Path \| None, trust_source_plugins: bool, helper_cache_dir: str \| Path \| None) -> tuple[str, tuple[str, ...], list[str], tuple[Mapping[str, str], ...]]` | — | Select legacy comparison or the fail-closed native evaluation seam. |
| `_basis_incompatible_diagnostics` | `(report: object) -> tuple[Mapping[str, str], ...]` | — | — |
| `_resolve_freshness` | `(manifest: Mapping[str, Any] \| None, *, legacy: bool, source_root: Path \| None, source_selection: str \| Path \| None) -> tuple[str, tuple[str, ...], list[str]]` | — | — |
| `_compare_generation_inputs` | `(source_root: Path, generation_inputs: Mapping[str, Any], *, source_snapshot: SourceSnapshot) -> list[str]` | — | — |
| `_compare_source_file` | `(source_root: Path, relative_path: str, expected_hash: str) -> str \| None` | — | — |
| `_enforce_freshness_policy` | `(policy: str, freshness: str, *, source_available: bool, diagnostics: list[str]) -> bool` | — | — |
| `_require_empty_workspace` | `(workspace_root: Path) -> None` | — | — |
| `_rollback_partial_workspace_snapshot` | `(workspace_root: Path, *, expected_identity: os.stat_result, preserve_root: bool) -> None` | — | Remove only the empty workspace root populated by this adoption attempt. |
| `_supports_secure_directory_fd_copy` | `() -> bool` | — | Return whether descriptor-relative, no-follow output creation is available. |
| `_uses_windows_guarded_copy_fallback` | `() -> bool` | — | — |
| `_workspace_identity` | `(entry_stat: os.stat_result, *, path: Path \| str, operation: str) -> tuple[int, int] \| WindowsObjectIdentity` | — | — |
| `_assert_same_workspace_identity` | `(expected: os.stat_result, actual: os.stat_result, *, path: Path \| str, operation: str) -> None` | — | — |
| `_assert_safe_workspace_directory` | `(entry_stat: os.stat_result, *, path: Path \| str) -> None` | — | — |
| `_assert_safe_workspace_file` | `(entry_stat: os.stat_result, *, path: Path \| str) -> None` | — | — |
| `_workspace_lstat` | `(path: Path, *, operation: str) -> os.stat_result` | — | — |
| `_canonical_path_key` | `(path: Path) -> str` | — | — |
| `_assert_workspace_path_bounded` | `(path: Path, workspace_root: Path, *, operation: str) -> None` | — | — |
| `_inspect_workspace_root` | `(workspace_root: Path) -> os.stat_result` | — | — |
| `_open_workspace_root_descriptor` | `(workspace_root: Path) -> tuple[int \| None, os.stat_result]` | — | — |
| `_copy_input_tree` | `(input_tree: _InputTree, workspace_root: Path) -> None` | — | — |
| `_open_or_create_workspace_subdirectory` | `(parent_descriptor: int, component: str, *, relative_path: PurePosixPath) -> int` | — | — |
| `_open_workspace_destination_at` | `(relative: PurePosixPath, *, root_descriptor: int) -> tuple[int, int, os.stat_result]` | — | — |
| `_assert_workspace_fallback_chain` | `(workspace_root: Path, relative_parent: PurePosixPath, *, root_identity: os.stat_result) -> tuple[Path, os.stat_result]` | — | — |
| `_open_workspace_destination_fallback` | `(relative: PurePosixPath, *, workspace_root: Path, root_identity: os.stat_result) -> tuple[int, Path, os.stat_result, os.stat_result]` | — | — |
| `_copy_file_bytes` | `(entry: _InputFile, destination_descriptor: int) -> tuple[str, os.stat_result]` | — | — |
| `_copy_regular_file` | `(entry: _InputFile, workspace_root: Path, *, root_descriptor: int \| None, root_identity: os.stat_result) -> None` | — | — |
