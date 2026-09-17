# search_service Module

**Path:** `src/llm_wiki_cli/services/search_service.py`

## Description

Shares wiki page discovery and ranked or substring search across public consumers. Ranking preserves exact identities, reasons, corpus commitments and collection bounds without introducing an MCP dependency into ordinary Python or CLI search.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `wiki_surface` |
| `..config` | `validate_path`, `validate_source_root` |
| `.documentation_query_builder` | `normalize_documentation_query_limit`, `validate_live_query_source_selection` |
| `.io` | `read_md` |
| `.search_rank` | `MAX_SEARCH_BYTES`, `MAX_SEARCH_PAGES`, `rank_pages` |
| `.source_selection` | `resolve_source_selection` |
| `.source_snapshot` | `build_source_snapshot`, `capture_source_selection_inputs` |
| `__future__` | `annotations` |
| `collections.abc` | `Callable`, `Iterable` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/config.py"]
    n2["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n3["src/llm_wiki_cli/services/io.py"]
    n4["src/llm_wiki_cli/services/search_rank.py"]
    n5["src/llm_wiki_cli/services/search_service.py"]
    n6["src/llm_wiki_cli/services/source_selection.py"]
    n7["src/llm_wiki_cli/services/source_snapshot.py"]
    n8["src/llm_wiki_cli/services/task_context.py"]
    n9["src/llm_wiki_cli/services/wiki_surface.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n0 --> n9
    n1 --> n3
    n2 --> n6
    n2 --> n7
    n2 --> n9
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n6
    n5 --> n7
    n5 --> n9
    n6 --> n1
    n7 --> n1
    n7 --> n6
    n8 --> n1
    n8 --> n2
    n8 --> n3
    n8 --> n5
    n8 --> n7
    click n0 "../modules/api.md"
    click n1 "../modules/config.md"
    click n2 "../modules/documentation_query_builder.md"
    click n3 "../modules/io.md"
    click n4 "../modules/search_rank.md"
    click n5 "../modules/search_service.md"
    click n6 "../modules/source_selection.md"
    click n7 "../modules/source_snapshot.md"
    click n8 "../modules/task_context.md"
    click n9 "../modules/wiki_surface.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [search_rank](../modules/search_rank.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |
| Outbound | [wiki_surface](../modules/wiki_surface.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `normalize_search` | `(query: object, kinds: object, limit: object, mode: object)` | — | Validate before discovering source or wiki inputs. |
| `search_records` | `(records: Iterable[dict[str, Any]], query: str, *, limit: int, mode: str)` | — | Apply the same ranking and legacy substring contracts to captured pages. |
| `page_records` | `(wiki_root: Path, kinds: set[str], *, reader: Callable = read_md)` | — | — |
| `search_wiki` | `(query, *, src_dir = '.', wiki_dir = 'docs/llm_wiki', kinds = None, limit = 20, mode = 'ranked', source_selection = None, allow_external_src = False)` | — | — |