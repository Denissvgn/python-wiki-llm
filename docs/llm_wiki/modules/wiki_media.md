# wiki_media Module

**Path:** `src/llm_wiki_cli/services/wiki_media.py`

## Description

Media reference parsing for wiki pages and agent-owned assets.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `bisect` | `bisect_right` |
| `dataclasses` | `dataclass` |
| `html.parser` | `HTMLParser` |
| `os` | `os` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Iterator`, `Mapping`, `Optional`, `Union` |
| `urllib.parse` | `unquote`, `urlsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n1["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n2["src/llm_wiki_cli/services/knowledge_governance.py"]
    n3["src/llm_wiki_cli/services/knowledge_graph.py"]
    n4["src/llm_wiki_cli/services/knowledge_index.py"]
    n5["src/llm_wiki_cli/services/knowledge_links.py"]
    n6["src/llm_wiki_cli/services/knowledge_model.py"]
    n7["src/llm_wiki_cli/services/lint_service.py"]
    n8["src/llm_wiki_cli/services/site_export.py"]
    n9["src/llm_wiki_cli/services/site_html_check.py"]
    n10["src/llm_wiki_cli/services/wiki_media.py"]
    n11["src/llm_wiki_cli/services/wiki_surface_index.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n10
    n0 --> n11
    n1 --> n6
    n1 --> n10
    n1 --> n11
    n2 --> n3
    n2 --> n6
    n2 --> n10
    n3 --> n10
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n4 --> n10
    n4 --> n11
    n5 --> n6
    n5 --> n10
    n6 --> n2
    n6 --> n3
    n6 --> n10
    n7 --> n2
    n7 --> n6
    n7 --> n10
    n7 --> n11
    n8 --> n9
    n8 --> n10
    n9 --> n10
    n11 --> n10
    click n0 "../modules/documentation_run_dependencies.md"
    click n1 "../modules/documentation_wiki_input.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_graph.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_links.md"
    click n6 "../modules/knowledge_model.md"
    click n7 "../modules/lint_service.md"
    click n8 "../modules/site_export.md"
    click n9 "../modules/site_html_check.md"
    click n10 "../modules/wiki_media.md"
    click n11 "../modules/wiki_surface_index.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| Inbound | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| Inbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Inbound | [knowledge_graph](../modules/knowledge_graph.md) |
| Inbound | [knowledge_index](../modules/knowledge_index.md) |
| Inbound | [knowledge_links](../modules/knowledge_links.md) |
| Inbound | [knowledge_model](../modules/knowledge_model.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Inbound | [site_export](../modules/site_export.md) |
| Inbound | [site_html_check](../modules/site_html_check.md) |
| Inbound | [wiki_surface_index](../modules/wiki_surface_index.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [MediaReference](../entities/MediaReference.md) | 40 | — | — |
| [MarkdownLinkTarget](../entities/MarkdownLinkTarget.md) | 52 | — | — |
| [AssetIndex](../entities/AssetIndex.md) | 62 | — | — |
| [_HtmlMediaParser](../entities/HtmlMediaParser.md) | 71 | `HTMLParser` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `strip_fenced_code_blocks` | `(content: str) -> str` | — | Blank fenced code blocks while preserving line count. |
| `mask_fenced_code_blocks` | `(content: str) -> str` | — | Blank fenced code blocks without changing character offsets. |
| `_mask_inline_code_spans` | `(content: str) -> str` | — | Blank matched backtick code spans without changing offsets or newlines. |
| `_is_escaped_backtick_run` | `(content: str, offset: int) -> bool` | — | — |
| `mask_markdown_code` | `(content: str) -> str` | — | Blank fenced and inline Markdown code while preserving offsets. |
| `iter_mermaid_click_targets` | `(content: str) -> Iterator[MarkdownLinkTarget]` | — | Yield URL-bearing ``click`` directives from explicit Mermaid fences. |
| `_fence_marker` | `(line: str) -> Optional[tuple[str, int]]` | — | — |
| `_blank_line` | `(line: str) -> str` | — | — |
| `_mask_line` | `(line: str) -> str` | — | — |
| `_iter_fenced_blocks` | `(content: str) -> Iterator[tuple[str, int, int]]` | — | Yield ``(info, body_start, body_end)`` using the established policy. |
| `iter_markdown_link_targets` | `(content: str) -> Iterator[MarkdownLinkTarget]` | — | Yield inline markdown link/image targets with balanced parenthesis support. |
| `_scan_markdown_target` | `(content: str, start: int) -> Optional[tuple[str, int]]` | — | — |
| `split_srcset_candidates` | `(value: str) -> list[str]` | — | — |
| `normalize_markdown_link_target` | `(raw_target: str) -> str` | — | Return a markdown link target without optional title text. |
| `contains_uri_authority_userinfo` | `(value: str) -> bool` | — | Detect authority userinfo without scanning URI query/fragment values. |
| `_uri_candidate_contains_authority_userinfo` | `(candidate: str) -> bool` | — | — |
| `local_link_path` | `(raw_target: str) -> Optional[str]` | — | Return the path component for a local link target, or None if ignored. |
| `media_type_for_path` | `(path: str) -> Optional[str]` | — | — |
| `is_media_target` | `(raw_target: str) -> bool` | — | — |
| `collect_media_references` | `(page_path: Union[str, Path], page_rel: str, content: str) -> list[MediaReference]` | — | — |
| `_reference_definitions` | `(content: str) -> dict[str, str]` | — | — |
| `_reference_label` | `(label: str) -> str` | — | — |
| `collect_media_references_by_page` | `(wiki_dir: Union[str, Path], content_by_page: Mapping[str, str]) -> dict[str, list[MediaReference]]` | — | — |
| `build_asset_index` | `(wiki_dir: Union[str, Path], content_by_page: Optional[Mapping[str, str]] = None, references_by_page: Optional[Mapping[str, list[MediaReference]]] = None) -> AssetIndex` | — | — |
| `asset_relative_path` | `(wiki_dir: Union[str, Path], reference: MediaReference) -> Optional[str]` | — | — |
| `is_assets_path` | `(path: str) -> bool` | — | — |
| `is_unrecognized_asset_warning_path` | `(path: str) -> bool` | — | — |
| `is_symlink_escape` | `(wiki_dir: Union[str, Path], reference: MediaReference) -> bool` | — | — |
| `_absolute_normalized` | `(path: Path) -> Path` | — | — |
| `expected_page_for_asset` | `(wiki_dir: Union[str, Path], asset_rel: str) -> Optional[str]` | — | — |
| `_read_pages` | `(wiki: Path) -> dict[str, str]` | — | — |
| `_asset_files` | `(wiki: Path) -> list[str]` | — | — |
