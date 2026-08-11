# MarkdownHeading

**Location:** `src/llm_wiki_cli/services/instruction_ownership.py:164`
**Kind:** Class
**Bases:** —
**Module:** [instruction_ownership](../modules/instruction_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One parsed Markdown heading and its actual local anchor.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `str` | *required* | — |
| `anchor` | `str` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MarkdownHeading (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1["_destination_heading_lookup (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n2["markdown_headings (src/llm_wiki_cli/services/instruction_ownership.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/instruction_ownership.md"
    click n1 "../modules/instruction_ownership.md"
    click n2 "../modules/instruction_ownership.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [instruction_ownership](../modules/instruction_ownership.md) | 0 | `anchor`, `title` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_destination_heading_lookup` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
| `markdown_headings` | call | [instruction_ownership](../modules/instruction_ownership.md) |
| `markdown_headings` | type_reference | [instruction_ownership](../modules/instruction_ownership.md) |
