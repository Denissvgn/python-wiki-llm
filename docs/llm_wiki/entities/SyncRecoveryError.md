# SyncRecoveryError

**Location:** `src/llm_wiki_cli/services/sync_recovery.py:42`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_recovery](../modules/sync_recovery.md)

## Description

A recovery proof or operation cannot be admitted safely.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncRecoveryError (src/llm_wiki_cli/services/sync_recovery.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/sync_cmd.py"]
    n3["_page (src/llm_wiki_cli/services/sync_recovery.py)"]
    n4["_policy_inputs (src/llm_wiki_cli/services/sync_recovery.py)"]
    n5["_root_identity (src/llm_wiki_cli/services/sync_recovery.py)"]
    n6["_safe (src/llm_wiki_cli/services/sync_recovery.py)"]
    n7["NewPageJournal._persist (src/llm_wiki_cli/services/sync_recovery.py)"]
    n8["NewPageJournal.after_write (src/llm_wiki_cli/services/sync_recovery.py)"]
    n9["NewPageJournal.before_write (src/llm_wiki_cli/services/sync_recovery.py)"]
    n10["NewPageJournal.discard_committed (src/llm_wiki_cli/services/sync_recovery.py)"]
    n11["recover_new_sync_pages (src/llm_wiki_cli/services/sync_recovery.py)"]
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
    n11 --> n0
    click n0 "../modules/sync_recovery.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/sync_recovery.md"
    click n4 "../modules/sync_recovery.md"
    click n5 "../modules/sync_recovery.md"
    click n6 "../modules/sync_recovery.md"
    click n7 "../modules/sync_recovery.md"
    click n8 "../modules/sync_recovery.md"
    click n9 "../modules/sync_recovery.md"
    click n10 "../modules/sync_recovery.md"
    click n11 "../modules/sync_recovery.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_recovery](../modules/sync_recovery.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) | — |
| `_page` | call | [sync_recovery](../modules/sync_recovery.md) | 2 |
| `_policy_inputs` | call | [sync_recovery](../modules/sync_recovery.md) | 1 |
| `_root_identity` | call | [sync_recovery](../modules/sync_recovery.md) | 1 |
| `_safe` | call | [sync_recovery](../modules/sync_recovery.md) | 1 |
| `NewPageJournal._persist` | call | [sync_recovery](../modules/sync_recovery.md) | 1 |
| `NewPageJournal.after_write` | call | [sync_recovery](../modules/sync_recovery.md) | 1 |
| `NewPageJournal.before_write` | call | [sync_recovery](../modules/sync_recovery.md) | 5 |
| `NewPageJournal.discard_committed` | call | [sync_recovery](../modules/sync_recovery.md) | 5 |
| `recover_new_sync_pages` | call | [sync_recovery](../modules/sync_recovery.md) | 28 |
