# _HrefParser

**Location:** `src/llm_wiki_cli/services/site_html_check.py:20`
**Kind:** Class
**Bases:** `HTMLParser`
**Module:** [site_html_check](../modules/site_html_check.md)

## Description

_Auto-generated from `_HrefParser` in `src/llm_wiki_cli/services/site_html_check.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `() -> None` | — | — |
| `handle_starttag` | `(tag: str, attrs: list[tuple[str, Optional[str]]]) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_HrefParser (src/llm_wiki_cli/services/site_html_check.py)"]
    n1["HTMLParser"]
    n2["check_built_site_links (src/llm_wiki_cli/services/site_html_check.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/site_html_check.md"
    click n2 "../modules/site_html_check.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [site_html_check](../modules/site_html_check.md) | 2 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `HTMLParser` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `check_built_site_links` | call | [site_html_check](../modules/site_html_check.md) | 1 |
