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
    n6["_expected_page_coordinates (src/llm_wiki_cli/services/knowledge_links.py)"]
    n7["_page_locator (src/llm_wiki_cli/services/knowledge_links.py)"]
    n8["_validate_asset_paths (src/llm_wiki_cli/services/knowledge_links.py)"]
    n9["_validate_page_content (src/llm_wiki_cli/services/knowledge_links.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/knowledge_links.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_links.md"
    click n4 "../modules/knowledge_links.md"
    click n5 "../modules/knowledge_links.md"
    click n6 "../modules/knowledge_links.md"
    click n7 "../modules/knowledge_links.md"
    click n8 "../modules/knowledge_links.md"
    click n9 "../modules/knowledge_links.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_build_observation` | call | [knowledge_links](../modules/knowledge_links.md) | 1 |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) | 6 |
| `_canonical_relative_path` | call | [knowledge_links](../modules/knowledge_links.md) | 4 |
| `_expected_page_coordinates` | call | [knowledge_links](../modules/knowledge_links.md) | 2 |
| `_page_locator` | call | [knowledge_links](../modules/knowledge_links.md) | 3 |
| `_validate_asset_paths` | call | [knowledge_links](../modules/knowledge_links.md) | 4 |
| `_validate_page_content` | call | [knowledge_links](../modules/knowledge_links.md) | 5 |
