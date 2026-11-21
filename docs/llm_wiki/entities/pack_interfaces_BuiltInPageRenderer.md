# BuiltInPageRenderer

**Location:** `src/llm_wiki_engine/pack_interfaces.py:327`
**Kind:** Class
**Bases:** —
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

## Description

Writes each page's built-in Markdown unchanged; subclass it to adjust pages.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `render_module` | `(request: ModulePageRequest) -> str` | — | — |
| `render_entity` | `(request: EntityPageRequest) -> str` | — | — |
| `render_page` | `(request: PageRequest) -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BuiltInPageRenderer (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["BuiltInPageRenderer (src/llm_wiki_cli/services/domain_pack.py)"]
    n2["src/llm_wiki_cli/services/domain_pack.py"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n1 "../modules/domain_pack.md"
    click n2 "../modules/domain_pack.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 3 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `BuiltInPageRenderer` | [domain_pack](../modules/domain_pack.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `domain_pack` | import | [domain_pack](../modules/domain_pack.md) | — |
