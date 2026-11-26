# GeneratedSurfacePruneError

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:344`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_runtime](../modules/sync_runtime.md)

## Description

A stale generated page cannot be removed without explicit authority.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["GeneratedSurfacePruneError (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["ValueError"]
    n2["_enforce_sync_write_safety (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["_generated_surface_pages_without_index (src/llm_wiki_cli/services/sync_runtime.py)"]
    n4["_planned_generated_surface_prune (src/llm_wiki_cli/services/sync_runtime.py)"]
    n5["_regenerate_flow_pages (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["_regenerate_workflow_pages (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/sync_runtime.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/sync_runtime.md"
    click n4 "../modules/sync_runtime.md"
    click n5 "../modules/sync_runtime.md"
    click n6 "../modules/sync_runtime.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_runtime](../modules/sync_runtime.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_enforce_sync_write_safety` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_generated_surface_pages_without_index` | call | [sync_runtime](../modules/sync_runtime.md) | 3 |
| `_planned_generated_surface_prune` | call | [sync_runtime](../modules/sync_runtime.md) | 10 |
| `_regenerate_flow_pages` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_regenerate_workflow_pages` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
