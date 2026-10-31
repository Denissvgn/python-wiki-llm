# SyncAnalysisMutationError

**Location:** `src/llm_wiki_cli/services/sync_analysis_cache.py:25`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Description

A matched static-input snapshot changed before publication.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncAnalysisMutationError (src/llm_wiki_cli/services/sync_analysis_cache.py)"]
    n1["ValueError"]
    n2["_prepare_sync_run (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["build_payload (src/llm_wiki_cli/services/sync_analysis_cache.py)"]
    n4["generated_sections_match (src/llm_wiki_cli/services/sync_analysis_cache.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/sync_analysis_cache.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/sync_analysis_cache.md"
    click n4 "../modules/sync_analysis_cache.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_analysis_cache](../modules/sync_analysis_cache.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_prepare_sync_run` | call | [sync_cmd](../modules/sync_cmd.md) | 3 |
| `build_payload` | call | [sync_analysis_cache](../modules/sync_analysis_cache.md) | 1 |
| `generated_sections_match` | call | [sync_analysis_cache](../modules/sync_analysis_cache.md) | 1 |
