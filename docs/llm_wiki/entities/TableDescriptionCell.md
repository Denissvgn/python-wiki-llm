# TableDescriptionCell

**Location:** `src/llm_wiki_cli/services/markdown_sections.py:176`
**Kind:** Class
**Bases:** —
**Module:** [markdown_sections](../modules/markdown_sections.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One table Description cell without lossy duplicate-key collapse.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `key` | `str` | *required* | — |
| `occurrence` | `int` | *required* | — |
| `description` | `str` | *required* | — |
| `row_index` | `int` | *required* | — |
| `cells` | `tuple[str, ...]` | *required* | — |
| `description_index` | `int` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["TableDescriptionCell (src/llm_wiki_cli/services/markdown_sections.py)"]
    n1["description_table_cells (src/llm_wiki_cli/services/markdown_sections.py)"]
    n1 --> n0
    click n0 "../modules/markdown_sections.md"
    click n1 "../modules/markdown_sections.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [markdown_sections](../modules/markdown_sections.md) | 0 | `cells`, `description`, `description_index`, `key`, `occurrence`, `row_index` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `description_table_cells` | call | [markdown_sections](../modules/markdown_sections.md) | 1 |
| `description_table_cells` | type_reference | [markdown_sections](../modules/markdown_sections.md) | — |
