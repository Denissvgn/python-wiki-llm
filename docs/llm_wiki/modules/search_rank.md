# search_rank Module

**Path:** `src/llm_wiki_cli/services/search_rank.py`

## Description

Ranks wiki pages offline using lexical, title, path, symbol, and internal-link
signals, with precedence for exact page identities. Results expose matching
reasons, content hashes, and the ranking version, with stable ordering shared by
CLI and MCP consumers. The scan is bounded to 10,000 pages and 64 MiB of UTF-8
content; callers can restrict the selected wiki or page kinds to fit the limits.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections` | `Counter` |
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
    n0["src/llm_wiki_cli/services/search_lexical.py"]
    n1["src/llm_wiki_cli/services/search_rank.py"]
    n2["src/llm_wiki_cli/services/search_service.py"]
    n3["src/llm_wiki_cli/services/search_source.py"]
    n0 --> n1
    n2 --> n0
    n2 --> n1
    n2 --> n3
    n3 --> n1
    click n0 "../modules/search_lexical.md"
    click n1 "../modules/search_rank.md"
    click n2 "../modules/search_service.md"
    click n3 "../modules/search_source.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [search_lexical](../modules/search_lexical.md) |
| Inbound | [search_service](../modules/search_service.md) |
| Inbound | [search_source](../modules/search_source.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_tokens` | `(text)` | — | — |
| `rank_pages` | `(pages, query: str, *, limit = 20, max_pages = MAX_SEARCH_PAGES, max_bytes = MAX_SEARCH_BYTES) -> dict` | — | Consume page records once; retain compact matches and local link counts. |