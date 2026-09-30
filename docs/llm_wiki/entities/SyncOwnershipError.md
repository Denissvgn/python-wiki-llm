# SyncOwnershipError

**Location:** `src/llm_wiki_cli/services/sync_analysis.py:26`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_analysis](../modules/sync_analysis.md)

## Description

A page cannot be safely assigned to one recorded source entity.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncOwnershipError (src/llm_wiki_cli/services/sync_analysis.py)"]
    n1["ValueError"]
    n2["PageTransitionError (src/llm_wiki_cli/services/sync_transitions.py)"]
    n3["src/llm_wiki_cli/commands/sync_cmd.py"]
    n4["_ownership_error (src/llm_wiki_cli/services/sync_analysis.py)"]
    n5["_recorded_entity_pages (src/llm_wiki_cli/services/sync_analysis.py)"]
    n6["src/llm_wiki_cli/services/sync_transitions.py"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/sync_analysis.md"
    click n2 "../modules/sync_transitions.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/sync_analysis.md"
    click n5 "../modules/sync_analysis.md"
    click n6 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_analysis](../modules/sync_analysis.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `PageTransitionError` | [sync_transitions](../modules/sync_transitions.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) | — |
| `_ownership_error` | call | [sync_analysis](../modules/sync_analysis.md) | 1 |
| `_ownership_error` | type_reference | [sync_analysis](../modules/sync_analysis.md) | — |
| `_recorded_entity_pages` | call | [sync_analysis](../modules/sync_analysis.md) | 2 |
| `sync_transitions` | import | [sync_transitions](../modules/sync_transitions.md) | — |
