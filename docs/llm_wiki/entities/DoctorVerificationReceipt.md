# DoctorVerificationReceipt

**Location:** `src/llm_wiki_cli/api_types.py:231`
**Kind:** Class
**Bases:** `TypedDict`
**Module:** [api_types](../modules/api_types.md)

## Description

_Auto-generated from `DoctorVerificationReceipt` in `src/llm_wiki_cli/api_types.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state` | `str` | *required* | — |
| `reason` | `str` | *required* | — |
| `recorded_result` | `str \| None` | *required* | — |
| `passed` | `bool \| None` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DoctorVerificationReceipt (src/llm_wiki_cli/api_types.py)"]
    n1["TypedDict"]
    n0 --> n1
    click n0 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `passed`, `reason`, `recorded_result`, `state` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `TypedDict` | — |
