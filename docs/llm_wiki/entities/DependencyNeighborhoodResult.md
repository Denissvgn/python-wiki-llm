# DependencyNeighborhoodResult

**Location:** `src/llm_wiki_cli/api_types.py:194`
**Kind:** Class
**Bases:** `_BoundedQueryResult`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `DependencyNeighborhoodResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str \| None` | *required* | — |
| `inbound` | `list[str]` | *required* | — |
| `outbound` | `list[str]` | *required* | — |
| `metrics` | `dict[str, Any]` | *required* | — |
| `cycle_groups` | `list[dict[str, Any]]` | *required* | — |
| `load_order_index` | `int \| None` | *required* | — |
| `pages` | `list[dict[str, Any]]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DependencyNeighborhoodResult (src/llm_wiki_cli/api_types.py)"]
    n1["_BoundedQueryResult (src/llm_wiki_cli/api_types.py)"]
    n2["dependency_neighborhood (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `cycle_groups`, `inbound`, `load_order_index`, `metrics`, `outbound`, `pages`, `path` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_BoundedQueryResult` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `dependency_neighborhood` | type_reference | [api](../modules/api.md) | — |
