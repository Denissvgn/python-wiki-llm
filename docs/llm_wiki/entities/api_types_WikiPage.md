# WikiPage

**Location:** `src/llm_wiki_cli/api_types.py:137`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

One registry-backed wiki page.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `str` | *required* | — |
| `id` | `str` | *required* | — |
| `label` | `str` | *required* | — |
| `canonical_path` | `str` | *required* | — |
| `mcp_uri` | `str` | *required* | — |
| `role` | `str` | *required* | — |
| `obsidian_mirror_dir` | `str \| None` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiPage (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["_wiki_page_counts (src/llm_wiki_cli/api.py)"]
    n3["_wiki_page_payload (src/llm_wiki_cli/api.py)"]
    n4["list_wiki_pages (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `canonical_path`, `id`, `kind`, `label`, `mcp_uri`, `obsidian_mirror_dir`, `role` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_wiki_page_counts` | type_reference | [api](../modules/api.md) | — |
| `_wiki_page_payload` | type_reference | [api](../modules/api.md) | — |
| `list_wiki_pages` | type_reference | [api](../modules/api.md) | — |
