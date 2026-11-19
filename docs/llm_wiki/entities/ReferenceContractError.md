# ReferenceContractError

**Location:** `src/llm_wiki_cli/services/reference_providers.py:49`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [reference_providers](../modules/reference_providers.md)

## Description

A stored contract could not have come from its provider.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReferenceContractError (src/llm_wiki_cli/services/reference_providers.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/publication_contracts.py"]
    n3["CliContractProvider.validate_contract (src/llm_wiki_cli/services/reference_providers.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/reference_providers.md"
    click n2 "../modules/publication_contracts.md"
    click n3 "../modules/reference_providers.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [reference_providers](../modules/reference_providers.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `publication_contracts` | import | [publication_contracts](../modules/publication_contracts.md) | — |
| `CliContractProvider.validate_contract` | call | [reference_providers](../modules/reference_providers.md) | 1 |
