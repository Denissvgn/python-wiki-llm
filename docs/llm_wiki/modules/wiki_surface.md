# wiki_surface Module

**Path:** `src/llm_wiki_cli/services/wiki_surface.py`

## Description

Canonical wiki page surface registry.

This module only describes and collects pages that already exist under a wiki
directory. It intentionally avoids source inventory and command-module imports.

## Imports

| Source | Symbols |
|--------|---------|
| `.validation` | `is_portable_path_component`, `path_is_in_top_level_directory` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Optional`, `Union` |
| `urllib.parse` | `quote`, `unquote` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/wiki_surface.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/wiki_surface.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (30) |
| Outbound | `src` (1) |

> All 31 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [WikiSurfaceError](../entities/WikiSurfaceError.md) | Class | 25 | `ValueError` | Raised for invalid wiki surface lookups. |
| [WikiSurfacePathError](../entities/WikiSurfacePathError.md) | Class | 32 | `WikiSurfaceError` | Raised when a canonical page path cannot be read inside its wiki root. |
| [PageKind](../entities/PageKind.md) | Enum | 41 | `str`, `Enum` | — |
| [SurfaceRole](../entities/SurfaceRole.md) | Enum | 55 | `str`, `Enum` | — |
| [WikiSurfaceKind](../entities/WikiSurfaceKind.md) | Class | 62 | — | — |
| [WikiSurfacePage](../entities/WikiSurfacePage.md) | Class | 82 | — | — |
| [WikiAssetSurface](../entities/WikiAssetSurface.md) | Class | 94 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `iter_page_kinds` | `() -> tuple[WikiSurfaceKind, ...]` | — | Return all canonical page kinds in display/collection order. |
| `asset_surface` | `() -> WikiAssetSurface` | — | Return the canonical agent-owned media asset surface. |
| `iter_root_pages` | `() -> tuple[WikiSurfaceKind, ...]` | — | Return top-level page kinds in canonical order. |
| `iter_directory_kinds` | `() -> tuple[WikiSurfaceKind, ...]` | — | Return directory-backed page kinds in canonical order. |
| `is_safe_page_id` | `(page_id: str) -> bool` | — | Return True when a page id can safely map to one Markdown filename. |
| `canonical_path` | `(kind: Union[PageKind, str], page_id: Optional[str] = None) -> str` | — | Return the canonical POSIX relative path for a wiki page. |
| `mcp_uri` | `(kind: Union[PageKind, str], page_id: Optional[str] = None) -> str` | — | Return the canonical MCP URI for a wiki page. |
| `validate_exact_page_coordinate` | `(value: object) -> str` | — | Validate and return one canonical wiki path or MCP URI coordinate. |
| `collect_wiki_pages` | `(wiki_dir: Union[str, Path]) -> list[WikiSurfacePage]` | — | Collect active canonical wiki pages in deterministic registry order. |
| `_collect_directory_pages` | `(wiki: Path, entry: WikiSurfaceKind) -> list[WikiSurfacePage]` | — | — |
| `_surface_page` | `(wiki: Path, path: Path, entry: WikiSurfaceKind, page_id: str) -> WikiSurfacePage` | — | — |
| `resolve_wiki_page_path` | `(wiki_dir: Union[str, Path], path: Union[str, Path]) -> Path` | — | Resolve one canonical page while rejecting nested symlinks and escapes. |
| `_entry_for` | `(kind: Union[PageKind, str]) -> WikiSurfaceKind` | — | — |
| `_validate_page_id` | `(page_id: Optional[str], *, required: bool) -> str` | — | — |
| `_matches_directory_path` | `(coordinate: str, entry: WikiSurfaceKind) -> bool` | — | — |
| `_matches_directory_uri` | `(coordinate: str, entry: WikiSurfaceKind) -> bool` | — | — |
| `_is_legacy_path` | `(path: Path, wiki: Path) -> bool` | — | — |
