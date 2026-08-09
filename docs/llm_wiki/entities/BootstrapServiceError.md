# BootstrapServiceError

**Location:** `src/llm_wiki_cli/services/bootstrap_service.py:10`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [bootstrap_service](../modules/bootstrap_service.md)

## Description

Base error raised by the library bootstrap boundary.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BootstrapServiceError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n1["RuntimeError"]
    n2["BootstrapContractError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n3["BootstrapExtractionError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n4["src/llm_wiki_cli/api.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/bootstrap_service.md"
    click n2 "../modules/bootstrap_service.md"
    click n3 "../modules/bootstrap_service.md"
    click n4 "../modules/api.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_service](../modules/bootstrap_service.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |
| Subclass | `BootstrapContractError` | [bootstrap_service](../modules/bootstrap_service.md) |
| Subclass | `BootstrapExtractionError` | [bootstrap_service](../modules/bootstrap_service.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `api` | import | [api](../modules/api.md) |
