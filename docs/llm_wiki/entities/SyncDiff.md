# SyncDiff

**Location:** `src/llm_wiki_cli/services/sync_analysis.py:20`
**Kind:** Class
**Bases:** —
**Module:** [sync_analysis](../modules/sync_analysis.md)

**Decorators:** `@dataclass`

## Description

Categorised difference between a persisted manifest and live inventory.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `new_files` | `list[str]` | `field(default_factory=list)` | — |
| `changed_files` | `list[str]` | `field(default_factory=list)` | — |
| `metadata_only_files` | `list[str]` | `field(default_factory=list)` | — |
| `unchanged_files` | `list[str]` | `field(default_factory=list)` | — |
| `removed_files` | `list[str]` | `field(default_factory=list)` | — |
| `moved_entities` | `dict[str, tuple[str, str]]` | `field(default_factory=dict)` | — |
| `renamed_entity_pages` | `dict[tuple[str, str], tuple[str, str]]` | `field(default_factory=dict)` | — |
| `renamed_module_pages` | `dict[str, tuple[str, str]]` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `has_changes` | `() -> bool` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SyncDiff (src/llm_wiki_cli/services/sync_analysis.py)"]
    n1["_affected_source_files (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_append_log (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["_apply_diff (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n4["_apply_entity_page (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n5["_apply_module_page (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n6["_apply_refreshed_file_pages (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n7["_apply_sync_changes (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n8["_build_apply_diff_context (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n9["_compute_sync_diff (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n10["_deprecate_removed_files (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n11["_exit_if_large_unforced_diff (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n12["_generator_refresh_diff (src/llm_wiki_cli/commands/sync_cmd.py)"]
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
    click n0 "../modules/sync_analysis.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/sync_cmd.md"
    click n5 "../modules/sync_cmd.md"
    click n6 "../modules/sync_cmd.md"
    click n7 "../modules/sync_cmd.md"
    click n8 "../modules/sync_cmd.md"
    click n9 "../modules/sync_cmd.md"
    click n10 "../modules/sync_cmd.md"
    click n11 "../modules/sync_cmd.md"
    click n12 "../modules/sync_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_analysis](../modules/sync_analysis.md) | 1 | `changed_files`, `metadata_only_files`, `moved_entities`, `new_files`, `removed_files`, `renamed_entity_pages`, `renamed_module_pages`, `unchanged_files` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_affected_source_files` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_append_log` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_diff` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_entity_page` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_module_page` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_refreshed_file_pages` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_apply_sync_changes` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_build_apply_diff_context` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_compute_sync_diff` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_deprecate_removed_files` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_exit_if_large_unforced_diff` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_generator_refresh_diff` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
