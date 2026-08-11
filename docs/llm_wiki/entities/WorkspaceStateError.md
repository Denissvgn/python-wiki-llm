# WorkspaceStateError

**Location:** `src/llm_wiki_cli/api.py:336`
**Kind:** Class
**Bases:** `LlmWikiApiError`
**Module:** [api](../modules/api.md)

## Description

Raised when workspace state or an operational dependency is unusable.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WorkspaceStateError (src/llm_wiki_cli/api.py)"]
    n1["LlmWikiApiError (src/llm_wiki_cli/api.py)"]
    n2["_raise_api_error (src/llm_wiki_cli/api.py)"]
    n3["_raise_required_knowledge_api_error (src/llm_wiki_cli/api.py)"]
    n4["bootstrap_wiki (src/llm_wiki_cli/api.py)"]
    n5["build_context (src/llm_wiki_cli/api.py)"]
    n6["build_documentation_query_service (src/llm_wiki_cli/api.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/api.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
    click n5 "../modules/api.md"
    click n6 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api](../modules/api.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `LlmWikiApiError` | [api](../modules/api.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_raise_api_error` | call | [api](../modules/api.md) |
| `_raise_api_error` | call | [api](../modules/api.md) |
| `_raise_api_error` | call | [api](../modules/api.md) |
| `_raise_api_error` | call | [api](../modules/api.md) |
| `_raise_api_error` | call | [api](../modules/api.md) |
| `_raise_required_knowledge_api_error` | call | [api](../modules/api.md) |
| `bootstrap_wiki` | call | [api](../modules/api.md) |
| `bootstrap_wiki` | call | [api](../modules/api.md) |
| `build_context` | call | [api](../modules/api.md) |
| `build_context` | call | [api](../modules/api.md) |
| `build_context` | call | [api](../modules/api.md) |
| `build_documentation_query_service` | call | [api](../modules/api.md) |
