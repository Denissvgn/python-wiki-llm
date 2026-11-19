# PageRenderer

**Location:** `src/llm_wiki_cli/services/domain_pack.py:209`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [domain_pack](../modules/domain_pack.md)

**Decorators:** `@runtime_checkable`

## Description

Writes the Markdown of generated pages.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `render_module` | `(request: ModulePageRequest) -> str` | — | Return the Markdown of one module page. |
| `render_entity` | `(request: EntityPageRequest) -> str` | — | Return the Markdown of one entity page. |
| `render_page` | `(request: PageRequest) -> str` | — | Return the Markdown of one other generated page. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageRenderer (src/llm_wiki_cli/services/domain_pack.py)"]
    n1["Protocol"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["DomainPack.with_page_renderer (src/llm_wiki_cli/services/domain_pack.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/domain_pack.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/domain_pack.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [domain_pack](../modules/domain_pack.md) | 3 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `DomainPack.with_page_renderer` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
