# inventory_cache Module

**Path:** `src/llm_wiki_cli/services/inventory_cache.py`

## Description

Persistent inventory cache used by lint and CI validation.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `__version__` |
| `..extractors.common` | `LANGUAGE_EXTENSIONS` |
| `.analysis_capture` | `capture_analysis` |
| `.analysis_compatibility` | `digest` |
| `.domain_pack` | `current_pack` |
| `.extractor_registry` | `COMPOSE_PATTERNS`, `DOCKERFILE_PATTERNS` |
| `.io` | `write_json_atomic` |
| `.path_policy` | `AGENT_WORKTREE_DIR_PATTERNS`, `EXCLUDED_DIRS`, `is_agent_worktree_path` |
| `.plugins` | `lock_path`, `plugin_store` |
| `.source_snapshot` | `SourceFile`, `SourceSnapshot` |
| `__future__` | `annotations` |
| `dataclasses` | `asdict`, `dataclass`, `field`, `replace` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine.knowledge_evidence` | `hash_json` |
| `llm_wiki_engine.progress` | `observed_phase` |
| `llm_wiki_engine.runtime_output` | `RuntimeDestination`, `RuntimeOutputError`, `WarningSink`, `prepare_destination`, `stderr_warning`, `warn` |
| `os` | `os` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/inventory_cache.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/inventory_cache.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (9) |
| Outbound | `src` (13) |

> All 22 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [InventoryCacheOptions](../entities/InventoryCacheOptions.md) | 37 | — | Runtime cache controls for inventory-producing commands. |
| [InventoryCacheStats](../entities/InventoryCacheStats.md) | 51 | — | — |
| [InventoryCache](../entities/InventoryCache.md) | 373 | — | JSON-backed cache for per-file built-in inventory entries. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `format_cache_stats` | `(stats: InventoryCacheStats) -> list[str]` | — | Return human-readable inventory cache diagnostics. |
| `_sha256_bytes` | `(data: bytes) -> str` | — | — |
| `_hash_json` | `(value: Any) -> str` | — | — |
| `_hash_file` | `(path: Path) -> str \| None` | — | — |
| `hash_source_file` | `(source_file: SourceFile) -> str \| None` | — | Return a content hash for a source file, or None when unreadable. |
| `_hash_labeled_files` | `(paths: list[tuple[str, Path]]) -> str` | — | — |
| `_path_has_excluded_part` | `(path: Path) -> bool` | — | — |
| `_gitignore_fingerprint` | `(root: Path) -> str` | — | — |
| `_implementation_fingerprint` | `() -> str` | — | — |
| `_plugin_fingerprint` | `(root: Path) -> str` | — | — |
| `_filter_fingerprint` | `() -> str` | — | — |
| `build_inventory_cache_key` | `(src_dir: str \| Path, source_snapshot: SourceSnapshot, *, deep: bool, include_empty: bool, extractor_registry: dict[str, str], helper_cache_dir: str \| None = None) -> dict[str, Any] \| None` | — | Return a cache key only if all selected bundled helpers were observed. |
| `_resolve_gitdir_file` | `(git_file: Path) -> Path \| None` | — | — |
| `_nearest_git_dir` | `(start: Path) -> Path \| None` | — | — |
| `resolve_inventory_cache_path` | `(src_dir: str \| Path, cache_dir: str \| None = None, *, env: dict[str, str] \| None = None) -> Path \| None` | — | Resolve the cache file path for a source tree and optional override. |
| `cache_options_from_args` | `(args) -> InventoryCacheOptions` | — | — |
| `cache_options_for` | `(*, disabled: bool = False, rebuild: bool = False, cache_dir: str \| None = None, stats_enabled: bool = False) -> InventoryCacheOptions` | — | Validated inventory cache options for one run. |
| `prepare_cache_options` | `(src_dir: str \| Path, options: InventoryCacheOptions \| None) -> InventoryCacheOptions \| None` | — | — |
| `is_valid_cache_entry` | `(entry: Any, source_file: SourceFile, file_hash: str) -> bool` | — | — |
| `make_cache_entry` | `(source_file: SourceFile, file_hash: str, inventory_entry: dict) -> dict` | — | — |
| `extraction_bundle_hash` | `(entry: dict) -> str` | — | Commit every raw analysis value reused together, excluding file metadata. |
