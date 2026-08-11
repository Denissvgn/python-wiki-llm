# IdentityUpdate

**Location:** `src/llm_wiki_cli/services/concept_identity.py:232`
**Kind:** Class
**Bases:** —
**Module:** [concept_identity](../modules/concept_identity.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A replacement allocation and the complete canonical alias collection.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `allocation` | `ConceptAllocation` | *required* | — |
| `aliases` | `tuple[IdentityAlias, ...]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["IdentityUpdate (src/llm_wiki_cli/services/concept_identity.py)"]
    n1["add_identity_alias (src/llm_wiki_cli/services/concept_identity.py)"]
    n2["move_allocation (src/llm_wiki_cli/services/concept_identity.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/concept_identity.md"
    click n1 "../modules/concept_identity.md"
    click n2 "../modules/concept_identity.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [concept_identity](../modules/concept_identity.md) | 1 | `aliases`, `allocation` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `add_identity_alias` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `add_identity_alias` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `move_allocation` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `move_allocation` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
