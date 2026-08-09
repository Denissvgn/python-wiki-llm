# KnowledgeLinkError

**Location:** `src/llm_wiki_cli/services/knowledge_links.py:53`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_links](../modules/knowledge_links.md)

## Description

Field-specific invalid input at the pure link-collection boundary.

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
    n0["KnowledgeLinkError (src/llm_wiki_cli/services/knowledge_links.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_generation.py"]
    n3["_build_observation (src/llm_wiki_cli/services/knowledge_links.py)"]
    n4["_build_page_registry (src/llm_wiki_cli/services/knowledge_links.py)"]
    n5["_canonical_relative_path (src/llm_wiki_cli/services/knowledge_links.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_links.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_links.md"
    click n4 "../modules/knowledge_links.md"
    click n5 "../modules/knowledge_links.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_links](../modules/knowledge_links.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) |
| `_build_observation` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_canonical_relative_path` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_canonical_relative_path` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_canonical_relative_path` | call | [knowledge_links](../modules/knowledge_links.md) |
| `_canonical_relative_path` | call | [knowledge_links](../modules/knowledge_links.md) |
