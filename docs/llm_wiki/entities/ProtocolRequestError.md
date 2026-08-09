# ProtocolRequestError

**Location:** `src/llm_wiki_cli/services/context_service.py:165`
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
| `__init__` | `(message: str, field: str \| None = None)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProtocolRequestError (src/llm_wiki_cli/services/context_service.py)"]
    n1["ValueError"]
    n2["_build_context (src/llm_wiki_cli/services/context_service.py)"]
    n3["_build_protocol_enrichment (src/llm_wiki_cli/services/context_service.py)"]
    n4["_emit_protocol_error (src/llm_wiki_cli/services/context_service.py)"]
    n5["_normalise_protocol_filters (src/llm_wiki_cli/services/context_service.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/context_service.md"
    click n2 "../modules/context_service.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/context_service.md"
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
| `_build_context` | call | [context_service](../modules/context_service.md) |
| `_build_context` | call | [context_service](../modules/context_service.md) |
| `_build_context` | call | [context_service](../modules/context_service.md) |
| `_build_context` | call | [context_service](../modules/context_service.md) |
| `_build_protocol_enrichment` | call | [context_service](../modules/context_service.md) |
| `_build_protocol_enrichment` | call | [context_service](../modules/context_service.md) |
| `_build_protocol_enrichment` | call | [context_service](../modules/context_service.md) |
| `_emit_protocol_error` | type_reference | [context_service](../modules/context_service.md) |
| `_normalise_protocol_filters` | call | [context_service](../modules/context_service.md) |
| `_normalise_protocol_filters` | call | [context_service](../modules/context_service.md) |
| `_normalise_protocol_filters` | call | [context_service](../modules/context_service.md) |
