# LlmWikiApiError

**Location:** `src/llm_wiki_cli/api.py:317`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [api](../modules/api.md)

## Description

Base exception raised by the supported Python API.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, *, code: str \| None = None, details: Mapping[str, Any] \| None = None) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LlmWikiApiError (src/llm_wiki_cli/api.py)"]
    n1["RuntimeError"]
    n2["ArtifactIntegrityError (src/llm_wiki_cli/api.py)"]
    n3["InvalidRequestError (src/llm_wiki_cli/api.py)"]
    n4["WorkspaceStateError (src/llm_wiki_cli/api.py)"]
    n5["_api_mcp_error (src/llm_wiki_cli/services/mcp_server.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
    click n5 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api](../modules/api.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |
| Subclass | `ArtifactIntegrityError` | [api](../modules/api.md) |
| Subclass | `InvalidRequestError` | [api](../modules/api.md) |
| Subclass | `WorkspaceStateError` | [api](../modules/api.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_api_mcp_error` | type_reference | [mcp_server](../modules/mcp_server.md) |
