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

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiSurfaceError (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n3["src/llm_wiki_cli/commands/sync_cmd.py"]
    n4["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n5["src/llm_wiki_cli/services/concept_identity.py"]
    n6["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n7["src/llm_wiki_cli/services/knowledge_graph.py"]
    n8["src/llm_wiki_cli/services/knowledge_index.py"]
    n9["src/llm_wiki_cli/services/knowledge_links.py"]
    n10["_entry_for (src/llm_wiki_cli/services/wiki_surface.py)"]
    n11["_validate_page_id (src/llm_wiki_cli/services/wiki_surface.py)"]
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
    click n0 "../modules/wiki_surface.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/bootstrap_runtime.md"
    click n5 "../modules/concept_identity.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_graph.md"
    click n8 "../modules/knowledge_index.md"
    click n9 "../modules/knowledge_links.md"
    click n10 "../modules/wiki_surface.md"
    click n11 "../modules/wiki_surface.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `migrate_cmd` | import | [migrate_cmd](../modules/migrate_cmd.md) |
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) |
| `bootstrap_runtime` | import | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| `concept_identity` | import | [concept_identity](../modules/concept_identity.md) |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| `knowledge_graph` | import | [knowledge_graph](../modules/knowledge_graph.md) |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) |
| `knowledge_links` | import | [knowledge_links](../modules/knowledge_links.md) |
| `_entry_for` | call | [wiki_surface](../modules/wiki_surface.md) |
| `_validate_page_id` | call | [wiki_surface](../modules/wiki_surface.md) |
| `_validate_page_id` | call | [wiki_surface](../modules/wiki_surface.md) |
| `_validate_page_id` | call | [wiki_surface](../modules/wiki_surface.md) |
