# ResultBounds

**Location:** `src/llm_wiki_cli/api_types.py:17`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

Exact size disclosure for one bounded result collection.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `total` | `int` | *required* | — |
| `returned` | `int` | *required* | — |
| `truncated` | `bool` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ResultBounds (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n2["ByteResultBounds (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/api_types.md"
    click n2 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `returned`, `total`, `truncated` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
| Subclass | `ByteResultBounds` | [api_types](../modules/api_types.md) |
