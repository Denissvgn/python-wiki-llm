# ApiContractError

**Location:** `src/llm_wiki_cli/services/api_contracts.py:72`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [api_contracts](../modules/api_contracts.md)

## Description

Raised when an API-contract input cannot be consumed safely.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ApiContractError (src/llm_wiki_cli/services/api_contracts.py)"]
    n1["ValueError"]
    n2["_manifest_openapi_path (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_resolve_openapi_path (src/llm_wiki_cli/services/api_contracts.py)"]
    n4["load_openapi_document (src/llm_wiki_cli/services/api_contracts.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/api_contracts.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/api_contracts.md"
    click n4 "../modules/api_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [api_contracts](../modules/api_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_manifest_openapi_path` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_manifest_openapi_path` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) |
| `load_openapi_document` | call | [api_contracts](../modules/api_contracts.md) |
| `load_openapi_document` | call | [api_contracts](../modules/api_contracts.md) |
