# ExistingPage

**Location:** `src/llm_wiki_cli/commands/migrate_cmd.py:112`
**Kind:** Class
**Bases:** —
**Module:** [migrate_cmd](../modules/migrate_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A currently active wiki page before migration.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `str` | *required* | — |
| `path` | `Path` | *required* | — |
| `rel` | `str` | *required* | — |
| `stem` | `str` | *required* | — |
| `content` | `str` | *required* | — |
| `heading` | `str \| None` | `None` | — |
| `location_path` | `str \| None` | `None` | — |
| `location_line` | `int \| None` | `None` | — |
| `source_path` | `str \| None` | `None` | — |
| `archived` | `bool` | `False` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExistingPage (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n1["_active_managed_pages (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n2["_archive_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n3["_archived_managed_pages (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n4["_existing_legacy_payload (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n5["_match_existing_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n6["_merge_legacy_notes (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n7["_read_existing_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n8["_remove_old_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n9["_should_archive_matched_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n10["_staged_existing_page (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n11["_target_needs_apply (src/llm_wiki_cli/commands/migrate_cmd.py)"]
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
    click n0 "../modules/migrate_cmd.md"
    click n1 "../modules/migrate_cmd.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/migrate_cmd.md"
    click n5 "../modules/migrate_cmd.md"
    click n6 "../modules/migrate_cmd.md"
    click n7 "../modules/migrate_cmd.md"
    click n8 "../modules/migrate_cmd.md"
    click n9 "../modules/migrate_cmd.md"
    click n10 "../modules/migrate_cmd.md"
    click n11 "../modules/migrate_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [migrate_cmd](../modules/migrate_cmd.md) | 0 | `archived`, `content`, `heading`, `kind`, `location_line`, `location_path`, `path`, `rel`, `source_path`, `stem` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_active_managed_pages` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_archive_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_archived_managed_pages` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_existing_legacy_payload` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_match_existing_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_merge_legacy_notes` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_read_existing_page` | call | [migrate_cmd](../modules/migrate_cmd.md) |
| `_read_existing_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_remove_old_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_should_archive_matched_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_staged_existing_page` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_target_needs_apply` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
