# VerificationResult

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:96`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [verification_contracts](../modules/verification_contracts.md)

## Description

A recorded checker result at one evaluated snapshot.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `PASSED` | `'passed'` | — |
| `FAILED` | `'failed'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["VerificationResult (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n4["src/llm_wiki_cli/services/knowledge_verification.py"]
    n5["src/llm_wiki_cli/services/lint_service.py"]
    n6["_parse_check (src/llm_wiki_cli/services/verification_contracts.py)"]
    n7["validate_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n8["VerificationCheckResult.__post_init__ (src/llm_wiki_cli/services/verification_contracts.py)"]
    n9["VerificationReceipt.__post_init__ (src/llm_wiki_cli/services/verification_contracts.py)"]
    n10["VerificationReceiptEvaluation.recorded_result (src/llm_wiki_cli/services/verification_contracts.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    click n0 "../modules/verification_contracts.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/knowledge_verification.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/verification_contracts.md"
    click n7 "../modules/verification_contracts.md"
    click n8 "../modules/verification_contracts.md"
    click n9 "../modules/verification_contracts.md"
    click n10 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [verification_contracts](../modules/verification_contracts.md) | 0 | `FAILED`, `PASSED` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `knowledge_verification` | import | [knowledge_verification](../modules/knowledge_verification.md) |
| `lint_service` | import | [lint_service](../modules/lint_service.md) |
| `_parse_check` | call | [verification_contracts](../modules/verification_contracts.md) |
| `validate_verification_receipt` | call | [verification_contracts](../modules/verification_contracts.md) |
| `VerificationCheckResult.__post_init__` | call | [verification_contracts](../modules/verification_contracts.md) |
| `VerificationReceipt.__post_init__` | call | [verification_contracts](../modules/verification_contracts.md) |
| `VerificationReceiptEvaluation.recorded_result` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
