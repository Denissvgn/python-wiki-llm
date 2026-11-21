# EntityPageRequest

**Location:** `src/llm_wiki_engine/pack_interfaces.py:97`
**Kind:** Class
**Bases:** —
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Everything a renderer gets for one entity page.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `entity` | `Mapping[str, Any]` | *required* | — |
| `source_path` | `str` | *required* | — |
| `module_page` | `str \| None` | *required* | — |
| `relationships` | `Mapping[str, Any]` | *required* | — |
| `relationship_summary` | `Mapping[str, Any]` | *required* | — |
| `module_pages` | `Mapping[str, str]` | *required* | — |
| `diagram_style` | `Mapping[str, Any] \| None` | *required* | — |
| `_builtin` | `Callable[[], str]` | `field(repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `builtin_markdown` | `() -> str` | — | The Markdown the built-in renderer writes for this page. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["EntityPageRequest (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["_generate_entity_md (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["render_with_pack (src/llm_wiki_cli/services/domain_pack.py)"]
    n3["BuiltInPageRenderer.render_entity (src/llm_wiki_engine/pack_interfaces.py)"]
    n4["PageRenderer.render_entity (src/llm_wiki_engine/pack_interfaces.py)"]
    n5["_rendered_entity (src/llm_wiki_engine/wiki_operations.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/domain_pack.md"
    click n3 "../modules/pack_interfaces.md"
    click n4 "../modules/pack_interfaces.md"
    click n5 "../modules/wiki_operations.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 1 | `_builtin`, `diagram_style`, `entity`, `module_page`, `module_pages`, `relationship_summary`, `relationships`, `source_path` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_generate_entity_md` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) | 1 |
| `render_with_pack` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `BuiltInPageRenderer.render_entity` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `PageRenderer.render_entity` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `_rendered_entity` | call | [wiki_operations](../modules/wiki_operations.md) | 1 |
