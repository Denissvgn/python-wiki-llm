# PageRequest

**Location:** `src/llm_wiki_engine/pack_interfaces.py:123`
**Kind:** Class
**Bases:** —
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Everything a renderer gets for one page that is not a module or entity.

``inputs`` holds what the built-in page is generated from, by name:

* ``index``: ``entity_names``, ``module_entries``, ``workflow_entries``,
  ``guide_entries``, ``infra_entries``, ``flow_entries``,
  ``architecture_entries``, ``retired_entity_pages``,
  ``api_contracts_present``, ``log_present``;
* ``workflows``: ``name``, ``workflow``, ``module_pages``;
* ``flows``: ``flow``, ``module_pages``, ``data_flow``,
  ``diagram_style``, ``api_contract_operations``;
* ``infrastructure``: ``source_path``, ``info``, ``module_links``,
  ``unsupported_sources``;
* ``api-contracts``: ``contracts``, ``module_pages``, ``entity_pages``;
* ``dependencies``: ``analysis``, ``module_pages``, ``detail``,
  ``diagram_style``;
* ``load-order``: ``analysis``, ``module_pages``.

Absent optional inputs are ``None``.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page_kind` | `PageKind` | *required* | — |
| `inputs` | `Mapping[str, Any]` | *required* | — |
| `_builtin` | `Callable[[], str]` | `field(repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `builtin_markdown` | `() -> str` | — | The Markdown the built-in renderer writes for this page. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageRequest (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["_render_page (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["BuiltInPageRenderer.render_entity (src/llm_wiki_cli/services/domain_pack.py)"]
    n3["BuiltInPageRenderer.render_module (src/llm_wiki_cli/services/domain_pack.py)"]
    n4["BuiltInPageRenderer.render_page (src/llm_wiki_cli/services/domain_pack.py)"]
    n5["render_with_pack (src/llm_wiki_cli/services/domain_pack.py)"]
    n6["PageRenderer.render_entity (src/llm_wiki_engine/pack_interfaces.py)"]
    n7["PageRenderer.render_module (src/llm_wiki_engine/pack_interfaces.py)"]
    n8["PageRenderer.render_page (src/llm_wiki_engine/pack_interfaces.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/domain_pack.md"
    click n3 "../modules/domain_pack.md"
    click n4 "../modules/domain_pack.md"
    click n5 "../modules/domain_pack.md"
    click n6 "../modules/pack_interfaces.md"
    click n7 "../modules/pack_interfaces.md"
    click n8 "../modules/pack_interfaces.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 2 | `_builtin`, `inputs`, `page_kind` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_render_page` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) | 1 |
| `BuiltInPageRenderer.render_entity` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `BuiltInPageRenderer.render_module` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `BuiltInPageRenderer.render_page` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `render_with_pack` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `PageRenderer.render_entity` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `PageRenderer.render_module` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
| `PageRenderer.render_page` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
