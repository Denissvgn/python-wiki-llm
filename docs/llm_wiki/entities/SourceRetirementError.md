# SourceRetirementError

**Location:** `src/llm_wiki_engine/source_retirement.py:29`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [source_retirement](../modules/source_retirement.md)

## Description

A retirement record cannot be reconciled with authoritative ownership.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceRetirementError (src/llm_wiki_engine/source_retirement.py)"]
    n1["ValueError"]
    n2["run_release (src/llm_wiki_cli/services/historical_release.py)"]
    n3["_selected_paths (src/llm_wiki_cli/services/historical_retirement.py)"]
    n4["refuse (src/llm_wiki_cli/services/historical_retirement.py)"]
    n5["src/llm_wiki_cli/services/knowledge_generation.py"]
    n6["_historical_pages_for_lint (src/llm_wiki_cli/services/lint_service.py)"]
    n7["_merge_revived_source_page (src/llm_wiki_cli/services/sync_runtime.py)"]
    n8["_plan_source_page_transitions (src/llm_wiki_cli/services/sync_runtime.py)"]
    n9["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
    n10["_qualify_surviving_module_inventory (src/llm_wiki_cli/services/sync_runtime.py)"]
    n11["_sync_run_options_from_request (src/llm_wiki_cli/services/sync_runtime.py)"]
    n12["_refuse (src/llm_wiki_engine/historical_sources.py)"]
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
    n12 --> n0
    click n0 "../modules/source_retirement.md"
    click n2 "../modules/historical_release.md"
    click n3 "../modules/historical_retirement.md"
    click n4 "../modules/historical_retirement.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/sync_runtime.md"
    click n8 "../modules/sync_runtime.md"
    click n9 "../modules/sync_runtime.md"
    click n10 "../modules/sync_runtime.md"
    click n11 "../modules/sync_runtime.md"
    click n12 "../modules/historical_sources.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_retirement](../modules/source_retirement.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `run_release` | call | [historical_release](../modules/historical_release.md) | 6 |
| `_selected_paths` | call | [historical_retirement](../modules/historical_retirement.md) | 1 |
| `refuse` | call | [historical_retirement](../modules/historical_retirement.md) | 1 |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_historical_pages_for_lint` | call | [lint_service](../modules/lint_service.md) | 1 |
| `_merge_revived_source_page` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_plan_source_page_transitions` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_prepare_sync_run` | call | [sync_runtime](../modules/sync_runtime.md) | 2 |
| `_qualify_surviving_module_inventory` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_sync_run_options_from_request` | call | [sync_runtime](../modules/sync_runtime.md) | 3 |
| `_refuse` | call | [historical_sources](../modules/historical_sources.md) | 1 |
| `_refuse` | type_reference | [historical_sources](../modules/historical_sources.md) | — |

> References: showing 12 of 20 logical references; 8 omitted by the 12-row generated summary limit.
