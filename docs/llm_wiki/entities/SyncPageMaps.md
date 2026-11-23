# _SyncPageMaps

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:1787`
**Kind:** Class
**Bases:** —
**Module:** [sync_runtime](../modules/sync_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_SyncPageMaps` in `src/llm_wiki_cli/services/sync_runtime.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `module_page_map` | `dict[str, str]` | *required* | — |
| `entity_page_cache` | `dict[tuple[str, str], str]` | *required* | — |
| `entity_occurrence_page_cache` | `dict[tuple[str, str, int], str]` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_SyncPageMaps (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["_apply_current_infrastructure_plan (src/llm_wiki_cli/services/sync_runtime.py)"]
    n2["_apply_infrastructure_plan (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["_apply_source_selection_prune (src/llm_wiki_cli/services/sync_runtime.py)"]
    n4["_apply_surface_page_changes (src/llm_wiki_cli/services/sync_runtime.py)"]
    n5["_apply_sync_changes (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["_compute_sync_diff (src/llm_wiki_cli/services/sync_runtime.py)"]
    n7["_prepare_sync_page_maps (src/llm_wiki_cli/services/sync_runtime.py)"]
    n8["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n9["_qualify_infrastructure_page_drift (src/llm_wiki_cli/services/sync_runtime.py)"]
    n10["_regenerate_api_contracts_page (src/llm_wiki_cli/services/sync_runtime.py)"]
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
    click n0 "../modules/sync_runtime.md"
    click n1 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/sync_runtime.md"
    click n4 "../modules/sync_runtime.md"
    click n5 "../modules/sync_runtime.md"
    click n6 "../modules/sync_runtime.md"
    click n7 "../modules/sync_runtime.md"
    click n8 "../modules/sync_runtime.md"
    click n9 "../modules/sync_runtime.md"
    click n10 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | `entity_occurrence_page_cache`, `entity_page_cache`, `module_page_map` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_apply_current_infrastructure_plan` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_infrastructure_plan` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_source_selection_prune` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_surface_page_changes` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_sync_changes` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_compute_sync_diff` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_prepare_sync_page_maps` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_prepare_sync_page_maps` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_prepare_sync_run` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_qualify_infrastructure_page_drift` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_regenerate_api_contracts_page` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
