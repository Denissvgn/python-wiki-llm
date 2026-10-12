# SourceRetirementError

**Location:** `src/llm_wiki_cli/services/source_retirement.py:23`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [source_retirement](../modules/source_retirement.md)

## Description

A retirement record cannot be reconciled with authoritative ownership.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceRetirementError (src/llm_wiki_cli/services/source_retirement.py)"]
    n1["ValueError"]
    n2["_plan_source_page_transitions (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_prepare_sync_run (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n4["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n5["src/llm_wiki_cli/services/knowledge_generation.py"]
    n6["src/llm_wiki_cli/services/lint_service.py"]
    n7["_check_duplicate_removal_custody (src/llm_wiki_cli/services/source_retirement.py)"]
    n8["discover_retired_entities (src/llm_wiki_cli/services/source_retirement.py)"]
    n9["entity_owner_present (src/llm_wiki_cli/services/source_retirement.py)"]
    n10["read_entity_retirement_state (src/llm_wiki_cli/services/source_retirement.py)"]
    n11["retired_entity_mappings (src/llm_wiki_cli/services/source_retirement.py)"]
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
    click n0 "../modules/source_retirement.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/knowledge_artifacts.md"
    click n5 "../modules/knowledge_generation.md"
    click n6 "../modules/lint_service.md"
    click n7 "../modules/source_retirement.md"
    click n8 "../modules/source_retirement.md"
    click n9 "../modules/source_retirement.md"
    click n10 "../modules/source_retirement.md"
    click n11 "../modules/source_retirement.md"
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
| `_plan_source_page_transitions` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `_prepare_sync_run` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `lint_service` | import | [lint_service](../modules/lint_service.md) | — |
| `_check_duplicate_removal_custody` | call | [source_retirement](../modules/source_retirement.md) | 2 |
| `discover_retired_entities` | call | [source_retirement](../modules/source_retirement.md) | 4 |
| `entity_owner_present` | call | [source_retirement](../modules/source_retirement.md) | 1 |
| `read_entity_retirement_state` | call | [source_retirement](../modules/source_retirement.md) | 9 |
| `retired_entity_mappings` | call | [source_retirement](../modules/source_retirement.md) | 1 |
