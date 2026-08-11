# _PageRegistry

**Location:** `src/llm_wiki_cli/services/knowledge_links.py:126`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_links](../modules/knowledge_links.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_PageRegistry` in `src/llm_wiki_cli/services/knowledge_links.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `routes` | `Mapping[str, tuple[WikiSurfacePage, ...]]` | *required* | — |
| `locators` | `Mapping[str, tuple[WikiSurfacePage, ...]]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_PageRegistry (src/llm_wiki_cli/services/knowledge_links.py)"]
    n1["_build_observation (src/llm_wiki_cli/services/knowledge_links.py)"]
    n2["_build_page_registry (src/llm_wiki_cli/services/knowledge_links.py)"]
    n3["_classify_target (src/llm_wiki_cli/services/knowledge_links.py)"]
    n4["_validate_asset_paths (src/llm_wiki_cli/services/knowledge_links.py)"]
    n5["_validate_page_content (src/llm_wiki_cli/services/knowledge_links.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/knowledge_links.md"
    click n1 "../modules/knowledge_links.md"
    click n2 "../modules/knowledge_links.md"
    click n3 "../modules/knowledge_links.md"
    click n4 "../modules/knowledge_links.md"
    click n5 "../modules/knowledge_links.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_links](../modules/knowledge_links.md) | 0 | `locators`, `routes` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_observation` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
| `_build_page_registry` | call | [knowledge_links](../modules/knowledge_links.md) | 1 |
| `_build_page_registry` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
| `_classify_target` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
| `_validate_asset_paths` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
| `_validate_page_content` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |
