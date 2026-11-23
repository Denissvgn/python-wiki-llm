# DomainPack

**Location:** `src/llm_wiki_engine/pack_interfaces.py:551`
**Kind:** Class
**Bases:** —
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A named set of domain decisions: classification, naming, rendering, context,
references and analysis helpers.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `str` | *required* | — |
| `classifier` | `SourceClassifier` | *required* | — |
| `page_namer` | `PageNamer` | `field(default_factory=lambda: StemPageNamer())` | — |
| `page_renderer` | `PageRenderer` | `field(default_factory=lambda: BuiltInPageRenderer())` | — |
| `context_source` | `ContextSource` | `field(default_factory=lambda: NoContextSource())` | — |
| `reference_providers` | `tuple[Any, ...]` | `()` | — |
| `helper_toolchain` | `HelperToolchain` | `field(default_factory=lambda: NoHelperToolchain())` | — |
| `extractors` | `Mapping[str, str]` | `field(default_factory=dict, hash=False)` | — |
| `integrations` | `IntegrationSet` | `DEFAULT_INTEGRATIONS` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `with_classifier` | `(classifier: SourceClassifier) -> Self` | — | A copy of this pack that classifies sources with ``classifier``. |
| `with_page_namer` | `(page_namer: PageNamer) -> Self` | — | A copy of this pack that names pages with ``page_namer``. |
| `with_page_renderer` | `(page_renderer: PageRenderer) -> Self` | — | A copy of this pack that writes pages with ``page_renderer``. |
| `with_context_source` | `(context_source: ContextSource) -> Self` | — | A copy of this pack that builds budgeted context with ``context_source``. |
| `with_reference_provider` | `(provider: Any) -> Self` | — | A copy of this pack that also serves ``provider``, replacing one of the same kind. |
| `with_extractor` | `(source_kind: str, entry_point: str) -> Self` | — | A copy of this pack that extracts ``source_kind`` with ``entry_point``. |
| `with_helper_toolchain` | `(helper_toolchain: HelperToolchain) -> Self` | — | A copy of this pack that prepares analysis helpers with ``helper_toolchain``. |
| `with_integrations` | `(integrations: IntegrationSet) -> Self` | — | A copy of this pack whose knowledge core uses ``integrations``. |
| `describe` | `() -> dict[str, Any]` | — | A JSON-ready summary of the pack. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DomainPack (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["DomainPack (src/llm_wiki_cli/services/domain_pack.py)"]
    n2["current_pack (src/llm_wiki_cli/services/domain_pack.py)"]
    n3["Engine.__init__ (src/llm_wiki_engine/engine.py)"]
    n4["Engine.pack (src/llm_wiki_engine/engine.py)"]
    n5["active_pack (src/llm_wiki_engine/pack_interfaces.py)"]
    n6["current_pack (src/llm_wiki_engine/pack_interfaces.py)"]
    n7["using_pack (src/llm_wiki_engine/pack_interfaces.py)"]
    n8["_classified_sources (src/llm_wiki_engine/wiki_operations.py)"]
    n9["_extract (src/llm_wiki_engine/wiki_operations.py)"]
    n10["_pack (src/llm_wiki_engine/wiki_operations.py)"]
    n11["_render (src/llm_wiki_engine/wiki_operations.py)"]
    n12["_rendered_entity (src/llm_wiki_engine/wiki_operations.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n1 "../modules/domain_pack.md"
    click n2 "../modules/domain_pack.md"
    click n3 "../modules/engine.md"
    click n4 "../modules/engine.md"
    click n5 "../modules/pack_interfaces.md"
    click n6 "../modules/pack_interfaces.md"
    click n7 "../modules/pack_interfaces.md"
    click n8 "../modules/wiki_operations.md"
    click n9 "../modules/wiki_operations.md"
    click n10 "../modules/wiki_operations.md"
    click n11 "../modules/wiki_operations.md"
    click n12 "../modules/wiki_operations.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 10 | `classifier`, `context_source`, `extractors`, `helper_toolchain`, `integrations`, `name`, `page_namer`, `page_renderer`, `reference_providers` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `DomainPack` | [domain_pack](../modules/domain_pack.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `current_pack` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `Engine.__init__` | type_reference | [engine](../modules/engine.md) | — |
| `Engine.pack` | type_reference | [engine](../modules/engine.md) | — |
| `active_pack` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `current_pack` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `using_pack` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `_classified_sources` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
| `_extract` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
| `_pack` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
| `_render` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
| `_rendered_entity` | type_reference | [wiki_operations](../modules/wiki_operations.md) | — |
