# InfrastructureSyncPlan

**Location:** `src/llm_wiki_cli/services/infrastructure_sync.py:367`
**Kind:** Class
**Bases:** —
**Module:** [infrastructure_sync](../modules/infrastructure_sync.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One immutable infrastructure regeneration plan.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `inventory` | `dict[str, dict]` | *required* | — |
| `prior_sources` | `dict[str, dict[str, object]]` | *required* | — |
| `current_sources` | `dict[str, dict[str, object]]` | *required* | — |
| `new_sources` | `tuple[str, ...]` | *required* | — |
| `changed_sources` | `tuple[str, ...]` | *required* | — |
| `unchanged_sources` | `tuple[str, ...]` | *required* | — |
| `removed_sources` | `tuple[str, ...]` | *required* | — |
| `moved_sources` | `dict[str, str]` | *required* | — |
| `unsupported_yaml` | `tuple[dict[str, object], ...]` | *required* | — |
| `discovery_roots` | `tuple[str, ...]` | *required* | — |
| `next_state` | `dict[str, object]` | *required* | — |
| `deselection_only_state` | `dict[str, object]` | *required* | — |
| `state_changed` | `bool` | *required* | — |
| `deselection_state_changed` | `bool` | *required* | — |
| `repair_tombstones` | `tuple[str, ...]` | `()` | — |
| `cleanup_moved_pages` | `tuple[str, ...]` | `()` | — |
| `deselected_records` | `dict[str, dict[str, object]]` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `has_deselection_changes` | `() -> bool` | `@property` | Return whether policy narrowing changes persisted infrastructure state. |
| `deselected_page_paths` | `() -> tuple[str, ...]` | `@property` | Return pages owned only by records removed through policy narrowing. |
| `affected_count` | `() -> int` | `@property` | — |
| `has_changes` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InfrastructureSyncPlan (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n1["build_infrastructure_sync_plan (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n2["with_infrastructure_deselection_generation_input (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n3["with_infrastructure_generation_input (src/llm_wiki_cli/services/infrastructure_sync.py)"]
    n4["_append_log (src/llm_wiki_cli/services/sync_runtime.py)"]
    n5["_apply_current_infrastructure_plan (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["_apply_deselected_infrastructure_pages (src/llm_wiki_cli/services/sync_runtime.py)"]
    n7["_apply_infrastructure_plan (src/llm_wiki_cli/services/sync_runtime.py)"]
    n8["_apply_sync_changes (src/llm_wiki_cli/services/sync_runtime.py)"]
    n9["_discover_infrastructure_plan (src/llm_wiki_cli/services/sync_runtime.py)"]
    n10["_exit_if_large_unforced_diff (src/llm_wiki_cli/services/sync_runtime.py)"]
    n11["_initialization_infrastructure_index_entries (src/llm_wiki_cli/services/sync_runtime.py)"]
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
    click n0 "../modules/infrastructure_sync.md"
    click n1 "../modules/infrastructure_sync.md"
    click n2 "../modules/infrastructure_sync.md"
    click n3 "../modules/infrastructure_sync.md"
    click n4 "../modules/sync_runtime.md"
    click n5 "../modules/sync_runtime.md"
    click n6 "../modules/sync_runtime.md"
    click n7 "../modules/sync_runtime.md"
    click n8 "../modules/sync_runtime.md"
    click n9 "../modules/sync_runtime.md"
    click n10 "../modules/sync_runtime.md"
    click n11 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [infrastructure_sync](../modules/infrastructure_sync.md) | 4 | `changed_sources`, `cleanup_moved_pages`, `current_sources`, `deselected_records`, `deselection_only_state`, `deselection_state_changed`, `discovery_roots`, `inventory`, `moved_sources`, `new_sources`, `next_state`, `prior_sources` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_infrastructure_sync_plan` | call | [infrastructure_sync](../modules/infrastructure_sync.md) | 1 |
| `build_infrastructure_sync_plan` | type_reference | [infrastructure_sync](../modules/infrastructure_sync.md) | — |
| `with_infrastructure_deselection_generation_input` | type_reference | [infrastructure_sync](../modules/infrastructure_sync.md) | — |
| `with_infrastructure_generation_input` | type_reference | [infrastructure_sync](../modules/infrastructure_sync.md) | — |
| `_append_log` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_current_infrastructure_plan` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_deselected_infrastructure_pages` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_infrastructure_plan` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_apply_sync_changes` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_discover_infrastructure_plan` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_exit_if_large_unforced_diff` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_initialization_infrastructure_index_entries` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |

> References: showing 12 of 21 logical references; 9 omitted by the 12-row generated summary limit.
