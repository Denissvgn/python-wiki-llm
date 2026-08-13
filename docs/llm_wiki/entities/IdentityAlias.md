# IdentityAlias

**Location:** `src/llm_wiki_cli/services/concept_identity.py:153`
**Kind:** Class
**Bases:** —
**Module:** [concept_identity](../modules/concept_identity.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One historical locator or natural key owned by a persisted UID.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `alias_type` | `AliasType \| str` | *required* | — |
| `value` | `str` | *required* | — |
| `uid` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["IdentityAlias (src/llm_wiki_cli/services/concept_identity.py)"]
    n1["_deduplicated_aliases (src/llm_wiki_cli/services/concept_identity.py)"]
    n2["_sorted_aliases (src/llm_wiki_cli/services/concept_identity.py)"]
    n3["add_identity_alias (src/llm_wiki_cli/services/concept_identity.py)"]
    n4["aliases_for_move (src/llm_wiki_cli/services/concept_identity.py)"]
    n5["allocate_concept (src/llm_wiki_cli/services/concept_identity.py)"]
    n6["find_identity_collisions (src/llm_wiki_cli/services/concept_identity.py)"]
    n7["move_allocation (src/llm_wiki_cli/services/concept_identity.py)"]
    n8["validate_identity_registry (src/llm_wiki_cli/services/concept_identity.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/concept_identity.md"
    click n1 "../modules/concept_identity.md"
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
| [concept_identity](../modules/concept_identity.md) | 1 | `alias_type`, `uid`, `value` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_deduplicated_aliases` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `_sorted_aliases` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `add_identity_alias` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `add_identity_alias` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `aliases_for_move` | call | [concept_identity](../modules/concept_identity.md) | 2 |
| `aliases_for_move` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `allocate_concept` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `find_identity_collisions` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `move_allocation` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
| `validate_identity_registry` | type_reference | [concept_identity](../modules/concept_identity.md) | — |
