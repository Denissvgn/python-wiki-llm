# ExtractSourceResult

**Location:** `src/llm_wiki_cli/api_types.py:20`
**Kind:** Class
**Bases:** `_ExtractSourceRequired`
**Module:** [api_types](../modules/api_types.md)

## Description

Top-level ``extract_source`` payload.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `docker` | `dict[str, Any]` | *required* | — |
| `unsupported_sources` | `dict[str, Any]` | *required* | — |
| `entrypoints` | `list[dict[str, Any]]` | *required* | — |
| `data_flows` | `list[dict[str, Any]]` | *required* | — |
| `dependencies` | `dict[str, Any]` | *required* | — |
| `api_contracts` | `dict[str, Any]` | *required* | — |
| `warnings` | `list[str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExtractSourceResult (src/llm_wiki_cli/api_types.py)"]
    n1["_ExtractSourceRequired (src/llm_wiki_cli/api_types.py)"]
    n2["extract_source (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
    click n2 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `api_contracts`, `data_flows`, `dependencies`, `docker`, `entrypoints`, `unsupported_sources`, `warnings` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_ExtractSourceRequired` | [api_types](../modules/api_types.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `extract_source` | type_reference | [api](../modules/api.md) |
