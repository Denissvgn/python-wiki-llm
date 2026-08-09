# ConceptIdentityError

**Location:** `src/llm_wiki_cli/services/concept_identity.py:75`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [concept_identity](../modules/concept_identity.md)

## Description

Field-specific validation failure for stable concept identity.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str, *, code: str = 'invalid')` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConceptIdentityError (src/llm_wiki_cli/services/concept_identity.py)"]
    n1["ValueError"]
    n2["IdentityCollisionError (src/llm_wiki_cli/services/concept_identity.py)"]
    n3["_machine_text (src/llm_wiki_cli/services/concept_identity.py)"]
    n4["_safe_decoded_coordinate (src/llm_wiki_cli/services/concept_identity.py)"]
    n5["add_identity_alias (src/llm_wiki_cli/services/concept_identity.py)"]
    n6["aliases_for_move (src/llm_wiki_cli/services/concept_identity.py)"]
    n7["allocate_concept (src/llm_wiki_cli/services/concept_identity.py)"]
    n8["ConceptAllocation.__post_init__ (src/llm_wiki_cli/services/concept_identity.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/concept_identity.md"
    click n2 "../modules/concept_identity.md"
    click n3 "../modules/concept_identity.md"
    click n4 "../modules/concept_identity.md"
    click n5 "../modules/concept_identity.md"
    click n6 "../modules/concept_identity.md"
    click n7 "../modules/concept_identity.md"
    click n8 "../modules/concept_identity.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [concept_identity](../modules/concept_identity.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `IdentityCollisionError` | [concept_identity](../modules/concept_identity.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) |
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) |
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) |
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) |
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) |
| `_safe_decoded_coordinate` | call | [concept_identity](../modules/concept_identity.md) |
| `_safe_decoded_coordinate` | call | [concept_identity](../modules/concept_identity.md) |
| `_safe_decoded_coordinate` | call | [concept_identity](../modules/concept_identity.md) |
| `add_identity_alias` | call | [concept_identity](../modules/concept_identity.md) |
| `aliases_for_move` | call | [concept_identity](../modules/concept_identity.md) |
| `allocate_concept` | call | [concept_identity](../modules/concept_identity.md) |
| `ConceptAllocation.__post_init__` | call | [concept_identity](../modules/concept_identity.md) |
