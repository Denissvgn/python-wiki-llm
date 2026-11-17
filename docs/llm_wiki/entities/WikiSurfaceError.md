# WikiSurfaceError

**Location:** `src/llm_wiki_cli/services/wiki_surface.py:25`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [wiki_surface](../modules/wiki_surface.md)

## Description

Raised for invalid wiki surface lookups.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiSurfaceError (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["ValueError"]
    n2["WikiSurfacePathError (src/llm_wiki_cli/services/wiki_surface.py)"]
    n3["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n4["src/llm_wiki_cli/services/concept_identity.py"]
    n5["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n6["src/llm_wiki_cli/services/knowledge_graph.py"]
    n7["src/llm_wiki_cli/services/knowledge_index.py"]
    n8["src/llm_wiki_cli/services/knowledge_links.py"]
    n9["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n10["src/llm_wiki_cli/services/migrate_runtime.py"]
    n11["src/llm_wiki_cli/services/source_retirement.py"]
    n12["src/llm_wiki_cli/services/surface_index_format.py"]
    n13["src/llm_wiki_cli/services/sync_runtime.py"]
    n14["src/llm_wiki_cli/services/sync_transitions.py"]
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
    n14 --> n0
    click n0 "../modules/wiki_surface.md"
    click n2 "../modules/wiki_surface.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/concept_identity.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_graph.md"
    click n7 "../modules/knowledge_index.md"
    click n8 "../modules/knowledge_links.md"
    click n9 "../modules/knowledge_storage_lifecycle.md"
    click n10 "../modules/migrate_runtime.md"
    click n11 "../modules/source_retirement.md"
    click n12 "../modules/surface_index_format.md"
    click n13 "../modules/sync_runtime.md"
    click n14 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `WikiSurfacePathError` | [wiki_surface](../modules/wiki_surface.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `concept_identity` | import | [concept_identity](../modules/concept_identity.md) | — |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_graph` | import | [knowledge_graph](../modules/knowledge_graph.md) | — |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) | — |
| `knowledge_links` | import | [knowledge_links](../modules/knowledge_links.md) | — |
| `knowledge_storage_lifecycle` | import | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | — |
| `migrate_runtime` | import | [migrate_runtime](../modules/migrate_runtime.md) | — |
| `source_retirement` | import | [source_retirement](../modules/source_retirement.md) | — |
| `surface_index_format` | import | [surface_index_format](../modules/surface_index_format.md) | — |
| `sync_runtime` | import | [sync_runtime](../modules/sync_runtime.md) | — |
| `sync_transitions` | import | [sync_transitions](../modules/sync_transitions.md) | — |

> References: showing 12 of 18 logical references; 6 omitted by the 12-row generated summary limit.
