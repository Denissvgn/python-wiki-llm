# LinkSyntax

**Location:** `src/llm_wiki_cli/services/knowledge_links.py:62`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_links](../modules/knowledge_links.md)

## Description

Source syntax that produced one Markdown-owned observation.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `MARKDOWN` | `'markdown'` | — |
| `MARKDOWN_IMAGE` | `'markdown-image'` | — |
| `MERMAID_CLICK` | `'mermaid-click'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LinkSyntax (src/llm_wiki_cli/services/knowledge_links.py)"]
    n1["Enum"]
    n2["str"]
    n3["_index_source_link_occurrences (src/llm_wiki_cli/services/knowledge_index.py)"]
    n4["_validate_builder_link (src/llm_wiki_cli/services/knowledge_index.py)"]
    n5["_validate_observation_source_syntax (src/llm_wiki_cli/services/knowledge_index.py)"]
    n6["_build_observation (src/llm_wiki_cli/services/knowledge_links.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_links.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_index.md"
    click n6 "../modules/knowledge_links.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_links](../modules/knowledge_links.md) | 0 | `MARKDOWN`, `MARKDOWN_IMAGE`, `MERMAID_CLICK` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_index_source_link_occurrences` | type_reference | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_builder_link` | call | [knowledge_index](../modules/knowledge_index.md) |
| `_validate_observation_source_syntax` | type_reference | [knowledge_index](../modules/knowledge_index.md) |
| `_build_observation` | type_reference | [knowledge_links](../modules/knowledge_links.md) |
