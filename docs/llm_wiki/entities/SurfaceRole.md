# SurfaceRole

**Location:** `src/llm_wiki_cli/services/wiki_surface.py:55`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [wiki_surface](../modules/wiki_surface.md)

## Description

_Auto-generated from `SurfaceRole` in `src/llm_wiki_cli/services/wiki_surface.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `GENERATED` | `'generated'` | — |
| `SEMANTIC` | `'semantic'` | — |
| `MIXED` | `'mixed'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SurfaceRole (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["Enum"]
    n2["str"]
    n3["_surface_pages (src/llm_wiki_cli/services/knowledge_index.py)"]
    n4["src/llm_wiki_cli/services/knowledge_model.py"]
    n5["src/llm_wiki_cli/services/knowledge_projection.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/wiki_surface.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_model.md"
    click n5 "../modules/knowledge_projection.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 0 | `GENERATED`, `MIXED`, `SEMANTIC` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_surface_pages` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `knowledge_model` | import | [knowledge_model](../modules/knowledge_model.md) | — |
| `knowledge_projection` | import | [knowledge_projection](../modules/knowledge_projection.md) | — |
