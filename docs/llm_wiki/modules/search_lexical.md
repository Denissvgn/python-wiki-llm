# search_lexical Module

**Path:** `src/llm_wiki_cli/services/search_lexical.py`

## Description

Pure informative lexical discovery; matches never establish source truth.

## Imports

| Source | Symbols |
|--------|---------|
| `.markdown_sections` | `parse_markdown_document`, `semantic_table_key`, `split_table_row` |
| `.search_rank` | `MAX_SEARCH_BYTES`, `MAX_SEARCH_PAGES`, `_tokens` |
| `.wiki_media` | `mask_fenced_code_blocks` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping` |
| `copy` | `deepcopy` |
| `hashlib` | `hashlib` |
| `math` | `math` |
| `posixpath` | `posixpath` |
| `re` | `re` |
| `unicodedata` | `unicodedata` |
| `urllib.parse` | `unquote`, `urlsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/markdown_sections.py"]
    n1["src/llm_wiki_cli/services/search_lexical.py"]
    n2["src/llm_wiki_cli/services/search_rank.py"]
    n3["src/llm_wiki_cli/services/search_service.py"]
    n4["src/llm_wiki_cli/services/wiki_media.py"]
    n1 --> n0
    n1 --> n2
    n1 --> n4
    n3 --> n1
    n3 --> n2
    click n0 "../modules/markdown_sections.md"
    click n1 "../modules/search_lexical.md"
    click n2 "../modules/search_rank.md"
    click n3 "../modules/search_service.md"
    click n4 "../modules/wiki_media.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [search_service](../modules/search_service.md) |
| Outbound | [markdown_sections](../modules/markdown_sections.md) |
| Outbound | [search_rank](../modules/search_rank.md) |
| Outbound | [wiki_media](../modules/wiki_media.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_normal` | `(text)` | — | — |
| `_fields` | `(page)` | — | Disjoint captured spans; child sections do not multiply parent evidence. |
| `_identity_tier` | `(page, needle, definitions)` | — | — |
| `rank_pages` | `(pages, query: str, *, limit = 20, max_pages = MAX_SEARCH_PAGES, max_bytes = MAX_SEARCH_BYTES) -> dict` | — | Rank only supplied captured text within honest, fail-closed work bounds. |
