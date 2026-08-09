# ConceptReference

**Location:** `src/llm_wiki_cli/services/concept_identity.py:93`
**Kind:** Class
**Bases:** —
**Module:** [concept_identity](../modules/concept_identity.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One current, regenerable concept coordinate before UID allocation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `locator` | `str` | *required* | — |
| `concept_kind` | `str` | *required* | — |
| `natural_key` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptReference (src/llm_wiki_cli/services/concept_identity.py)"]
    n1["aliases_for_move (src/llm_wiki_cli/services/concept_identity.py)"]
    n2["allocate_concept (src/llm_wiki_cli/services/concept_identity.py)"]
    n3["ConceptAllocation.reference (src/llm_wiki_cli/services/concept_identity.py)"]
    n4["move_allocation (src/llm_wiki_cli/services/concept_identity.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/concept_identity.md"
    click n1 "../modules/concept_identity.md"
    click n2 "../modules/concept_identity.md"
    click n3 "../modules/concept_identity.md"
    click n4 "../modules/concept_identity.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [concept_identity](../modules/concept_identity.md) | 1 | `concept_kind`, `locator`, `natural_key` |

### References

| Reference | Kind | Source |
|---|---|---|
| `aliases_for_move` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `allocate_concept` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `ConceptAllocation.reference` | call | [concept_identity](../modules/concept_identity.md) |
| `ConceptAllocation.reference` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `move_allocation` | type_reference | [concept_identity](../modules/concept_identity.md) |
