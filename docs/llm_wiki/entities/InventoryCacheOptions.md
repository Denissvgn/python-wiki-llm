# InventoryCacheOptions

**Location:** `src/llm_wiki_cli/services/inventory_cache.py:32`
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

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryCacheOptions (src/llm_wiki_cli/services/inventory_cache.py)"]
    n1["run (src/llm_wiki_cli/commands/ci_check_cmd.py)"]
    n2["_cache_options_from_args (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_sync_run_options_from_args (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n4["_collect_runtime (src/llm_wiki_cli/services/documentation_native.py)"]
    n5["_run_wiki_validation_pair (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n6["src/llm_wiki_cli/services/extraction_service.py"]
    n7["InventoryCache.__init__ (src/llm_wiki_cli/services/inventory_cache.py)"]
    n8["_collect_lint_inputs (src/llm_wiki_cli/services/lint_service.py)"]
    n9["build_report (src/llm_wiki_cli/services/lint_service.py)"]
    n10["run (src/llm_wiki_cli/services/lint_service.py)"]
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
    click n0 "../modules/inventory_cache.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/documentation_native.md"
    click n5 "../modules/integrity.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/inventory_cache.md"
    click n8 "../modules/lint_service.md"
    click n9 "../modules/lint_service.md"
    click n10 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [inventory_cache](../modules/inventory_cache.md) | 0 | `cache_dir`, `enabled`, `rebuild`, `stats_enabled` |

### References

| Reference | Kind | Source |
|---|---|---|
| `run` | call | [ci_check_cmd](../modules/ci_check_cmd.md) |
| `_cache_options_from_args` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_cache_options_from_args` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_sync_run_options_from_args` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_collect_runtime` | call | [documentation_native](../modules/documentation_native.md) |
| `_run_wiki_validation_pair` | call | [integrity](../modules/integrity.md) |
| `extraction_service` | import | [extraction_service](../modules/extraction_service.md) |
| `InventoryCache.__init__` | type_reference | [inventory_cache](../modules/inventory_cache.md) |
| `_collect_lint_inputs` | type_reference | [lint_service](../modules/lint_service.md) |
| `build_report` | type_reference | [lint_service](../modules/lint_service.md) |
| `run` | call | [lint_service](../modules/lint_service.md) |
