# _SurfaceInitializationPlan

**Location:** `src/llm_wiki_cli/commands/sync_cmd.py:1646`
**Kind:** Class
**Bases:** —
**Module:** [sync_cmd](../modules/sync_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_SurfaceInitializationPlan` in `src/llm_wiki_cli/commands/sync_cmd.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `surfaces` | `dict[str, dict]` | *required* | — |
| `policy_changed` | `bool` | *required* | — |
| `flow_entries` | `tuple[dict, ...]` | *required* | — |
| `new_flow_entries` | `tuple[dict, ...]` | *required* | — |
| `excluded_flow_tests` | `int` | *required* | — |
| `dependency_inventory` | `dict` | *required* | — |
| `dependency_analysis` | `dict \| None` | *required* | — |
| `dependency_target_pages` | `tuple[str, ...]` | *required* | — |
| `new_dependency_pages` | `tuple[str, ...]` | *required* | — |
| `requested_surfaces` | `frozenset[str]` | *required* | — |
| `excluded_dependency_tests` | `int` | `0` | — |
| `api_contracts` | `dict \| None` | `None` | — |
| `api_contract_target` | `bool` | `False` | — |
| `new_api_contract_page` | `bool` | `False` | — |
| `generation_inputs` | `dict[str, object]` | `field(default_factory=dict)` | — |
| `generation_inputs_changed` | `bool` | `False` | — |
| `managed_flow_page_paths` | `frozenset[str]` | `frozenset()` | — |
| `managed_workflow_page_paths` | `frozenset[str]` | `frozenset()` | — |
| `new_workflow_page_paths` | `tuple[str, ...]` | `()` | — |
| `managed_surface_index` | `bool` | `False` | — |
| `prior_surface_source_overrides` | `tuple[tuple[str, str], ...]` | `()` | — |
| `prior_flow_entries` | `tuple[dict, ...]` | `()` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `created_pages` | `() -> int` | `@property` | — |
| `has_work` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_SurfaceInitializationPlan (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n1["_append_log (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_apply_surface_page_changes (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_apply_sync_changes (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n4["_build_surface_initialization_plan (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n5["_build_sync_graph_observations (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n6["_canonical_sync_surface_flow_targets (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n7["_exit_if_large_unforced_surface_plan (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n8["_initialization_flow_entries (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n9["_large_surface_message (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n10["_print_dry_run_plan (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n11["_print_surface_summary (src/llm_wiki_cli/commands/sync_cmd.py)"]
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
    click n10 "../modules/sync_cmd.md"
    click n11 "../modules/sync_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_cmd](../modules/sync_cmd.md) | 2 | `api_contract_target`, `api_contracts`, `dependency_analysis`, `dependency_inventory`, `dependency_target_pages`, `excluded_dependency_tests`, `excluded_flow_tests`, `flow_entries`, `generation_inputs`, `generation_inputs_changed`, `managed_flow_page_paths`, `managed_surface_index` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_append_log` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_apply_surface_page_changes` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_apply_sync_changes` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_build_surface_initialization_plan` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `_build_surface_initialization_plan` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_build_sync_graph_observations` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_canonical_sync_surface_flow_targets` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_exit_if_large_unforced_surface_plan` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_initialization_flow_entries` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_large_surface_message` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_print_dry_run_plan` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_print_surface_summary` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
