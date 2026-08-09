# VerificationReceipt

**Location:** `src/llm_wiki_cli/services/verification_contracts.py:453`
**Kind:** Class
**Bases:** —
**Module:** [verification_contracts](../modules/verification_contracts.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Deterministic recorded evidence from one explicit verification run.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `knowledge_hash` | `str` | *required* | — |
| `scope_uid` | `str` | *required* | — |
| `scope_hash` | `str` | *required* | — |
| `evidence` | `Mapping[str, str]` | *required* | — |
| `evidence_hash` | `str` | *required* | — |
| `evaluated_snapshot` | `Mapping[str, str]` | *required* | — |
| `snapshot_hash` | `str` | *required* | — |
| `result` | `VerificationResult` | *required* | — |
| `checks` | `tuple[VerificationCheckResult, ...]` | *required* | — |
| `schema_version` | `str` | `VERIFICATION_RECEIPT_SCHEMA_VERSION` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, object]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["VerificationReceipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1["machine_verification_summary (src/llm_wiki_cli/services/knowledge_verification.py)"]
    n2["_receipt_to_payload (src/llm_wiki_cli/services/verification_contracts.py)"]
    n3["build_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n4["deserialize_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n5["evaluate_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n6["load_and_evaluate_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n7["load_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n8["serialize_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n9["validate_verification_receipt (src/llm_wiki_cli/services/verification_contracts.py)"]
    n10["verification_receipt_to_payload (src/llm_wiki_cli/services/verification_contracts.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    click n0 "../modules/verification_contracts.md"
    click n1 "../modules/knowledge_verification.md"
    click n2 "../modules/verification_contracts.md"
    click n3 "../modules/verification_contracts.md"
    click n4 "../modules/verification_contracts.md"
    click n5 "../modules/verification_contracts.md"
    click n6 "../modules/verification_contracts.md"
    click n7 "../modules/verification_contracts.md"
    click n8 "../modules/verification_contracts.md"
    click n9 "../modules/verification_contracts.md"
    click n10 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [verification_contracts](../modules/verification_contracts.md) | 2 | `checks`, `evaluated_snapshot`, `evidence`, `evidence_hash`, `knowledge_hash`, `result`, `schema_version`, `scope_hash`, `scope_uid`, `snapshot_hash` |

### References

| Reference | Kind | Source |
|---|---|---|
| `machine_verification_summary` | type_reference | [knowledge_verification](../modules/knowledge_verification.md) |
| `_receipt_to_payload` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `build_verification_receipt` | call | [verification_contracts](../modules/verification_contracts.md) |
| `build_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `deserialize_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `evaluate_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `load_and_evaluate_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `load_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `serialize_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `validate_verification_receipt` | call | [verification_contracts](../modules/verification_contracts.md) |
| `validate_verification_receipt` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
| `verification_receipt_to_payload` | type_reference | [verification_contracts](../modules/verification_contracts.md) |
