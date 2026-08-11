# _BootstrapPageMaps

**Location:** `src/llm_wiki_cli/services/bootstrap_runtime.py:4120`
**Kind:** Class
**Bases:** —
**Module:** [bootstrap_runtime](../modules/bootstrap_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_BootstrapPageMaps` in `src/llm_wiki_cli/services/bootstrap_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `module_page_map` | `dict[str, str]` | *required* | — |
| `entity_page_name_cache` | `dict[tuple[str, str], str]` | *required* | — |
| `entity_occurrence_page_name_cache` | `dict[EntityOccurrenceKey, str]` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_BootstrapPageMaps (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1["_finalize_bootstrap (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["_finalize_bootstrap_artifacts (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["_generate_bootstrap_content (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n4["_governance_moves_for_bootstrap (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["_prepare_bootstrap_page_maps (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n6["_write_bootstrap_api_contract_page (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n7["_write_entity_and_module_pages (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/bootstrap_runtime.md"
    click n6 "../modules/bootstrap_runtime.md"
    click n7 "../modules/bootstrap_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [bootstrap_runtime](../modules/bootstrap_runtime.md) | 0 | `entity_occurrence_page_name_cache`, `entity_page_name_cache`, `module_page_map` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_finalize_bootstrap` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_finalize_bootstrap_artifacts` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_generate_bootstrap_content` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_governance_moves_for_bootstrap` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_prepare_bootstrap_page_maps` | call | [bootstrap_runtime](../modules/bootstrap_runtime.md) | 1 |
| `_prepare_bootstrap_page_maps` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_write_bootstrap_api_contract_page` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_write_entity_and_module_pages` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
