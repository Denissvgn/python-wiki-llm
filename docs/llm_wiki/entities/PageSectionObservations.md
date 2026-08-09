# PageSectionObservations

**Location:** `src/llm_wiki_cli/services/section_ownership.py:111`
**Kind:** Class
**Bases:** —
**Module:** [section_ownership](../modules/section_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

All ordered section observations for one final Markdown page.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page_locator` | `str` | *required* | — |
| `page_kind` | `PageKind` | *required* | — |
| `source_hash` | `str` | *required* | — |
| `exact_hash` | `str` | *required* | — |
| `ordering_hash` | `str` | *required* | — |
| `sections` | `tuple[SectionObservation, ...]` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_payload` | `() -> dict[str, object]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageSectionObservations (src/llm_wiki_cli/services/section_ownership.py)"]
    n1["observe_page_sections (src/llm_wiki_cli/services/section_ownership.py)"]
    n2["section_ownership_extension (src/llm_wiki_cli/services/section_ownership.py)"]
    n3["serialize_section_ownership (src/llm_wiki_cli/services/section_ownership.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/section_ownership.md"
    click n1 "../modules/section_ownership.md"
    click n2 "../modules/section_ownership.md"
    click n3 "../modules/section_ownership.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [section_ownership](../modules/section_ownership.md) | 1 | `exact_hash`, `ordering_hash`, `page_kind`, `page_locator`, `sections`, `source_hash` |

### References

| Reference | Kind | Source |
|---|---|---|
| `observe_page_sections` | call | [section_ownership](../modules/section_ownership.md) |
| `observe_page_sections` | type_reference | [section_ownership](../modules/section_ownership.md) |
| `section_ownership_extension` | type_reference | [section_ownership](../modules/section_ownership.md) |
| `serialize_section_ownership` | type_reference | [section_ownership](../modules/section_ownership.md) |
