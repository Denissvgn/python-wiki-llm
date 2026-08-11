# ExtractorStatus

**Location:** `src/llm_wiki_cli/services/extraction_service.py:127`
**Kind:** Class
**Bases:** —
**Module:** [extraction_service](../modules/extraction_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ExtractorStatus` in `src/llm_wiki_cli/services/extraction_service.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `language` | `str` | *required* | — |
| `state` | `str` | *required* | — |
| `files_found` | `int` | *required* | — |
| `message` | `str` | `''` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExtractorStatus (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["_collect_inventory_outcomes (src/llm_wiki_cli/services/extraction_service.py)"]
    n2["_completed_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
    n3["_inventory_plugin_state (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_ordered_inventory_statuses (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_plan_language_extraction (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_save_inventory_cache (src/llm_wiki_cli/services/extraction_service.py)"]
    n7["_selected_extractor_plugin_components (src/llm_wiki_cli/services/extraction_service.py)"]
    n8["InventoryResult.failed (src/llm_wiki_cli/services/extraction_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/extraction_service.md"
    click n1 "../modules/extraction_service.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 0 | `files_found`, `language`, `message`, `state` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_collect_inventory_outcomes` | call | [extraction_service](../modules/extraction_service.md) | 2 |
| `_completed_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_inventory_plugin_state` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_ordered_inventory_statuses` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_plan_language_extraction` | call | [extraction_service](../modules/extraction_service.md) | 2 |
| `_plan_language_extraction` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_save_inventory_cache` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_selected_extractor_plugin_components` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `InventoryResult.failed` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
