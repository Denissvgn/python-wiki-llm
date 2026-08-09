# SiteExportError

**Location:** `src/llm_wiki_cli/services/site_export.py:108`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [site_export](../modules/site_export.md)

## Description

Raised for invalid static-site export requests.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SiteExportError (src/llm_wiki_cli/services/site_export.py)"]
    n1["ValueError"]
    n2["_knowledge_metadata (src/llm_wiki_cli/commands/site_cmd.py)"]
    n3["_load_hub_knowledge_projections (src/llm_wiki_cli/commands/site_cmd.py)"]
    n4["_load_knowledge_projection (src/llm_wiki_cli/commands/site_cmd.py)"]
    n5["src/llm_wiki_cli/services/documentation_run/export.py"]
    n6["_build_publication_selection (src/llm_wiki_cli/services/site_export.py)"]
    n7["_file_digest (src/llm_wiki_cli/services/site_export.py)"]
    n8["_find_unexpected_knowledge_pages (src/llm_wiki_cli/services/site_export.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/site_export.md"
    click n2 "../modules/site_cmd.md"
    click n3 "../modules/site_cmd.md"
    click n4 "../modules/site_cmd.md"
    click n5 "../modules/export.md"
    click n6 "../modules/site_export.md"
    click n7 "../modules/site_export.md"
    click n8 "../modules/site_export.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [site_export](../modules/site_export.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `_knowledge_metadata` | call | [site_cmd](../modules/site_cmd.md) |
| `_knowledge_metadata` | call | [site_cmd](../modules/site_cmd.md) |
| `_load_hub_knowledge_projections` | call | [site_cmd](../modules/site_cmd.md) |
| `_load_knowledge_projection` | call | [site_cmd](../modules/site_cmd.md) |
| `export` | import | [export](../modules/export.md) |
| `_build_publication_selection` | call | [site_export](../modules/site_export.md) |
| `_file_digest` | call | [site_export](../modules/site_export.md) |
| `_find_unexpected_knowledge_pages` | call | [site_export](../modules/site_export.md) |
| `_find_unexpected_knowledge_pages` | call | [site_export](../modules/site_export.md) |
| `_find_unexpected_knowledge_pages` | call | [site_export](../modules/site_export.md) |
| `_find_unexpected_knowledge_pages` | call | [site_export](../modules/site_export.md) |
| `_find_unexpected_knowledge_pages` | call | [site_export](../modules/site_export.md) |
