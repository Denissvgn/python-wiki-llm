# ConceptIdentityError

**Location:** `src/llm_wiki_engine/concept_identity.py:76`
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
    n0["ConceptIdentityError (src/llm_wiki_engine/concept_identity.py)"]
    n1["ValueError"]
    n2["IdentityCollisionError (src/llm_wiki_engine/concept_identity.py)"]
    n3["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n4["src/llm_wiki_cli/services/knowledge_projection.py"]
    n5["src/llm_wiki_cli/services/mcp_server.py"]
    n6["src/llm_wiki_cli/services/publication_config.py"]
    n7["_machine_text (src/llm_wiki_engine/concept_identity.py)"]
    n8["_safe_decoded_coordinate (src/llm_wiki_engine/concept_identity.py)"]
    n9["add_identity_alias (src/llm_wiki_engine/concept_identity.py)"]
    n10["aliases_for_move (src/llm_wiki_engine/concept_identity.py)"]
    n11["allocate_concept (src/llm_wiki_engine/concept_identity.py)"]
    n12["ConceptAllocation.__post_init__ (src/llm_wiki_engine/concept_identity.py)"]
    n13["IdentityCollision.__post_init__ (src/llm_wiki_engine/concept_identity.py)"]
    n14["IdentityUpdate.__post_init__ (src/llm_wiki_engine/concept_identity.py)"]
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
    click n3 "../modules/documentation_query_builder.md"
    click n4 "../modules/knowledge_projection.md"
    click n5 "../modules/mcp_server.md"
    click n6 "../modules/publication_config.md"
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
| `documentation_query_builder` | import | [documentation_query_builder](../modules/documentation_query_builder.md) | — |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
| `mcp_server` | import | [mcp_server](../modules/mcp_server.md) | — |
| `publication_config` | import | [publication_config](../modules/publication_config.md) | — |
| `_machine_text` | call | [concept_identity](../modules/concept_identity.md) | 5 |
| `_safe_decoded_coordinate` | call | [concept_identity](../modules/concept_identity.md) | 3 |
| `add_identity_alias` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `aliases_for_move` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `allocate_concept` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `ConceptAllocation.__post_init__` | call | [concept_identity](../modules/concept_identity.md) | 1 |
| `IdentityCollision.__post_init__` | call | [concept_identity](../modules/concept_identity.md) | 4 |
| `IdentityUpdate.__post_init__` | call | [concept_identity](../modules/concept_identity.md) | 3 |

> References: showing 12 of 22 logical references; 10 omitted by the 12-row generated summary limit.
