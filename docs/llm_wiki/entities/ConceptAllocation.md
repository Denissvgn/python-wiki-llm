# ConceptAllocation

**Location:** `src/llm_wiki_cli/services/concept_identity.py:115`
**Kind:** Class
**Bases:** —
**Module:** [concept_identity](../modules/concept_identity.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A persisted UID bound to the concept's current coordinates.

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
| `__post_init__` | `() -> None` | — | — |
| `reference` | `() -> ConceptReference` | `@property` | Return the allocation's current regenerable reference. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptAllocation (src/llm_wiki_cli/services/concept_identity.py)"]
    n1["add_identity_alias (src/llm_wiki_cli/services/concept_identity.py)"]
    n2["aliases_for_move (src/llm_wiki_cli/services/concept_identity.py)"]
    n3["allocate_concept (src/llm_wiki_cli/services/concept_identity.py)"]
    n4["find_identity_collisions (src/llm_wiki_cli/services/concept_identity.py)"]
    n5["move_allocation (src/llm_wiki_cli/services/concept_identity.py)"]
    n6["validate_identity_registry (src/llm_wiki_cli/services/concept_identity.py)"]
    n7["validate_governance_ledger (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/concept_identity.md"
    click n1 "../modules/concept_identity.md"
    click n2 "../modules/concept_identity.md"
    click n3 "../modules/concept_identity.md"
    click n4 "../modules/concept_identity.md"
    click n5 "../modules/concept_identity.md"
    click n6 "../modules/concept_identity.md"
    click n7 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [concept_identity](../modules/concept_identity.md) | 2 | `concept_kind`, `locator`, `natural_key`, `uid` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `add_identity_alias` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `aliases_for_move` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `allocate_concept` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `allocate_concept` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `find_identity_collisions` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `move_allocation` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `move_allocation` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `validate_identity_registry` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `validate_governance_ledger` | call | [knowledge_governance](../modules/knowledge_governance.md) | 1 |
