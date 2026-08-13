# _BoundedQueryResult

**Location:** `src/llm_wiki_cli/api_types.py:165`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

Fields shared by bounded documentation graph queries.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `query` | `str` | *required* | — |
| `found` | `bool` | *required* | — |
| `ambiguous` | `bool` | *required* | — |
| `matches` | `list[dict[str, Any]]` | *required* | — |
| `truncated` | `bool` | *required* | — |
| `bounds` | `dict[str, Any]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_BoundedQueryResult (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["CalleesResult (src/llm_wiki_cli/api_types.py)"]
    n3["CallersResult (src/llm_wiki_cli/api_types.py)"]
    n4["ConceptResult (src/llm_wiki_cli/api_types.py)"]
    n5["DataFlowForEntrypointResult (src/llm_wiki_cli/api_types.py)"]
    n6["DependencyNeighborhoodResult (src/llm_wiki_cli/api_types.py)"]
    n7["FlowForEntrypointResult (src/llm_wiki_cli/api_types.py)"]
    n8["PagesForSymbolResult (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
    click n3 "../modules/api_types.md"
    click n4 "../modules/api_types.md"
    click n5 "../modules/api_types.md"
    click n6 "../modules/api_types.md"
    click n7 "../modules/api_types.md"
    click n8 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `ambiguous`, `bounds`, `found`, `matches`, `query`, `truncated` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
| Subclass | `CalleesResult` | [api_types](../modules/api_types.md) |
| Subclass | `CallersResult` | [api_types](../modules/api_types.md) |
| Subclass | `ConceptResult` | [api_types](../modules/api_types.md) |
| Subclass | `DataFlowForEntrypointResult` | [api_types](../modules/api_types.md) |
| Subclass | `DependencyNeighborhoodResult` | [api_types](../modules/api_types.md) |
| Subclass | `FlowForEntrypointResult` | [api_types](../modules/api_types.md) |
| Subclass | `PagesForSymbolResult` | [api_types](../modules/api_types.md) |
