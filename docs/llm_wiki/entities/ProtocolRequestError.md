# ProtocolRequestError

**Location:** `src/llm_wiki_cli/services/context_service.py:176`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_service](../modules/context_service.md)

## Description

Validation error for Wiki-as-Context protocol requests.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, field: str \| None = None, *, protocol: str = PROTOCOL_VERSION)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtocolRequestError (src/llm_wiki_cli/services/context_service.py)"]
    n1["ValueError"]
    n2["_build_context (src/llm_wiki_cli/services/context_service.py)"]
    n3["_build_context_impl (src/llm_wiki_cli/services/context_service.py)"]
    n4["_capture_protocol_enrichment_session (src/llm_wiki_cli/services/context_service.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/context_service.md"
    click n2 "../modules/context_service.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/context_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_service](../modules/context_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_build_context` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_build_context_impl` | call | [context_service](../modules/context_service.md) |
| `_capture_protocol_enrichment_session` | call | [context_service](../modules/context_service.md) |
| `_capture_protocol_enrichment_session` | call | [context_service](../modules/context_service.md) |
| `_capture_protocol_enrichment_session` | call | [context_service](../modules/context_service.md) |
