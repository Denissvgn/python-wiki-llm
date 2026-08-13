# KnowledgeModelError

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:77`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

Raised when a knowledge payload violates the v1 contract.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str, *, code: str \| None = None)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeModelError (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_envelope.py"]
    n3["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n4["_require_structure_state (src/llm_wiki_cli/services/knowledge_index.py)"]
    n5["_validate_builder_derived (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_validate_builder_link (src/llm_wiki_cli/services/knowledge_index.py)"]
    n7["_validate_builder_model (src/llm_wiki_cli/services/knowledge_index.py)"]
    n8["_array (src/llm_wiki_cli/services/knowledge_model.py)"]
    n9["_enum_value (src/llm_wiki_cli/services/knowledge_model.py)"]
    n10["_evaluated_revision (src/llm_wiki_cli/services/knowledge_model.py)"]
    n11["_external_uri (src/llm_wiki_cli/services/knowledge_model.py)"]
    n12["_hash (src/llm_wiki_cli/services/knowledge_model.py)"]
    n13["_link_observation_string (src/llm_wiki_cli/services/knowledge_model.py)"]
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
    click n0 "../modules/knowledge_model.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_freshness.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_index.md"
    click n8 "../modules/knowledge_model.md"
    click n9 "../modules/knowledge_model.md"
    click n10 "../modules/knowledge_model.md"
    click n11 "../modules/knowledge_model.md"
    click n12 "../modules/knowledge_model.md"
    click n13 "../modules/knowledge_model.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_envelope` | import | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_require_structure_state` | call | [knowledge_index](../modules/knowledge_index.md) | 3 |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) | 9 |
| `_validate_builder_link` | call | [knowledge_index](../modules/knowledge_index.md) | 17 |
| `_validate_builder_model` | call | [knowledge_index](../modules/knowledge_index.md) | 11 |
| `_array` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_enum_value` | call | [knowledge_model](../modules/knowledge_model.md) | 2 |
| `_evaluated_revision` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_external_uri` | call | [knowledge_model](../modules/knowledge_model.md) | 6 |
| `_hash` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |
| `_link_observation_string` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |

> References: showing 12 of 43 logical references; 31 omitted by the 12-row generated summary limit.
