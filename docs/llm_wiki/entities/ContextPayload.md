# ContextPayload

**Location:** `src/llm_wiki_cli/api_types.py:118`
**Kind:** Class
**Bases:** `_ContextRequired`
**Module:** [api_types](../modules/api_types.md)

## Description

Top-level JSON context payload.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `graphs` | `dict[str, Any]` | *required* | — |
| `knowledge` | `ContextKnowledgeResult \| dict[str, Any]` | *required* | — |
| `typed_graph` | `dict[str, Any]` | *required* | — |
| `surface` | `dict[str, Any]` | *required* | — |
| `ranking_policy` | `RankingPolicy \| dict[str, Any]` | *required* | — |
| `warnings` | `list[str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPayload (src/llm_wiki_cli/api_types.py)"]
    n1["_ContextRequired (src/llm_wiki_cli/api_types.py)"]
    n2["build_context (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `graphs`, `knowledge`, `ranking_policy`, `surface`, `typed_graph`, `warnings` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_ContextRequired` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_context` | type_reference | [api](../modules/api.md) | — |
