# SupervisorReconciliation

**Location:** `src/llm_wiki_cli/services/documentation_review.py:310`
**Kind:** Class
**Bases:** —
**Module:** [documentation_review](../modules/documentation_review.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Independent supervisor disposition for a clean review ledger.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `packet` | `DocumentationReviewPacket` | *required* | — |
| `approved` | `bool` | *required* | — |
| `rationale` | `str` | *required* | — |
| `reviewed_finding_ids` | `tuple[str, ...]` | *required* | — |
| `evidence` | `tuple[str, ...]` | *required* | — |
| `reconciled_at` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'SupervisorReconciliation'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SupervisorReconciliation (src/llm_wiki_cli/services/documentation_review.py)"]
    n1["reconcile_review_ledger (src/llm_wiki_cli/services/documentation_review.py)"]
    n2["SupervisorReconciliation.from_dict (src/llm_wiki_cli/services/documentation_review.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/documentation_review.md"
    click n1 "../modules/documentation_review.md"
    click n2 "../modules/documentation_review.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_review](../modules/documentation_review.md) | 2 | `approved`, `evidence`, `packet`, `rationale`, `reconciled_at`, `reviewed_finding_ids` |

### References

| Reference | Kind | Source |
|---|---|---|
| `reconcile_review_ledger` | call | [documentation_review](../modules/documentation_review.md) |
| `SupervisorReconciliation.from_dict` | type_reference | [documentation_review](../modules/documentation_review.md) |
