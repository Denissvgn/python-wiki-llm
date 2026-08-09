# WikiPage

**Location:** `src/llm_wiki_cli/services/obsidian.py:153`
**Kind:** Class
**Bases:** —
**Module:** [obsidian](../modules/obsidian.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `WikiPage` in `src/llm_wiki_cli/services/obsidian.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `str` | *required* | — |
| `page_id` | `str` | *required* | — |
| `title` | `str` | *required* | — |
| `canonical_path` | `Path` | *required* | — |
| `canonical_rel` | `str` | *required* | — |
| `mirror_rel` | `str` | *required* | — |
| `source_path` | `str \| None` | `None` | — |
| `source_line` | `int \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiPage (src/llm_wiki_cli/services/obsidian.py)"]
    n1["_aliases_for (src/llm_wiki_cli/services/obsidian.py)"]
    n2["_build_related_links (src/llm_wiki_cli/services/obsidian.py)"]
    n3["_collect_outgoing_links (src/llm_wiki_cli/services/obsidian.py)"]
    n4["_knowledge_frontmatter_summary (src/llm_wiki_cli/services/obsidian.py)"]
    n5["_merge_inventory_relationships (src/llm_wiki_cli/services/obsidian.py)"]
    n6["_merge_source_coordinate_relationships (src/llm_wiki_cli/services/obsidian.py)"]
    n7["_mirror_scan_relative_path (src/llm_wiki_cli/services/obsidian.py)"]
    n8["_render_projected_target (src/llm_wiki_cli/services/obsidian.py)"]
    n9["_render_related_links (src/llm_wiki_cli/services/obsidian.py)"]
    n10["_render_typed_relationships (src/llm_wiki_cli/services/obsidian.py)"]
    n11["_resolve_markdown_target (src/llm_wiki_cli/services/obsidian.py)"]
    n12["_select_knowledge_projection (src/llm_wiki_cli/services/obsidian.py)"]
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
    click n0 "../modules/obsidian.md"
    click n1 "../modules/obsidian.md"
    click n2 "../modules/obsidian.md"
    click n3 "../modules/obsidian.md"
    click n4 "../modules/obsidian.md"
    click n5 "../modules/obsidian.md"
    click n6 "../modules/obsidian.md"
    click n7 "../modules/obsidian.md"
    click n8 "../modules/obsidian.md"
    click n9 "../modules/obsidian.md"
    click n10 "../modules/obsidian.md"
    click n11 "../modules/obsidian.md"
    click n12 "../modules/obsidian.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [obsidian](../modules/obsidian.md) | 0 | `canonical_path`, `canonical_rel`, `kind`, `mirror_rel`, `page_id`, `source_line`, `source_path`, `title` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_aliases_for` | type_reference | [obsidian](../modules/obsidian.md) |
| `_build_related_links` | type_reference | [obsidian](../modules/obsidian.md) |
| `_collect_outgoing_links` | type_reference | [obsidian](../modules/obsidian.md) |
| `_knowledge_frontmatter_summary` | type_reference | [obsidian](../modules/obsidian.md) |
| `_merge_inventory_relationships` | type_reference | [obsidian](../modules/obsidian.md) |
| `_merge_source_coordinate_relationships` | type_reference | [obsidian](../modules/obsidian.md) |
| `_mirror_scan_relative_path` | type_reference | [obsidian](../modules/obsidian.md) |
| `_render_projected_target` | type_reference | [obsidian](../modules/obsidian.md) |
| `_render_related_links` | type_reference | [obsidian](../modules/obsidian.md) |
| `_render_typed_relationships` | type_reference | [obsidian](../modules/obsidian.md) |
| `_resolve_markdown_target` | type_reference | [obsidian](../modules/obsidian.md) |
| `_select_knowledge_projection` | type_reference | [obsidian](../modules/obsidian.md) |
