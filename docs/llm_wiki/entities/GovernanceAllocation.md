# GovernanceAllocation

**Location:** `src/llm_wiki_cli/services/knowledge_governance.py:154`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_governance](../modules/knowledge_governance.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One authoritative stable concept allocation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `uid` | `str` | *required* | — |
| `concept_kind` | `str` | *required* | — |
| `natural_key` | `str` | *required* | — |
| `locator` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_payload` | `() -> dict[str, str]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["GovernanceAllocation (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1["_existing_uid (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n2["_put_alias (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n3["_validate_lifecycle_event_fields (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n4["_validate_lifecycle_histories (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n5["_validate_review_event_fields (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n6["move_concept (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n7["parse_governance_ledger (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n8["reconcile_concepts (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_governance.md"
    click n1 "../modules/knowledge_governance.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_governance.md"
    click n5 "../modules/knowledge_governance.md"
    click n6 "../modules/knowledge_governance.md"
    click n7 "../modules/knowledge_governance.md"
    click n8 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_governance](../modules/knowledge_governance.md) | 1 | `concept_kind`, `locator`, `natural_key`, `uid` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_existing_uid` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_put_alias` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_lifecycle_event_fields` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_lifecycle_histories` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_review_event_fields` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `move_concept` | call | [knowledge_governance](../modules/knowledge_governance.md) |
| `parse_governance_ledger` | call | [knowledge_governance](../modules/knowledge_governance.md) |
| `reconcile_concepts` | call | [knowledge_governance](../modules/knowledge_governance.md) |
| `reconcile_concepts` | call | [knowledge_governance](../modules/knowledge_governance.md) |
