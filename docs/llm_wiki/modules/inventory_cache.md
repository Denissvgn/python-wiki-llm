# inventory_cache Module

**Path:** `src/llm_wiki_cli/services/inventory_cache.py`

## Description

Persistent inventory cache used by lint and CI validation.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `__version__` |
| `..config` | `AGENT_WORKTREE_DIR_PATTERNS`, `COMPOSE_PATTERNS`, `DOCKERFILE_PATTERNS`, `EXCLUDED_DIRS`, `is_agent_worktree_path` |
| `..extractors.common` | `LANGUAGE_EXTENSIONS` |
| `.plugins` | `lock_path`, `plugin_store` |
| `.source_snapshot` | `SourceFile`, `SourceSnapshot` |
| `__future__` | `annotations` |
| `dataclasses` | `asdict`, `dataclass` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/ci_check_cmd.py"]
    n1["src/llm_wiki_cli/commands/sync_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/extractors/common.py"]
    n4["src/llm_wiki_cli/services/documentation_native.py"]
    n5["src/llm_wiki_cli/services/documentation_run/integrity.py"]
    n6["src/llm_wiki_cli/services/extraction_service.py"]
    n7["src/llm_wiki_cli/services/extractor_helpers.py"]
    n8["src/llm_wiki_cli/services/inventory_cache.py"]
    n9["src/llm_wiki_cli/services/lint_service.py"]
    n10["src/llm_wiki_cli/services/plugins.py"]
    n11["src/llm_wiki_cli/services/source_snapshot.py"]
    n0 --> n2
    n0 --> n8
    n0 --> n9
    n1 --> n2
    n1 --> n6
    n1 --> n8
    n1 --> n10
    n1 --> n11
    n3 --> n2
    n4 --> n6
    n4 --> n8
    n4 --> n11
    n5 --> n8
    n5 --> n9
    n6 --> n2
    n6 --> n3
    n6 --> n8
    n6 --> n10
    n6 --> n11
    n7 --> n8
    n8 --> n2
    n8 --> n3
    n8 --> n10
    n8 --> n11
    n9 --> n2
    n9 --> n3
    n9 --> n6
    n9 --> n8
    n9 --> n10
    n9 --> n11
    n10 --> n2
    n11 --> n2
    n11 --> n3
    click n0 "../modules/ci_check_cmd.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/common.md"
    click n4 "../modules/documentation_native.md"
    click n5 "../modules/integrity.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extractor_helpers.md"
    click n8 "../modules/inventory_cache.md"
    click n9 "../modules/lint_service.md"
    click n10 "../modules/plugins.md"
    click n11 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [ci_check_cmd](../modules/ci_check_cmd.md) |
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Inbound | [documentation_native](../modules/documentation_native.md) |
| Inbound | [integrity](../modules/integrity.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [extractor_helpers](../modules/extractor_helpers.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [common](../modules/common.md) |
| Outbound | [plugins](../modules/plugins.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [InventoryCacheOptions](../entities/InventoryCacheOptions.md) | 32 | — | Runtime cache controls for inventory-producing commands. |
| [InventoryCacheStats](../entities/InventoryCacheStats.md) | 42 | — | — |
| [InventoryCache](../entities/InventoryCache.md) | 280 | — | JSON-backed cache for per-file built-in inventory entries. |

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
| `build_inventory_cache_key` | `(src_dir: str \| Path, source_snapshot: SourceSnapshot, *, deep: bool, include_empty: bool, extractor_registry: dict[str, str]) -> dict[str, Any]` | — | Build cache metadata that must match before entries are reused. |
| `_resolve_gitdir_file` | `(git_file: Path) -> Path \| None` | — | — |
| `_nearest_git_dir` | `(start: Path) -> Path \| None` | — | — |
| `resolve_inventory_cache_path` | `(src_dir: str \| Path, cache_dir: str \| None = None, *, env: dict[str, str] \| None = None) -> Path \| None` | — | Resolve the cache file path for a source tree and optional override. |
| `is_valid_cache_entry` | `(entry: Any, source_file: SourceFile, file_hash: str) -> bool` | — | — |
| `make_cache_entry` | `(source_file: SourceFile, file_hash: str, inventory_entry: dict) -> dict` | — | — |
