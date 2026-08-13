# PageKind

**Location:** `src/llm_wiki_cli/services/wiki_surface.py:41`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [wiki_surface](../modules/wiki_surface.md)

## Description

_Auto-generated from `PageKind` in `src/llm_wiki_cli/services/wiki_surface.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `INDEX` | `'index'` | — |
| `LOG` | `'log'` | — |
| `ENTITIES` | `'entities'` | — |
| `MODULES` | `'modules'` | — |
| `WORKFLOWS` | `'workflows'` | — |
| `GUIDES` | `'guides'` | — |
| `FLOWS` | `'flows'` | — |
| `INFRASTRUCTURE` | `'infrastructure'` | — |
| `API_CONTRACTS` | `'api-contracts'` | — |
| `DEPENDENCIES` | `'dependencies'` | — |
| `LOAD_ORDER` | `'load-order'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageKind (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["Enum"]
    n2["str"]
    n3["_prepare_migration_governance_plan (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n4["_surface_text_pages (src/llm_wiki_cli/commands/review_cmd.py)"]
    n5["_status_label (src/llm_wiki_cli/commands/status_cmd.py)"]
    n6["_has_generated_surface_shape (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n7["_has_neutral_generated_behavior (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n8["_planned_generated_surface_prune (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n9["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n10["src/llm_wiki_cli/services/documentation_native.py"]
    n11["src/llm_wiki_cli/services/documentation_worklist.py"]
    n12["_surface_page_index (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n13["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n14["src/llm_wiki_cli/services/knowledge_generation.py"]
    n0 --> n1
    n0 --> n2
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
    n14 --> n0
    click n0 "../modules/wiki_surface.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/review_cmd.md"
    click n5 "../modules/status_cmd.md"
    click n6 "../modules/sync_cmd.md"
    click n7 "../modules/sync_cmd.md"
    click n8 "../modules/sync_cmd.md"
    click n9 "../modules/bootstrap_runtime.md"
    click n10 "../modules/documentation_native.md"
    click n11 "../modules/documentation_worklist.md"
    click n12 "../modules/knowledge_artifacts.md"
    click n13 "../modules/knowledge_freshness.md"
    click n14 "../modules/knowledge_generation.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 0 | `API_CONTRACTS`, `DEPENDENCIES`, `ENTITIES`, `FLOWS`, `GUIDES`, `INDEX`, `INFRASTRUCTURE`, `LOAD_ORDER`, `LOG`, `MODULES`, `WORKFLOWS` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_prepare_migration_governance_plan` | call | [migrate_cmd](../modules/migrate_cmd.md) | 3 |
| `_surface_text_pages` | type_reference | [review_cmd](../modules/review_cmd.md) | — |
| `_status_label` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_has_generated_surface_shape` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_has_neutral_generated_behavior` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_planned_generated_surface_prune` | call | [sync_cmd](../modules/sync_cmd.md) | 2 |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
| `documentation_worklist` | import | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |

> References: showing 12 of 33 logical references; 21 omitted by the 12-row generated summary limit.
