# VerificationContractError

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:75`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [verification_contracts](../modules/verification_contracts.md)

## Description

Base error for verification inputs, checkers, and receipts.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["VerificationContractError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["ValueError"]
    n2["UnknownVerificationCheckerError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n3["VerificationReceiptError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n4["_checker_id (src/llm_wiki_cli/services/verification_contracts.py)"]
    n5["_checker_version (src/llm_wiki_cli/services/verification_contracts.py)"]
    n6["_diagnostic_subject (src/llm_wiki_cli/services/verification_contracts.py)"]
    n7["_machine_code (src/llm_wiki_cli/services/verification_contracts.py)"]
    n8["_normalized_anchor_mapping (src/llm_wiki_cli/services/verification_contracts.py)"]
    n9["_portable_text (src/llm_wiki_cli/services/verification_contracts.py)"]
    n10["_scope_uid (src/llm_wiki_cli/services/verification_contracts.py)"]
    n11["_selected_contracts (src/llm_wiki_cli/services/verification_contracts.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/verification_contracts.md"
    click n2 "../modules/verification_contracts.md"
    click n3 "../modules/verification_contracts.md"
    click n4 "../modules/verification_contracts.md"
    click n5 "../modules/verification_contracts.md"
    click n6 "../modules/verification_contracts.md"
    click n7 "../modules/verification_contracts.md"
    click n8 "../modules/verification_contracts.md"
    click n9 "../modules/verification_contracts.md"
    click n10 "../modules/verification_contracts.md"
    click n11 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [verification_contracts](../modules/verification_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `UnknownVerificationCheckerError` | [verification_contracts](../modules/verification_contracts.md) |
| Subclass | `VerificationReceiptError` | [verification_contracts](../modules/verification_contracts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_checker_id` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_checker_version` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_diagnostic_subject` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_machine_code` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_normalized_anchor_mapping` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_normalized_anchor_mapping` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_normalized_anchor_mapping` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_portable_text` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_scope_uid` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_selected_contracts` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_selected_contracts` | call | [verification_contracts](../modules/verification_contracts.md) |
| `_selected_contracts` | call | [verification_contracts](../modules/verification_contracts.md) |
