# DiscoveryError

**Location:** `src/llm_wiki_cli/services/search_discovery.py:33`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [search_discovery](../modules/search_discovery.md)

## Description

Safe fixed diagnostics without reflecting captured content.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(code: str, field: str, *, required_bytes: int \| None = None)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DiscoveryError (src/llm_wiki_cli/services/search_discovery.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/services/mcp_server.py"]
    n4["_invalid (src/llm_wiki_cli/services/search_discovery.py)"]
    n5["enrich_search (src/llm_wiki_cli/services/search_discovery.py)"]
    n6["search_prevalidated_roots (src/llm_wiki_cli/services/search_service.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/search_discovery.md"
    click n2 "../modules/api.md"
    click n3 "../modules/mcp_server.md"
    click n4 "../modules/search_discovery.md"
    click n5 "../modules/search_discovery.md"
    click n6 "../modules/search_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [search_discovery](../modules/search_discovery.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `mcp_server` | import | [mcp_server](../modules/mcp_server.md) | — |
| `_invalid` | call | [search_discovery](../modules/search_discovery.md) | 1 |
| `enrich_search` | call | [search_discovery](../modules/search_discovery.md) | 1 |
| `search_prevalidated_roots` | call | [search_service](../modules/search_service.md) | 1 |
