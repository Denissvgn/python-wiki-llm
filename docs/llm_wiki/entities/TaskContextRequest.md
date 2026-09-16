# TaskContextRequest

**Location:** `src/llm_wiki_cli/api_types.py:43`
**Kind:** Class
**Bases:** `_TaskOptions`
**Module:** [api_types](../modules/api_types.md)

## Description

The versioned task request, combining bounded intent, exact anchors, observable requirements, change selection and permitted setting overrides. Free-form task text is retrieval input and cannot grant execution or filesystem authority.

## Attributes

| Name | Type | Presence | Description |
|------|------|----------|-------------|
| `schema_version` | `Literal['llm-wiki-task-request/v1']` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["TaskContextRequest (src/llm_wiki_cli/api_types.py)"]
    n1["_TaskOptions (src/llm_wiki_cli/api_types.py)"]
    n0 --> n1
    click n0 "../modules/api_types.md"
    click n1 "../modules/api_types.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_types](../modules/api_types.md) | 0 | `schema_version` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `_TaskOptions` | [api_types](../modules/api_types.md) |
