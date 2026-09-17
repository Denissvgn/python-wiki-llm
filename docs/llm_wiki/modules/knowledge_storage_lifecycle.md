# knowledge_storage_lifecycle Module

**Path:** `src/llm_wiki_cli/services/knowledge_storage_lifecycle.py`

## Description

Owns explicit storage and manifest migration, verified recovery, legacy export and cleanup. Migration preserves authored Markdown and governance, writes referenced objects before committing the manifest, and retains recovery evidence outside the wiki. Recovery binds both knowledge and manifest roots; cleanup removes only recognized unreachable objects after validating the current generation.

Validate the committed indexed generation and enumerate owned knowledge and manifest object namespaces. Retain unknown or malformed entries. Applying the preview rechecks current authority and each deletion preimage before removing recognized unreachable files.

Cleanup plans bind the generation, root and exact candidate bytes. Apply verifies shared recovery preimages before deletion and retains unknown, busy or over-budget work. Recovery can restore absent owned files without changing current authority.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory`, `unlink_guarded_bytes` |
| `.knowledge_artifacts` | `ArtifactWriteState`, `KnowledgeCommitPlan`, `PlannedArtifactWrite`, `build_knowledge_commit_plan`, `commit_knowledge_artifacts`, `current_knowledge_format`, `validate_knowledge_artifacts`, `validated_artifact_bytes`, `_commit_sharded` |
| `.knowledge_governance` | `GOVERNANCE_FILENAME`, `governance_lock` |
| `.knowledge_index` | `serialize_knowledge_index` |
| `.knowledge_loader` | `load_knowledge_state` |
| `.knowledge_packs` | `PACKED_SCHEMA`, `LOCAL_PACKED_SCHEMA`, `PACKED_SCHEMAS`, `PACKED_FORMATS`, `packed_format`, `PACK_NAME`, `INDEX_NAME`, `PACK_DIRECTORY`, `PACK_INDEX_DIRECTORY`, `INDEX_PAGE_NAME`, `INDEX_PAGE_DIRECTORY`, `PackedKnowledgeStoreReader`, `inspect_pack`, `inspect_index_pages` |
| `.knowledge_storage` | `MAX_EXPANDED_BYTES`, `MAX_OBJECT_BYTES`, `OBJECT_DIRECTORY`, `ROOT_FILENAME`, `GIT_FAILURE_BYTES`, `KnowledgeStorageError`, `KnowledgeStoreReader`, `decode_bytes`, `canonical_bytes`, `digest`, `_hash`, `decode_bytes` |
| `.knowledge_storage_io` | `StorageReadSession`, `read_guarded`, `_absolute_path` |
| `.manifest_storage` | `OBJECT_NAME`, `DIRECTORY`, `validate_catalog` |
| `.storage_spool` | `ByteSpool`, `ByteSpool` |
| `.sync_manifest` | `MANIFEST_FILENAME`, `SyncManifest` |
| `.wiki_surface_index` | `SURFACE_INDEX_FILENAME` |
| `__future__` | `annotations` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `subprocess` | `subprocess` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_storage_lifecycle.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (2) |
| Outbound | `src` (12) |

> All 14 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_committed_inputs` | `(wiki_dir: str \| Path)` | — | — |
| `_default_recovery_directory` | `(root: Path, root_hash: str) -> Path \| None` | — | — |
| `_outside_tree` | `(directory: Path, root: Path) -> Path` | — | — |
| `_backup` | `(directory: Path, files: dict[str, bytes], target_hash: str, target_manifest_hash: str) -> None` | — | — |
| `migrate_knowledge_storage` | `(wiki_dir: str \| Path, *, dry_run: bool = False, recovery_dir: str \| Path \| None = None, to: str = 'sharded-v2') -> dict[str, Any]` | — | Explicitly adopt indexed storage, retaining verified recovery bytes outside the wiki. |
| `_read_recovery` | `(directory: Path) -> tuple[dict[str, Any], dict[str, bytes]]` | — | — |
| `recover_knowledge_storage` | `(wiki_dir: str \| Path, recovery_dir: str \| Path, *, dry_run: bool = False) -> dict[str, Any]` | — | Restore an exact interrupted migration; refuse unrelated newer roots. |
| `export_knowledge_v1` | `(wiki_dir: str \| Path, output: str \| Path) -> dict[str, Any]` | — | — |
| `is_storage_path` | `(relative: str) -> bool` | — | — |
| `stored_object_paths` | `(wiki_dir: str \| Path) -> tuple[list[str], list[str]]` | — | Bounded enumeration of the owned two-level object namespace, without links. |
| `_prune_plan` | `(root, root_bytes, manifest_bytes, candidates)` | — | — |
| `_prune_backup` | `(root, directory, plan, candidates, cancelled)` | — | — |
| `prune_knowledge_storage` | `(wiki_dir: str \| Path, *, dry_run: bool = True, plan = None, recovery_dir: str \| Path \| None = None, max_bytes: int = MAX_EXPANDED_BYTES, cancelled = None) -> dict[str, Any]` | — | Preview or apply an exact generation-bound cleanup with verified recovery. |
| `_prune_storage` | `(wiki_dir, *, dry_run, plan, recovery_dir, safe, cancelled)` | — | Remove only valid content-addressed objects unreachable from a full audit. |
| `restore_pruned_storage` | `(wiki_dir: str \| Path, recovery_manifest: str \| Path, *, dry_run: bool = True, cancelled = None) -> dict[str, Any]` | — | Restore verified cleanup preimages without overwriting differing files. |