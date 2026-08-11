# KnowledgeStatus

**Location:** `src/llm_wiki_cli/api_types.py:31`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

Compact availability and freshness status shared by query adapters.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `availability` | `str` | *required* | — |
| `reason` | `str` | *required* | — |
| `freshness` | `str` | *required* | — |
| `freshness_evaluated` | `bool` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeStatus (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n0 --> n1
    click n0 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `availability`, `freshness`, `freshness_evaluated`, `reason` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
