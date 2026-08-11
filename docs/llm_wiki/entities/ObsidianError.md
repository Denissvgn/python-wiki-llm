# ObsidianError

**Location:** `src/llm_wiki_cli/services/obsidian.py:106`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [obsidian](../modules/obsidian.md)

## Description

Raised for invalid Obsidian export/check requests.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ObsidianError (src/llm_wiki_cli/services/obsidian.py)"]
    n1["ValueError"]
    n2["_knowledge_projection (src/llm_wiki_cli/commands/obsidian_cmd.py)"]
    n3["_ensure_safe_base (src/llm_wiki_cli/services/obsidian.py)"]
    n4["_knowledge_frontmatter_summary (src/llm_wiki_cli/services/obsidian.py)"]
    n5["_merge_inventory_relationships (src/llm_wiki_cli/services/obsidian.py)"]
    n6["_mirror_scan_relative_path (src/llm_wiki_cli/services/obsidian.py)"]
    n7["_preflight_no_alias_paths (src/llm_wiki_cli/services/obsidian.py)"]
    n8["_preflight_planned_parent_directories (src/llm_wiki_cli/services/obsidian.py)"]
    n9["_read_bounded_projected_frontmatter (src/llm_wiki_cli/services/obsidian.py)"]
    n10["_render_typed_relationships (src/llm_wiki_cli/services/obsidian.py)"]
    n11["_safe_join (src/llm_wiki_cli/services/obsidian.py)"]
    n12["_select_knowledge_projection (src/llm_wiki_cli/services/obsidian.py)"]
    n13["_unexpected_projected_mirror_pages (src/llm_wiki_cli/services/obsidian.py)"]
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
    click n0 "../modules/obsidian.md"
    click n2 "../modules/obsidian_cmd.md"
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
    click n13 "../modules/obsidian.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [obsidian](../modules/obsidian.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_knowledge_projection` | call | [obsidian_cmd](../modules/obsidian_cmd.md) | 3 |
| `_ensure_safe_base` | call | [obsidian](../modules/obsidian.md) | 1 |
| `_knowledge_frontmatter_summary` | call | [obsidian](../modules/obsidian.md) | 1 |
| `_merge_inventory_relationships` | call | [obsidian](../modules/obsidian.md) | 1 |
| `_mirror_scan_relative_path` | call | [obsidian](../modules/obsidian.md) | 1 |
| `_preflight_no_alias_paths` | call | [obsidian](../modules/obsidian.md) | 1 |
| `_preflight_planned_parent_directories` | call | [obsidian](../modules/obsidian.md) | 3 |
| `_read_bounded_projected_frontmatter` | call | [obsidian](../modules/obsidian.md) | 5 |
| `_render_typed_relationships` | call | [obsidian](../modules/obsidian.md) | 1 |
| `_safe_join` | call | [obsidian](../modules/obsidian.md) | 2 |
| `_select_knowledge_projection` | call | [obsidian](../modules/obsidian.md) | 4 |
| `_unexpected_projected_mirror_pages` | call | [obsidian](../modules/obsidian.md) | 13 |

> References: showing 12 of 18 logical references; 6 omitted by the 12-row generated summary limit.
