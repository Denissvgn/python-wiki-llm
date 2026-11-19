# BuiltInPageRenderer

**Location:** `src/llm_wiki_cli/services/domain_pack.py:225`
**Kind:** Class
**Bases:** —
**Module:** [domain_pack](../modules/domain_pack.md)

## Description

Today's code-documentation pages; subclass it to adjust them.

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
    n0["BuiltInPageRenderer (src/llm_wiki_cli/services/domain_pack.py)"]
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
