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
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_model.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_freshness.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
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

| Reference | Kind | Source |
|---|---|---|
| `knowledge_envelope` | import | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) |
| `_require_structure_state` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_require_structure_state` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_require_structure_state` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_derived` | call | [knowledge_index](../modules/knowledge_index.md) |
