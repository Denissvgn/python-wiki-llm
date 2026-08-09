# BootstrapRequestError

**Location:** `src/llm_wiki_cli/services/bootstrap_service.py:22`
**Kind:** Class
**Bases:** `BootstrapContractError`
**Module:** [bootstrap_service](../modules/bootstrap_service.md)

## Description

Raised when caller-supplied bootstrap options violate the contract.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BootstrapRequestError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n1["BootstrapContractError (src/llm_wiki_cli/services/bootstrap_service.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_bootstrap_run_options_from_request (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["_execute_bootstrap_options (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["_execute_documentation_workspace_refresh (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n6["_preflight_public_bootstrap (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/bootstrap_service.md"
    click n1 "../modules/bootstrap_service.md"
    click n2 "../modules/api.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/bootstrap_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_service](../modules/bootstrap_service.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `BootstrapContractError` | [bootstrap_service](../modules/bootstrap_service.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `api` | import | [api](../modules/api.md) |
| `_bootstrap_run_options_from_request` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_bootstrap_run_options_from_request` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_execute_bootstrap_options` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_execute_documentation_workspace_refresh` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_execute_documentation_workspace_refresh` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `_preflight_public_bootstrap` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
