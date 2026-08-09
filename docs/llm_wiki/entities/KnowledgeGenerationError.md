# KnowledgeGenerationError

**Location:** `src/llm_wiki_cli/services/knowledge_generation.py:85`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_generation](../modules/knowledge_generation.md)

## Description

Field-specific failure at the shared generation-planning boundary.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeGenerationError (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n1["ValueError"]
    n2["_application_knowledge_extensions (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n3["_build_knowledge_generation_plan (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n4["_exact_source_mapping (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n5["_next_manifest_mapping (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n6["_raise_page_map_parity (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_generation.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/knowledge_generation.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_generation](../modules/knowledge_generation.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_application_knowledge_extensions` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_application_knowledge_extensions` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_build_knowledge_generation_plan` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_build_knowledge_generation_plan` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_build_knowledge_generation_plan` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_build_knowledge_generation_plan` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_exact_source_mapping` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_exact_source_mapping` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_exact_source_mapping` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_next_manifest_mapping` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_raise_page_map_parity` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_raise_page_map_parity` | call | [knowledge_generation](../modules/knowledge_generation.md) |
