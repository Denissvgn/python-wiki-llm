# HealthCoverage

**Location:** `src/llm_wiki_cli/api_types.py:548`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `HealthCoverage` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `total` | `int \| None` | *required* | — |
| `modeled` | `int \| None` | *required* | — |
| `unmodeled` | `int \| None` | *required* | — |
| `evaluated` | `int \| None` | *required* | — |
| `comparison_attempted` | `int \| None` | *required* | — |
| `comparable` | `int \| None` | *required* | — |
| `outcomes` | `dict[str, int] \| None` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HealthCoverage (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n0 --> n1
    click n0 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `comparable`, `comparison_attempted`, `evaluated`, `modeled`, `outcomes`, `total`, `unmodeled` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
