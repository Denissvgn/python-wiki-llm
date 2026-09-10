# DocumentationQueryResult

**Location:** `src/llm_wiki_cli/api_types.py:269`
**Kind:** Class
**Bases:** `_DocumentationQueryRequired`
**Module:** [api_types](../modules/api_types.md)

## Description

Common envelope returned by the shared bounded query dispatcher.

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `knowledge` | `KnowledgeStatus \| dict[str, Any]` | *optional* | — |
| `concept` | `dict[str, Any] \| None` | *optional* | — |
| `total` | `int` | *optional* | — |
| `returned` | `int` | *optional* | — |
| `direction` | `str` | *optional* | — |
| `kinds` | `list[str]` | *optional* | — |
| `relationships` | `list[dict[str, Any]]` | *optional* | — |
| `related_concepts` | `list[dict[str, Any]]` | *optional* | — |
| `unresolved_targets` | `list[dict[str, Any]]` | *optional* | — |
| `external_targets` | `list[dict[str, Any]]` | *optional* | — |
| `origins` | `list[str]` | *optional* | — |
| `resolutions` | `list[str]` | *optional* | — |
| `include_evidence` | `bool` | *optional* | — |
| `typed_graph` | `dict[str, Any]` | *optional* | — |
| `edges` | `list[dict[str, Any]]` | *optional* | — |
| `symbol` | `dict[str, Any] \| None` | *optional* | — |
| `pages` | `list[dict[str, Any]]` | *optional* | — |
| `callers` | `list[dict[str, Any]]` | *optional* | — |
| `callees` | `list[dict[str, Any]]` | *optional* | — |
| `flow` | `dict[str, Any] \| None` | *optional* | — |
| `data_flow` | `dict[str, Any] \| None` | *optional* | — |
| `path` | `str \| None` | *optional* | — |
| `inbound` | `list[str]` | *optional* | — |
| `outbound` | `list[str]` | *optional* | — |
| `metrics` | `dict[str, Any]` | *optional* | — |
| `cycle_groups` | `list[dict[str, Any]]` | *optional* | — |
| `load_order_index` | `int \| None` | *optional* | — |
| `impacted_paths` | `list[str]` | *optional* | — |
| `concepts` | `list[dict[str, Any]]` | *optional* | — |
| `limitations` | `list[str]` | *optional* | — |
| `raw_evidence` | `list[dict[str, Any]]` | *optional* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationQueryResult (src/llm_wiki_cli/api_types.py)"]
    n1["_DocumentationQueryRequired (src/llm_wiki_cli/api_types.py)"]
    n2["_impact_query (src/llm_wiki_cli/api.py)"]
    n3["_with_query_envelope (src/llm_wiki_cli/api.py)"]
    n4["query_documentation (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `callees`, `callers`, `concept`, `concepts`, `cycle_groups`, `data_flow`, `direction`, `edges`, `external_targets`, `flow`, `impacted_paths`, `inbound` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_DocumentationQueryRequired` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_impact_query` | type_reference | [api](../modules/api.md) | — |
| `_with_query_envelope` | type_reference | [api](../modules/api.md) | — |
| `query_documentation` | type_reference | [api](../modules/api.md) | — |
