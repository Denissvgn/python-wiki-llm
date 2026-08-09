# KnowledgeIndexBuildError

**Location:** `src/llm_wiki_cli/services/knowledge_index.py:129`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_index](../modules/knowledge_index.md)

## Description

Field-specific failure at the pure knowledge-index join boundary.

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
    n0["KnowledgeIndexBuildError (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_generation.py"]
    n3["_expected_page_coordinates (src/llm_wiki_cli/services/knowledge_index.py)"]
    n4["_nonempty_string (src/llm_wiki_cli/services/knowledge_index.py)"]
    n5["_reject_extra_state (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_relative_path (src/llm_wiki_cli/services/knowledge_index.py)"]
    n7["_require_exact_keys (src/llm_wiki_cli/services/knowledge_index.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_index.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_index.md"
    click n7 "../modules/knowledge_index.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_index](../modules/knowledge_index.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) |
| `_expected_page_coordinates` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_expected_page_coordinates` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_nonempty_string` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_reject_extra_state` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_relative_path` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_relative_path` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_relative_path` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_relative_path` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_relative_path` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_require_exact_keys` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_require_exact_keys` | call | [knowledge_index](../modules/knowledge_index.md) |
