# ExtractorFailureError

**Location:** `src/llm_wiki_cli/services/extraction_service.py:212`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [extraction_service](../modules/extraction_service.md)

## Description

Raised when one or more extractors fail during payload construction.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(result: InventoryResult)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExtractorFailureError (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["RuntimeError"]
    n2["build_extract_payload (src/llm_wiki_cli/services/extraction_service.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/extraction_service.md"
    click n2 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_extract_payload` | call | [extraction_service](../modules/extraction_service.md) | 1 |
