# UnknownVerificationCheckerError

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:79`
**Kind:** Class
**Bases:** `VerificationContractError`
**Module:** [verification_contracts](../modules/verification_contracts.md)

## Description

Raised before execution when a requested checker is not registered.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(checker_id: object)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["UnknownVerificationCheckerError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["VerificationContractError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n2["_selected_contracts (src/llm_wiki_cli/services/verification_contracts.py)"]
    n3["checker_contract (src/llm_wiki_cli/services/verification_contracts.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/verification_contracts.md"
    click n1 "../modules/verification_contracts.md"
    click n2 "../modules/verification_contracts.md"
    click n3 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [verification_contracts](../modules/verification_contracts.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `VerificationContractError` | [verification_contracts](../modules/verification_contracts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_selected_contracts` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_selected_contracts` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_selected_contracts` | call | [verification_contracts](../modules/verification_contracts.md) |
| `checker_contract` | call | [verification_contracts](../modules/verification_contracts.md) |
