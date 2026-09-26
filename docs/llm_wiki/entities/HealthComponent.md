# HealthComponent

**Location:** `src/llm_wiki_cli/api_types.py:526`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `HealthComponent` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `id` | `str` | *required* | — |
| `version` | `str` | *required* | — |
| `configuration_hash` | `str \| None` | *required* | — |
| `limitations` | `list[str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HealthComponent (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n0 --> n1
    click n0 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `configuration_hash`, `id`, `limitations`, `version` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
