# HubWikiSource

**Location:** `src/llm_wiki_cli/services/site_export.py:272`
**Kind:** Class
**Bases:** —
**Module:** [site_export](../modules/site_export.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `HubWikiSource` in `src/llm_wiki_cli/services/site_export.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `source_id` | `str` | *required* | — |
| `wiki_dir` | `Path` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HubWikiSource (src/llm_wiki_cli/services/site_export.py)"]
    n1["_build_docusaurus_hub_sidebar (src/llm_wiki_cli/services/site_export.py)"]
    n2["_build_mkdocs_hub_config (src/llm_wiki_cli/services/site_export.py)"]
    n3["_check_hub_front_matter_id_collisions (src/llm_wiki_cli/services/site_export.py)"]
    n4["_check_hub_knowledge_uid_collisions (src/llm_wiki_cli/services/site_export.py)"]
    n5["_expected_hub_markdown_paths (src/llm_wiki_cli/services/site_export.py)"]
    n6["_hub_front_matter_id_prefix (src/llm_wiki_cli/services/site_export.py)"]
    n7["_hub_source_page_data (src/llm_wiki_cli/services/site_export.py)"]
    n8["_preflight_hub_knowledge_projections (src/llm_wiki_cli/services/site_export.py)"]
    n9["_preflight_hub_root_output_collisions (src/llm_wiki_cli/services/site_export.py)"]
    n10["_resolve_hub_sources (src/llm_wiki_cli/services/site_export.py)"]
    n11["_source_identity (src/llm_wiki_cli/services/site_export.py)"]
    n1 --> n0
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
    click n0 "../modules/site_export.md"
    click n1 "../modules/site_export.md"
    click n2 "../modules/site_export.md"
    click n3 "../modules/site_export.md"
    click n4 "../modules/site_export.md"
    click n5 "../modules/site_export.md"
    click n6 "../modules/site_export.md"
    click n7 "../modules/site_export.md"
    click n8 "../modules/site_export.md"
    click n9 "../modules/site_export.md"
    click n10 "../modules/site_export.md"
    click n11 "../modules/site_export.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [site_export](../modules/site_export.md) | 0 | `source_id`, `wiki_dir` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_docusaurus_hub_sidebar` | type_reference | [site_export](../modules/site_export.md) | — |
| `_build_mkdocs_hub_config` | type_reference | [site_export](../modules/site_export.md) | — |
| `_check_hub_front_matter_id_collisions` | type_reference | [site_export](../modules/site_export.md) | — |
| `_check_hub_knowledge_uid_collisions` | type_reference | [site_export](../modules/site_export.md) | — |
| `_expected_hub_markdown_paths` | type_reference | [site_export](../modules/site_export.md) | — |
| `_hub_front_matter_id_prefix` | type_reference | [site_export](../modules/site_export.md) | — |
| `_hub_source_page_data` | type_reference | [site_export](../modules/site_export.md) | — |
| `_preflight_hub_knowledge_projections` | type_reference | [site_export](../modules/site_export.md) | — |
| `_preflight_hub_root_output_collisions` | type_reference | [site_export](../modules/site_export.md) | — |
| `_resolve_hub_sources` | call | [site_export](../modules/site_export.md) | 2 |
| `_resolve_hub_sources` | type_reference | [site_export](../modules/site_export.md) | — |
| `_source_identity` | type_reference | [site_export](../modules/site_export.md) | — |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
