# InventoryCacheOptions

**Location:** `src/llm_wiki_cli/services/inventory_cache.py:37`
**Kind:** Class
**Bases:** —
**Module:** [inventory_cache](../modules/inventory_cache.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Runtime cache controls for inventory-producing commands.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `enabled` | `bool` | `False` | — |
| `rebuild` | `bool` | `False` | — |
| `cache_dir` | `str \| None` | `None` | — |
| `stats_enabled` | `bool` | `False` | — |
| `destination` | `RuntimeDestination \| None` | `field(default=None, repr=False, compare=False)` | — |
| `warning` | `WarningSink \| None` | `field(default=None, repr=False, compare=False)` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryCacheOptions (src/llm_wiki_cli/services/inventory_cache.py)"]
    n1["_collect_runtime (src/llm_wiki_cli/services/documentation_native.py)"]
    n2["_run_wiki_validation_pair (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n3["src/llm_wiki_cli/services/extraction_service.py"]
    n4["cache_options_for (src/llm_wiki_cli/services/inventory_cache.py)"]
    n5["cache_options_from_args (src/llm_wiki_cli/services/inventory_cache.py)"]
    n6["InventoryCache.__init__ (src/llm_wiki_cli/services/inventory_cache.py)"]
    n7["prepare_cache_options (src/llm_wiki_cli/services/inventory_cache.py)"]
    n8["_collect_lint_inputs (src/llm_wiki_cli/services/lint_service.py)"]
    n9["build_report (src/llm_wiki_cli/services/lint_service.py)"]
    n10["build_maintenance_queue (src/llm_wiki_cli/services/maintenance_queue.py)"]
    n11["_cache_options_from_args (src/llm_wiki_cli/services/sync_runtime.py)"]
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
    click n0 "../modules/inventory_cache.md"
    click n1 "../modules/documentation_native.md"
    click n2 "../modules/integrity.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/inventory_cache.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/inventory_cache.md"
    click n7 "../modules/inventory_cache.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/lint_service.md"
    click n10 "../modules/maintenance_queue.md"
    click n11 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [inventory_cache](../modules/inventory_cache.md) | 0 | `cache_dir`, `destination`, `enabled`, `rebuild`, `stats_enabled`, `warning` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_collect_runtime` | call | [documentation_native](../modules/documentation_native.md) | 1 |
| `_run_wiki_validation_pair` | call | [integrity](../modules/integrity.md) | 1 |
| `extraction_service` | import | [extraction_service](../modules/extraction_service.md) | — |
| `cache_options_for` | call | [inventory_cache](../modules/inventory_cache.md) | 1 |
| `cache_options_for` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
| `cache_options_from_args` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
| `InventoryCache.__init__` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
| `prepare_cache_options` | type_reference | [inventory_cache](../modules/inventory_cache.md) | — |
| `_collect_lint_inputs` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `build_report` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `build_maintenance_queue` | call | [maintenance_queue](../modules/maintenance_queue.md) | 1 |
| `_cache_options_from_args` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
