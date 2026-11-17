# PageKind

**Location:** `src/llm_wiki_engine/wiki_surface.py:41`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [wiki_surface](../modules/wiki_surface.md)

## Description

_Auto-generated from `PageKind` in `src/llm_wiki_engine/wiki_surface.py`._

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

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PageKind (src/llm_wiki_engine/wiki_surface.py)"]
    n1["Enum"]
    n2["str"]
    n3["_status_label (src/llm_wiki_cli/commands/status_cmd.py)"]
    n4["_render_page (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n5["src/llm_wiki_cli/services/documentation_worklist.py"]
    n6["PageRequest.__post_init__ (src/llm_wiki_cli/services/domain_pack.py)"]
    n7["_surface_page_index (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n8["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n9["src/llm_wiki_cli/services/knowledge_generation.py"]
    n10["_surface_pages (src/llm_wiki_cli/services/knowledge_index.py)"]
    n11["ConceptKindSpec.__post_init__ (src/llm_wiki_cli/services/knowledge_kinds.py)"]
    n12["KindRegistry.page_kinds (src/llm_wiki_cli/services/knowledge_kinds.py)"]
    n13["src/llm_wiki_cli/services/knowledge_links.py"]
    n14["concept_kind_for_page_kind (src/llm_wiki_cli/services/knowledge_model.py)"]
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
    click n3 "../modules/status_cmd.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/documentation_worklist.md"
    click n6 "../modules/domain_pack.md"
    click n7 "../modules/knowledge_artifacts.md"
    click n8 "../modules/knowledge_freshness.md"
    click n9 "../modules/knowledge_generation.md"
    click n10 "../modules/knowledge_index.md"
    click n11 "../modules/knowledge_kinds.md"
    click n12 "../modules/knowledge_kinds.md"
    click n13 "../modules/knowledge_links.md"
    click n14 "../modules/knowledge_model.md"
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
| `_status_label` | type_reference | [status_cmd](../modules/status_cmd.md) | — |
| `_render_page` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `documentation_worklist` | import | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `PageRequest.__post_init__` | call | [domain_pack](../modules/domain_pack.md) | 1 |
| `_surface_page_index` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 1 |
| `knowledge_freshness` | import | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_surface_pages` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `ConceptKindSpec.__post_init__` | call | [knowledge_kinds](../modules/knowledge_kinds.md) | 1 |
| `KindRegistry.page_kinds` | type_reference | [knowledge_kinds](../modules/knowledge_kinds.md) | — |
| `knowledge_links` | import | [knowledge_links](../modules/knowledge_links.md) | — |
| `concept_kind_for_page_kind` | call | [knowledge_model](../modules/knowledge_model.md) | 1 |

> References: showing 12 of 40 logical references; 28 omitted by the 12-row generated summary limit.
