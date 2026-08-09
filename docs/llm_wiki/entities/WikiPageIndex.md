# _WikiPageIndex

**Location:** `src/llm_wiki_cli/services/lint_service.py:308`
**Kind:** Class
**Bases:** —
**Module:** [lint_service](../modules/lint_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_WikiPageIndex` in `src/llm_wiki_cli/services/lint_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `pages` | `list[Path]` | *required* | — |
| `links_by_page` | `dict[Path, list[str]]` | *required* | — |
| `content_by_page` | `dict[Path, str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_WikiPageIndex (src/llm_wiki_cli/services/lint_service.py)"]
    n1["_build_page_index (src/llm_wiki_cli/services/lint_service.py)"]
    n2["_canonical_markdown_content (src/llm_wiki_cli/services/lint_service.py)"]
    n3["_check_broken_links (src/llm_wiki_cli/services/lint_service.py)"]
    n4["_check_generated_diagrams (src/llm_wiki_cli/services/lint_service.py)"]
    n5["_check_media_references (src/llm_wiki_cli/services/lint_service.py)"]
    n6["_check_orphan_pages (src/llm_wiki_cli/services/lint_service.py)"]
    n7["_check_workflow_coverage (src/llm_wiki_cli/services/lint_service.py)"]
    n8["_content_by_relative_path (src/llm_wiki_cli/services/lint_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/lint_service.md"
    click n1 "../modules/lint_service.md"
    click n2 "../modules/lint_service.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/lint_service.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/lint_service.md"
    click n8 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [lint_service](../modules/lint_service.md) | 0 | `content_by_page`, `links_by_page`, `pages` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_build_page_index` | call | [lint_service](../modules/lint_service.md) |
| `_build_page_index` | type_reference | [lint_service](../modules/lint_service.md) |
| `_canonical_markdown_content` | type_reference | [lint_service](../modules/lint_service.md) |
| `_check_broken_links` | type_reference | [lint_service](../modules/lint_service.md) |
| `_check_generated_diagrams` | type_reference | [lint_service](../modules/lint_service.md) |
| `_check_media_references` | type_reference | [lint_service](../modules/lint_service.md) |
| `_check_orphan_pages` | type_reference | [lint_service](../modules/lint_service.md) |
| `_check_workflow_coverage` | type_reference | [lint_service](../modules/lint_service.md) |
| `_content_by_relative_path` | type_reference | [lint_service](../modules/lint_service.md) |
