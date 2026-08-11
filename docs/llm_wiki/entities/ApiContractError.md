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
    n5["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n6["src/llm_wiki_cli/services/documentation_native.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/api_contracts.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/api_contracts.md"
    click n4 "../modules/api_contracts.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/documentation_native.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_manifest_openapi_path` | call | [sync_cmd](../modules/sync_cmd.md) | 2 |
| `_resolve_openapi_path` | call | [api_contracts](../modules/api_contracts.md) | 8 |
| `load_openapi_document` | call | [api_contracts](../modules/api_contracts.md) | 7 |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
