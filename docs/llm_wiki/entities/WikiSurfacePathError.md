# WikiSurfacePathError

**Location:** `src/llm_wiki_cli/services/wiki_surface.py:32`
**Kind:** Class
**Bases:** `WikiSurfaceError`
**Module:** [wiki_surface](../modules/wiki_surface.md)

## Description

Raised when a canonical page path cannot be read inside its wiki root.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, *, relative_path: str) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiSurfacePathError (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["WikiSurfaceError (src/llm_wiki_cli/services/wiki_surface.py)"]
    n2["src/llm_wiki_cli/services/knowledge_loader.py"]
    n3["_collect_directory_pages (src/llm_wiki_cli/services/wiki_surface.py)"]
    n4["resolve_wiki_page_path (src/llm_wiki_cli/services/wiki_surface.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/wiki_surface.md"
    click n1 "../modules/wiki_surface.md"
    click n2 "../modules/knowledge_loader.md"
    click n3 "../modules/wiki_surface.md"
    click n4 "../modules/wiki_surface.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `WikiSurfaceError` | [wiki_surface](../modules/wiki_surface.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_loader` | import | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `_collect_directory_pages` | call | [wiki_surface](../modules/wiki_surface.md) | 1 |
| `resolve_wiki_page_path` | call | [wiki_surface](../modules/wiki_surface.md) | 3 |
