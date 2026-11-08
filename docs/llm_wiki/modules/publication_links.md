# publication_links Module

**Path:** `src/llm_wiki_cli/services/publication_links.py`

## Description

Pure Markdown rewriting and checks for portable GitHub wiki candidates.

## Imports

| Source | Symbols |
|--------|---------|
| `.markdown_sections` | `parse_markdown_document`, `normalize_markdown` |
| `.validation` | `portable_path_key`, `require_portable_relative_path` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `html` | `unescape` |
| `html.parser` | `HTMLParser` |
| `markdown_it` | `MarkdownIt` |
| `posixpath` | `posixpath` |
| `re` | `re` |
| `typing` | `Any` |
| `urllib.parse` | `quote`, `unquote`, `urlsplit`, `urlunsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/markdown_sections.py"]
    n1["src/llm_wiki_cli/services/publication_candidate.py"]
    n2["src/llm_wiki_cli/services/publication_delivery.py"]
    n3["src/llm_wiki_cli/services/publication_impact.py"]
    n4["src/llm_wiki_cli/services/publication_links.py"]
    n5["src/llm_wiki_cli/services/publication_maintenance.py"]
    n6["src/llm_wiki_cli/services/validation.py"]
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n6
    n2 --> n1
    n2 --> n4
    n3 --> n4
    n3 --> n6
    n4 --> n0
    n4 --> n6
    n5 --> n1
    n5 --> n4
    click n0 "../modules/markdown_sections.md"
    click n1 "../modules/publication_candidate.md"
    click n2 "../modules/publication_delivery.md"
    click n3 "../modules/publication_impact.md"
    click n4 "../modules/publication_links.md"
    click n5 "../modules/publication_maintenance.md"
    click n6 "../modules/validation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [publication_candidate](../modules/publication_candidate.md) |
| Inbound | [publication_delivery](../modules/publication_delivery.md) |
| Inbound | [publication_impact](../modules/publication_impact.md) |
| Inbound | [publication_maintenance](../modules/publication_maintenance.md) |
| Outbound | [markdown_sections](../modules/markdown_sections.md) |
| Outbound | [validation](../modules/validation.md) |

### External packages

| Language | Used packages | Undeclared packages |
|---|---:|---:|
| python | 1 | 1 |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_HTML](../entities/HTML.md) | 531 | `HTMLParser` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_bounded_path` | `(path: str) -> str` | — | — |
| `_path` | `(value: object) -> str` | — | — |
| `_page_path` | `(value: object) -> str` | — | — |
| `_route` | `(path: str) -> str` | — | — |
| `_parse` | `(text: str)` | — | — |
| `_record_span` | `(rule, name)` | — | — |
| `_blank` | `(text: str) -> str` | — | — |
| `_line_match` | `(text, part, start, end)` | — | — |
| `_inline_offsets` | `(text, token, offsets, cursors)` | — | — |
| `_line_offsets` | `(text: str)` | — | — |
| `_visible` | `(text: str, tokens, *, mask_links = False, environment = None) -> str` | — | — |
| `_reference_records` | `(environment)` | — | — |
| `_reference_resources` | `(visible, environment)` | — | Locate parsed definitions across list/blockquote continuation prefixes. |
| `_parsed_resources` | `(text, tokens)` | — | Locate destinations accepted by the inline parser in original source. |
| `_escaped` | `(text: str, position: int) -> bool` | — | — |
| `_destination` | `(text: str, start: int) -> tuple[int, int] \| None` | — | — |
| `_resources` | `(visible: str, *, wiki_visible = None, environment = None, parsed = ())` | — | — |
| `_url` | `(value: str)` | — | — |
| `_relative` | `(path: str, parent: str = '') -> str` | — | — |
| `_append_url` | `(path: str, parsed) -> str` | — | — |
| `_repository_link` | `(path: str, parsed, repository_url: str \| None, source_revision: str \| None) -> str` | — | — |
| `prepare_wiki_markdown` | `(text: str, *, source_path: str, source_pages: Mapping[str, str], source_assets: Mapping[str, str], repository_url: str \| None = None, source_revision: str \| None = None) -> str` | — | Rewrite declared source links without loading application code or files. |
| `_plain` | `(children) -> str` | — | — |
| `_slug` | `(text: str) -> str` | — | — |
| `_heading_coordinates` | `(tokens)` | — | — |
| `_page_html` | `(tokens)` | — | — |
| `_simple_atx_section` | `(text, anchor)` | — | Resolve only unambiguous top-level ATX documents without the optional parser. |
| `public_atx_section` | `(markdown: str, anchor: str) -> bytes \| None` | — | Return the rendered, unique plain ATX section, preserving its normalized bytes. |
| `check_github_wiki` | `(files: Mapping[str, bytes]) -> dict[str, Any]` | — | Check a complete candidate without filesystem or network access. |
