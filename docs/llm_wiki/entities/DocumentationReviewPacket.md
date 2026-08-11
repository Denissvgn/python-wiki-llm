# DocumentationReviewPacket

**Location:** `src/llm_wiki_cli/services/documentation_review.py:256`
**Kind:** Class
**Bases:** —
**Module:** [documentation_review](../modules/documentation_review.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Auditable reference to one role-specific packet and result.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `packet_id` | `str` | *required* | — |
| `role` | `str` | *required* | — |
| `actor_id` | `str` | *required* | — |
| `iteration` | `int` | *required* | — |
| `packet_hash` | `str` | *required* | — |
| `result_hash` | `str` | *required* | — |
| `recorded_at` | `str` | *required* | — |
| `evidence` | `tuple[str, ...]` | `()` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationReviewPacket'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationReviewPacket (src/llm_wiki_cli/services/documentation_review.py)"]
    n1["_validate_loop_packets (src/llm_wiki_cli/services/documentation_review.py)"]
    n2["_validate_packet_evidence (src/llm_wiki_cli/services/documentation_review.py)"]
    n3["apply_review_loop (src/llm_wiki_cli/services/documentation_review.py)"]
    n4["DocumentationReviewPacket.from_dict (src/llm_wiki_cli/services/documentation_review.py)"]
    n5["reconcile_review_ledger (src/llm_wiki_cli/services/documentation_review.py)"]
    n6["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n7["_approve_review_ledger (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n8["_record_review_ledger_iteration (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n9["_record_site_review_findings (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/documentation_review.md"
    click n1 "../modules/documentation_review.md"
    click n2 "../modules/documentation_review.md"
    click n3 "../modules/documentation_review.md"
    click n4 "../modules/documentation_review.md"
    click n5 "../modules/documentation_review.md"
    click n6 "../modules/documentation_run_dependencies.md"
    click n7 "../modules/record.md"
    click n8 "../modules/record.md"
    click n9 "../modules/record.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_review](../modules/documentation_review.md) | 3 | `actor_id`, `evidence`, `iteration`, `packet_hash`, `packet_id`, `recorded_at`, `result_hash`, `role` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_validate_loop_packets` | type_reference | [documentation_review](../modules/documentation_review.md) | — |
| `_validate_packet_evidence` | type_reference | [documentation_review](../modules/documentation_review.md) | — |
| `apply_review_loop` | type_reference | [documentation_review](../modules/documentation_review.md) | — |
| `DocumentationReviewPacket.from_dict` | type_reference | [documentation_review](../modules/documentation_review.md) | — |
| `reconcile_review_ledger` | type_reference | [documentation_review](../modules/documentation_review.md) | — |
| `dependencies` | import | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) | — |
| `_approve_review_ledger` | call | [record](../modules/record.md) | 1 |
| `_record_review_ledger_iteration` | call | [record](../modules/record.md) | 2 |
| `_record_site_review_findings` | call | [record](../modules/record.md) | 2 |
