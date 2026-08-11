# _HeadingCandidate

**Location:** `src/llm_wiki_cli/services/markdown_sections.py:199`
**Kind:** Class
**Bases:** —
**Module:** [markdown_sections](../modules/markdown_sections.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_HeadingCandidate` in `src/llm_wiki_cli/services/markdown_sections.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `level` | `int` | *required* | — |
| `title` | `str` | *required* | — |
| `start` | `int` | *required* | — |
| `body_start` | `int` | *required* | — |
| `parent_index` | `int \| None` | *required* | — |
| `heading_path` | `tuple[str, ...]` | *required* | — |
| `occurrence_path` | `tuple[int, ...]` | *required* | — |
| `occurrence` | `int` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_HeadingCandidate (src/llm_wiki_cli/services/markdown_sections.py)"]
    n1["parse_markdown_document (src/llm_wiki_cli/services/markdown_sections.py)"]
    n1 --> n0
    click n0 "../modules/markdown_sections.md"
    click n1 "../modules/markdown_sections.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [markdown_sections](../modules/markdown_sections.md) | 0 | `body_start`, `heading_path`, `level`, `occurrence`, `occurrence_path`, `parent_index`, `start`, `title` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `parse_markdown_document` | call | [markdown_sections](../modules/markdown_sections.md) | 1 |
