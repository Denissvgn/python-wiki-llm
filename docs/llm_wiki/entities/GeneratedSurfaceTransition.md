# _GeneratedSurfaceTransition

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:1935`
**Kind:** Class
**Bases:** —
**Module:** [sync_runtime](../modules/sync_runtime.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Prior ownership proof and generated pages that cross the live boundary.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `retired_page_paths` | `tuple[str, ...]` | `()` | — |
| `protected_retirement_paths` | `tuple[str, ...]` | `()` | — |
| `managed_flow_page_paths` | `frozenset[str]` | `frozenset()` | — |
| `managed_workflow_page_paths` | `frozenset[str]` | `frozenset()` | — |
| `managed_surface_index` | `bool` | `False` | — |
| `prior_source_overrides` | `tuple[tuple[str, str], ...]` | `()` | — |
| `prior_flow_entries` | `tuple[dict, ...]` | `()` | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_GeneratedSurfaceTransition (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["_planned_generated_surface_prune (src/llm_wiki_cli/services/sync_runtime.py)"]
    n2["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/sync_runtime.md"
    click n1 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | `managed_flow_page_paths`, `managed_surface_index`, `managed_workflow_page_paths`, `prior_flow_entries`, `prior_source_overrides`, `protected_retirement_paths`, `retired_page_paths` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_planned_generated_surface_prune` | call | [sync_runtime](../modules/sync_runtime.md) | 2 |
| `_planned_generated_surface_prune` | type_reference | [sync_runtime](../modules/sync_runtime.md) | — |
| `_prepare_sync_run` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
