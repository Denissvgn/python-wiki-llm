# VerificationReceiptError

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:87`
**Kind:** Class
**Bases:** `VerificationContractError`
**Module:** [verification_contracts](../modules/verification_contracts.md)

## Description

Field-specific failure for a verification receipt.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["VerificationReceiptError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["VerificationContractError (src/llm_wiki_cli/services/verification_contracts.py)"]
    n2["_array (src/llm_wiki_cli/services/verification_contracts.py)"]
    n3["_exact_fields (src/llm_wiki_cli/services/verification_contracts.py)"]
    n4["_nonnegative_int (src/llm_wiki_cli/services/verification_contracts.py)"]
    n5["_object (src/llm_wiki_cli/services/verification_contracts.py)"]
    n6["_parse_check (src/llm_wiki_cli/services/verification_contracts.py)"]
    n7["_parse_coverage (src/llm_wiki_cli/services/verification_contracts.py)"]
    n8["_parse_diagnostic (src/llm_wiki_cli/services/verification_contracts.py)"]
    n9["_read_regular_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n10["_receipt_anchor_mapping (src/llm_wiki_cli/services/verification_contracts.py)"]
    n11["_receipt_hash (src/llm_wiki_cli/services/verification_contracts.py)"]
    n12["_string (src/llm_wiki_cli/services/verification_contracts.py)"]
    n13["deserialize_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
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
    n12 --> n0
    n13 --> n0
    click n0 "../modules/verification_contracts.md"
    click n1 "../modules/verification_contracts.md"
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
    click n12 "../modules/verification_contracts.md"
    click n13 "../modules/verification_contracts.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_array` | call | [verification_contracts](../modules/verification_contracts.md) | 1 |
| `_exact_fields` | call | [verification_contracts](../modules/verification_contracts.md) | 3 |
| `_nonnegative_int` | call | [verification_contracts](../modules/verification_contracts.md) | 1 |
| `_object` | call | [verification_contracts](../modules/verification_contracts.md) | 2 |
| `_parse_check` | call | [verification_contracts](../modules/verification_contracts.md) | 7 |
| `_parse_coverage` | call | [verification_contracts](../modules/verification_contracts.md) | 2 |
| `_parse_diagnostic` | call | [verification_contracts](../modules/verification_contracts.md) | 1 |
| `_read_regular_receipt` | call | [verification_contracts](../modules/verification_contracts.md) | 7 |
| `_receipt_anchor_mapping` | call | [verification_contracts](../modules/verification_contracts.md) | 1 |
| `_receipt_hash` | call | [verification_contracts](../modules/verification_contracts.md) | 1 |
| `_string` | call | [verification_contracts](../modules/verification_contracts.md) | 1 |
| `deserialize_verification_receipt` | call | [verification_contracts](../modules/verification_contracts.md) | 4 |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
