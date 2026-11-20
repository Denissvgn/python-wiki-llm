# PageRenderer

**Location:** `src/llm_wiki_engine/pack_interfaces.py:162`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

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
    n0["PageRenderer (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["Protocol"]
    n2["DomainPack.with_page_renderer (src/llm_wiki_cli/services/domain_pack.py)"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n2 "../modules/domain_pack.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 3 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `DomainPack.with_page_renderer` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
