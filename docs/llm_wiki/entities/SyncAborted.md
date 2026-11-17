# SyncAborted

**Location:** `src/llm_wiki_cli/services/sync_runtime.py:264`
**Kind:** Class
**Bases:** `SystemExit`
**Module:** [sync_runtime](../modules/sync_runtime.md)

## Description

Sync stopped after writing why to the host's stderr.

``code`` is the CLI exit status. It derives from ``SystemExit`` so that
every cleanup path between the stop and the command boundary behaves as it
did when the command exited; :func:`execute_sync` turns it into
:class:`SyncError`.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncAborted (src/llm_wiki_cli/services/sync_runtime.py)"]
    n1["SystemExit"]
    n2["SyncRequestAborted (src/llm_wiki_cli/services/sync_runtime.py)"]
    n3["_exit_if_large_unforced_diff (src/llm_wiki_cli/services/sync_runtime.py)"]
    n4["_exit_if_large_unforced_surface_plan (src/llm_wiki_cli/services/sync_runtime.py)"]
    n5["_extract_current_inventory (src/llm_wiki_cli/services/sync_runtime.py)"]
    n6["_load_or_seed_manifest (src/llm_wiki_cli/services/sync_runtime.py)"]
    n7["_run_prepared_sync (src/llm_wiki_cli/services/sync_runtime.py)"]
    n8["_run_sync_dry_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n9["_run_sync_options (src/llm_wiki_cli/services/sync_runtime.py)"]
    n10["run_request (src/llm_wiki_cli/services/sync_runtime.py)"]
    n0 --> n1
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
| [sync_runtime](../modules/sync_runtime.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `SystemExit` | — |
| Subclass | `SyncRequestAborted` | [sync_runtime](../modules/sync_runtime.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_exit_if_large_unforced_diff` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_exit_if_large_unforced_surface_plan` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_extract_current_inventory` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_load_or_seed_manifest` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_run_prepared_sync` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_run_sync_dry_run` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_run_sync_options` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `run_request` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
