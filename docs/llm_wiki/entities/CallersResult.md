# CallersResult

**Location:** `src/llm_wiki_cli/api_types.py:379`
**Kind:** Class
**Bases:** `_BoundedQueryResult`, `_StaticCallQueryOptions`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `CallersResult` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `callable` | `dict[str, Any] \| None` | *required* | — |
| `callers` | `list[dict[str, Any]]` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["CallersResult (src/llm_wiki_cli/api_types.py)"]
    n1["_BoundedQueryResult (src/llm_wiki_cli/api_types.py)"]
    n2["_StaticCallQueryOptions (src/llm_wiki_cli/api_types.py)"]
    n3["callers (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
    click n3 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `callable`, `callers` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_BoundedQueryResult` | [api_types](../modules/api_types.md) |
| Base | `_StaticCallQueryOptions` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `callers` | type_reference | [api](../modules/api.md) | — |
