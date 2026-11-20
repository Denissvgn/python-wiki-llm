# StemPageNamer

**Location:** `src/llm_wiki_cli/services/domain_pack.py:366`
**Kind:** Class
**Bases:** —
**Module:** [domain_pack](../modules/domain_pack.md)

## Description

Module pages take the source file stem, entity pages the entity name.

Colliding names are qualified with parent directories (modules) or the
module page (entities), and names that collide on a case-insensitive or
Windows filesystem are made distinct.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `module_pages` | `(inventory: Mapping[str, Mapping[str, Any]]) -> dict[str, str]` | — | — |
| `entity_pages` | `(inventory: Mapping[str, Mapping[str, Any]], module_pages: Mapping[str, str]) -> dict[EntityOccurrenceKey, str]` | — | — |
| `__repr__` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["StemPageNamer (src/llm_wiki_cli/services/domain_pack.py)"]
    n1["src/llm_wiki_cli/engine/__init__.py"]
    n1 --> n0
    click n0 "../modules/domain_pack.md"
    click n1 "../modules/engine___init__.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [domain_pack](../modules/domain_pack.md) | 3 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
