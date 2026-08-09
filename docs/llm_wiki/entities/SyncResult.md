# SyncResult

**Location:** `src/llm_wiki_cli/commands/sync_cmd.py:589`
**Kind:** Class
**Bases:** —
**Module:** [sync_cmd](../modules/sync_cmd.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `SyncResult` in `src/llm_wiki_cli/commands/sync_cmd.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `created` | `int` | `0` | — |
| `updated` | `int` | `0` | — |
| `metadata_only` | `int` | `0` | — |
| `skipped` | `int` | `0` | — |
| `deprecated` | `int` | `0` | — |
| `preserved_semantic` | `int` | `0` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncResult (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n1["_append_log (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_applied_sync_has_changes (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_apply_current_infrastructure_plan (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n4["_apply_deselected_infrastructure_pages (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n5["_apply_diff (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n6["_apply_entity_page (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n7["_apply_infrastructure_plan (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n8["_apply_module_page (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n9["_apply_prepared_sync (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/sync_cmd.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/sync_cmd.md"
    click n5 "../modules/sync_cmd.md"
    click n6 "../modules/sync_cmd.md"
    click n7 "../modules/sync_cmd.md"
    click n8 "../modules/sync_cmd.md"
    click n9 "../modules/sync_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_cmd](../modules/sync_cmd.md) | 0 | `created`, `deprecated`, `metadata_only`, `preserved_semantic`, `skipped`, `updated` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_append_log` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_applied_sync_has_changes` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_current_infrastructure_plan` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_deselected_infrastructure_pages` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_diff` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_diff` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_entity_page` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_infrastructure_plan` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_module_page` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_prepared_sync` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_prepared_sync` | call | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_prepared_sync` | call | [sync_cmd](../modules/sync_cmd.md) |
