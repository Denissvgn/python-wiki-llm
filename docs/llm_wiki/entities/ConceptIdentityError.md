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
    n9["IdentityCollision.__post_init__ (src/llm_wiki_cli/services/concept_identity.py)"]
    n10["IdentityUpdate.__post_init__ (src/llm_wiki_cli/services/concept_identity.py)"]
    n11["move_allocation (src/llm_wiki_cli/services/concept_identity.py)"]
    n12["validate_alias_type (src/llm_wiki_cli/services/concept_identity.py)"]
    n13["validate_bundle_id (src/llm_wiki_cli/services/concept_identity.py)"]
    n14["validate_concept_kind (src/llm_wiki_cli/services/concept_identity.py)"]
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
    n14 --> n0
    click n0 "../modules/concept_identity.md"
    click n2 "../modules/concept_identity.md"
    click n3 "../modules/concept_identity.md"
    click n4 "../modules/concept_identity.md"
    click n5 "../modules/concept_identity.md"
    click n6 "../modules/concept_identity.md"
    click n7 "../modules/concept_identity.md"
    click n8 "../modules/concept_identity.md"
    click n9 "../modules/concept_identity.md"
    click n10 "../modules/concept_identity.md"
    click n11 "../modules/concept_identity.md"
    click n12 "../modules/concept_identity.md"
    click n13 "../modules/concept_identity.md"
    click n14 "../modules/concept_identity.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) | 5 |
| `_safe_decoded_coordinate` | call | [concept_identity](../modules/concept_identity.md) | 3 |
| `add_identity_alias` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `aliases_for_move` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `allocate_concept` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `ConceptAllocation.__post_init__` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `IdentityCollision.__post_init__` | call | [concept_identity](../modules/concept_identity.md) | 4 |
| `IdentityUpdate.__post_init__` | call | [concept_identity](../modules/concept_identity.md) | 3 |
| `move_allocation` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `validate_alias_type` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `validate_bundle_id` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `validate_concept_kind` | call | [concept_identity](../modules/concept_identity.md) | 1 |

> References: showing 12 of 19 logical references; 7 omitted by the 12-row generated summary limit.
