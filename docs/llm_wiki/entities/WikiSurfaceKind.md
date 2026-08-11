# WikiSurfaceKind

**Location:** `src/llm_wiki_cli/services/wiki_surface.py:62`
**Kind:** Class
**Bases:** —
**Module:** [wiki_surface](../modules/wiki_surface.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `WikiSurfaceKind` in `src/llm_wiki_cli/services/wiki_surface.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `PageKind` | *required* | — |
| `label` | `str` | *required* | — |
| `path_pattern` | `str` | *required* | — |
| `mcp_uri_kind` | `str` | *required* | — |
| `obsidian_mirror_dir` | `Optional[str]` | *required* | — |
| `role` | `SurfaceRole` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `requires_page_id` | `() -> bool` | `@property` | — |
| `directory` | `() -> Optional[str]` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiSurfaceKind (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["_collect_directory_pages (src/llm_wiki_cli/services/wiki_surface.py)"]
    n2["_entry_for (src/llm_wiki_cli/services/wiki_surface.py)"]
    n3["_matches_directory_path (src/llm_wiki_cli/services/wiki_surface.py)"]
    n4["_matches_directory_uri (src/llm_wiki_cli/services/wiki_surface.py)"]
    n5["_surface_page (src/llm_wiki_cli/services/wiki_surface.py)"]
    n6["iter_directory_kinds (src/llm_wiki_cli/services/wiki_surface.py)"]
    n7["iter_page_kinds (src/llm_wiki_cli/services/wiki_surface.py)"]
    n8["iter_root_pages (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/wiki_surface.md"
    click n1 "../modules/wiki_surface.md"
    click n2 "../modules/wiki_surface.md"
    click n3 "../modules/wiki_surface.md"
    click n4 "../modules/wiki_surface.md"
    click n5 "../modules/wiki_surface.md"
    click n6 "../modules/wiki_surface.md"
    click n7 "../modules/wiki_surface.md"
    click n8 "../modules/wiki_surface.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 2 | `kind`, `label`, `mcp_uri_kind`, `obsidian_mirror_dir`, `path_pattern`, `role` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_collect_directory_pages` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `_entry_for` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `_matches_directory_path` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `_matches_directory_uri` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `_surface_page` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `iter_directory_kinds` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `iter_page_kinds` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
| `iter_root_pages` | type_reference | [wiki_surface](../modules/wiki_surface.md) |
