# BootstrapExtractionError

**Location:** `src/llm_wiki_cli/services/bootstrap_service.py:14`
**Kind:** Class
**Bases:** `BootstrapServiceError`
**Module:** [bootstrap_service](../modules/bootstrap_service.md)

## Description

Raised when one or more required extractors fail.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BootstrapExtractionError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n1["BootstrapServiceError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_extract_bootstrap_inventory (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/bootstrap_service.md"
    click n1 "../modules/bootstrap_service.md"
    click n2 "../modules/api.md"
    click n3 "../modules/bootstrap_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_service](../modules/bootstrap_service.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `BootstrapServiceError` | [bootstrap_service](../modules/bootstrap_service.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_extract_bootstrap_inventory` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) | 1 |
