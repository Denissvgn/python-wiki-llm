# publication_snapshot Module

**Path:** `src/llm_wiki_cli/services/publication_snapshot.py`

## Description

Complete, read-only native page commitments for documentation publication.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `EXCLUDED_DIRS`, `GitIgnoreMatcher`, `is_agent_worktree_path` |
| `.bootstrap_runtime` | `execute_bootstrap` |
| `.bootstrap_service` | `BootstrapRequest`, `BootstrapServiceError` |
| `.contracts` | `GOVERNANCE_EXTENSION_KEY`, `SECTION_OWNERSHIP_EXTENSION_KEY` |
| `.documentation_native` | `DocumentationNativeError`, `evaluate_documentation_native_freshness` |
| `.helper_runtime` | `helper_operation`, `helper_operation` |
| `.io` | `decode_markdown_bytes` |
| `.knowledge_evidence` | `hash_json`, `sha256_bytes` |
| `.knowledge_governance` | `GOVERNANCE_FILENAME` |
| `.knowledge_model` | `_bundle_to_payload` |
| `.knowledge_storage` | `MAX_EXPANDED_BYTES`, `KnowledgeStorageError` |
| `.knowledge_storage_io` | `_absolute_path` |
| `.knowledge_storage_lifecycle` | `_committed_inputs` |
| `.maintenance_protocol` | `guard_maintenance_owner` |
| `.markdown_sections` | `parse_markdown_document` |
| `.source_snapshot` | `_is_compose_candidate`, `_is_dockerfile_candidate`, `_is_package_marker`, `_is_rescuable_typescript_src_lib_file`, `_language_for_path`, `_unsupported_language_for_path`, `build_source_snapshot` |
| `.sync_manifest` | `MANIFEST_FILENAME` |
| `.validation` | `require_portable_relative_path` |
| `.wiki_surface` | `collect_wiki_pages` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `copy` | `deepcopy` |
| `os` | `os` |
| `pathlib` | `Path` |
| `tempfile` | `TemporaryDirectory` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/publication_snapshot.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/publication_snapshot.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (2) |
| Outbound | `src` (19) |

> All 21 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PublicationSnapshotError](../entities/PublicationSnapshotError.md) | 30 | `ValueError` | A complete, coherent publication input could not be established. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_output_payload_path` | `(value: object) -> str` | — | — |
| `assert_bootstrap_output_excluded` | `(source_root: Path, destination: Path, files: Mapping[str, bytes]) -> None` | — | Reject future output files that would become bootstrap producer inputs. |
| `build_publication_snapshot` | `(wiki_dir: str \| Path, *, source_root: Path \| None = None) -> dict[str, Any]` | — | Commit every canonical native page and optionally verify its live source. |
| `build_bootstrap_publication_snapshot` | `(source_root: Path) -> dict[str, Any]` | — | Build an isolated source-adapter wiki and return its native commitments. |
| `_build_snapshot` | `(root: Path, source_root: Path \| None = None) -> dict[str, Any]` | — | — |
