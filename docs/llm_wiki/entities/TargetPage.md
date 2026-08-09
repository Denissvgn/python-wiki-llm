# TargetPage

**Location:** `src/llm_wiki_cli/commands/migrate_cmd.py:128`
**Kind:** Class
**Bases:** —
**Module:** [migrate_cmd](../modules/migrate_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A canonical page generated from the current source inventory.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `str` | *required* | — |
| `stem` | `str` | *required* | — |
| `rel` | `str` | *required* | — |
| `content` | `str` | *required* | — |
| `source_path` | `str \| None` | `None` | — |
| `entity_name` | `str \| None` | `None` | — |
| `line` | `int \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["TargetPage (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n1["_build_match_lookups (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n2["_build_targets (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n3["_match_existing_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n4["_merge_legacy_notes (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n5["_pending_targets (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n6["_should_archive_matched_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n7["_target_needs_apply (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n8["_unique (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/migrate_cmd.md"
    click n1 "../modules/migrate_cmd.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/migrate_cmd.md"
    click n5 "../modules/migrate_cmd.md"
    click n6 "../modules/migrate_cmd.md"
    click n7 "../modules/migrate_cmd.md"
    click n8 "../modules/migrate_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [migrate_cmd](../modules/migrate_cmd.md) | 0 | `content`, `entity_name`, `kind`, `line`, `rel`, `source_path`, `stem` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_build_match_lookups` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_targets` | call | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_targets` | call | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_targets` | call | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_targets` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_match_existing_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_merge_legacy_notes` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_pending_targets` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_should_archive_matched_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_target_needs_apply` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_unique` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
