# SourceRetirementError

**Location:** `src/llm_wiki_cli/services/source_retirement.py:27`
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
    n0["SourceRetirementError (src/llm_wiki_cli/services/source_retirement.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n3["src/llm_wiki_cli/services/knowledge_generation.py"]
    n4["src/llm_wiki_cli/services/lint_service.py"]
    n5["_check_duplicate_removal_custody (src/llm_wiki_cli/services/source_retirement.py)"]
    n6["discover_retired_entities (src/llm_wiki_cli/services/source_retirement.py)"]
    n7["entity_owner_present (src/llm_wiki_cli/services/source_retirement.py)"]
    n8["qualified_retired_entity_locators (src/llm_wiki_cli/services/source_retirement.py)"]
    n9["read_entity_retirement_state (src/llm_wiki_cli/services/source_retirement.py)"]
    n10["retained_empty_module_paths (src/llm_wiki_cli/services/source_retirement.py)"]
    n11["retired_entity_mappings (src/llm_wiki_cli/services/source_retirement.py)"]
    n12["_plan_source_page_transitions (src/llm_wiki_cli/services/sync_runtime.py)"]
    n13["_prepare_sync_run (src/llm_wiki_cli/services/sync_runtime.py)"]
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
    n13 --> n0
    click n0 "../modules/source_retirement.md"
    click n2 "../modules/knowledge_artifacts.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/lint_service.md"
    click n5 "../modules/source_retirement.md"
    click n6 "../modules/source_retirement.md"
    click n7 "../modules/source_retirement.md"
    click n8 "../modules/source_retirement.md"
    click n9 "../modules/source_retirement.md"
    click n10 "../modules/source_retirement.md"
    click n11 "../modules/source_retirement.md"
    click n12 "../modules/sync_runtime.md"
    click n13 "../modules/sync_runtime.md"
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
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `_check_duplicate_removal_custody` | call | [source_retirement](../modules/source_retirement.md) | 2 |
| `discover_retired_entities` | call | [source_retirement](../modules/source_retirement.md) | 4 |
| `entity_owner_present` | call | [source_retirement](../modules/source_retirement.md) | 1 |
| `qualified_retired_entity_locators` | call | [source_retirement](../modules/source_retirement.md) | 2 |
| `read_entity_retirement_state` | call | [source_retirement](../modules/source_retirement.md) | 9 |
| `retained_empty_module_paths` | call | [source_retirement](../modules/source_retirement.md) | 1 |
| `retired_entity_mappings` | call | [source_retirement](../modules/source_retirement.md) | 1 |
| `_plan_source_page_transitions` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |
| `_prepare_sync_run` | call | [sync_runtime](../modules/sync_runtime.md) | 1 |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
