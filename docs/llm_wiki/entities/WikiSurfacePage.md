# WikiSurfacePage

**Location:** `src/llm_wiki_cli/services/wiki_surface.py:82`
**Kind:** Class
**Bases:** —
**Module:** [wiki_surface](../modules/wiki_surface.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `WikiSurfacePage` in `src/llm_wiki_cli/services/wiki_surface.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `PageKind` | *required* | — |
| `page_id` | `str` | *required* | — |
| `label` | `str` | *required* | — |
| `path` | `Path` | *required* | — |
| `relative_path` | `str` | *required* | — |
| `mcp_uri` | `str` | *required* | — |
| `obsidian_mirror_dir` | `Optional[str]` | *required* | — |
| `role` | `SurfaceRole` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiSurfacePage (src/llm_wiki_cli/services/wiki_surface.py)"]
    n1["_add_imported_page_candidates (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n2["_add_missing_flow_candidates (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n3["_add_page_candidate (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n4["_add_user_profile_candidates (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n5["_is_copied_docstring_only (src/llm_wiki_cli/services/documentation_worklist.py)"]
    n6["_graph_concepts (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n7["_structural_page_paths (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n8["_expected_page_coordinates (src/llm_wiki_cli/services/knowledge_index.py)"]
    n9["_validate_surface_page (src/llm_wiki_cli/services/knowledge_index.py)"]
    n10["_validated_content (src/llm_wiki_cli/services/knowledge_index.py)"]
    n11["_validated_pages (src/llm_wiki_cli/services/knowledge_index.py)"]
    n12["_build_observation (src/llm_wiki_cli/services/knowledge_links.py)"]
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
    n12 --> n0
    click n0 "../modules/wiki_surface.md"
    click n1 "../modules/documentation_worklist.md"
    click n2 "../modules/documentation_worklist.md"
    click n3 "../modules/documentation_worklist.md"
    click n4 "../modules/documentation_worklist.md"
    click n5 "../modules/documentation_worklist.md"
    click n6 "../modules/knowledge_generation.md"
    click n7 "../modules/knowledge_generation.md"
    click n8 "../modules/knowledge_index.md"
    click n9 "../modules/knowledge_index.md"
    click n10 "../modules/knowledge_index.md"
    click n11 "../modules/knowledge_index.md"
    click n12 "../modules/knowledge_links.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [wiki_surface](../modules/wiki_surface.md) | 0 | `kind`, `label`, `mcp_uri`, `obsidian_mirror_dir`, `page_id`, `path`, `relative_path`, `role` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_add_imported_page_candidates` | type_reference | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `_add_missing_flow_candidates` | type_reference | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `_add_page_candidate` | type_reference | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `_add_user_profile_candidates` | type_reference | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `_is_copied_docstring_only` | type_reference | [documentation_worklist](../modules/documentation_worklist.md) | — |
| `_graph_concepts` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_structural_page_paths` | type_reference | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_expected_page_coordinates` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validate_surface_page` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validated_content` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_validated_pages` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `_build_observation` | type_reference | [knowledge_links](../modules/knowledge_links.md) | — |

> References: showing 12 of 26 logical references; 14 omitted by the 12-row generated summary limit.
