# DomainPack

**Location:** `src/llm_wiki_cli/services/domain_pack.py:288`
**Kind:** Class
**Bases:** `_EngineDomainPack`
**Module:** [domain_pack](../modules/domain_pack.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A named set of domain decisions: classification, naming, rendering, context,
references and analysis helpers.

Unless given, a pack uses today's code-documentation parts: stem page
names, the built-in pages, code context, the built-in reference providers
and the bundled analysis helpers.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page_namer` | `PageNamer` | `field(default_factory=lambda: StemPageNamer())` | — |
| `page_renderer` | `PageRenderer` | `field(default_factory=lambda: BuiltInPageRenderer())` | — |
| `context_source` | `ContextSource` | `field(default_factory=lambda: CodeContextSource())` | — |
| `reference_providers` | `tuple[ReferenceProvider, ...]` | `BUILTIN_REFERENCE_PROVIDERS` | — |
| `helper_toolchain` | `HelperToolchain` | `field(default_factory=lambda: BundledHelperToolchain())` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DomainPack (src/llm_wiki_cli/services/domain_pack.py)"]
    n1["DomainPack (src/llm_wiki_engine/pack_interfaces.py)"]
    n2["Engine.__init__ (src/llm_wiki_cli/engine/__init__.py)"]
    n3["current_pack (src/llm_wiki_cli/services/domain_pack.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/domain_pack.md"
    click n1 "../modules/pack_interfaces.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/domain_pack.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [domain_pack](../modules/domain_pack.md) | 1 | `context_source`, `helper_toolchain`, `page_namer`, `page_renderer`, `reference_providers` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `DomainPack` | [pack_interfaces](../modules/pack_interfaces.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `Engine.__init__` | type_reference | [engine___init__](../modules/engine___init__.md) | — |
| `current_pack` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
