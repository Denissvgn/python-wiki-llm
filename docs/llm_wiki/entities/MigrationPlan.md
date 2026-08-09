# MigrationPlan

**Location:** `src/llm_wiki_cli/commands/migrate_cmd.py:141`
**Kind:** Class
**Bases:** —
**Module:** [migrate_cmd](../modules/migrate_cmd.md)

**Decorators:** `@dataclass`

## Description

Computed migration operations, shared by apply and dry-run paths.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `archive_name` | `str` | *required* | — |
| `targets` | `list[TargetPage]` | *required* | — |
| `matches` | `dict[str, list[ExistingPage]]` | `field(default_factory=dict)` | — |
| `unmatched` | `list[ExistingPage]` | `field(default_factory=list)` | — |
| `link_map` | `dict[str, str]` | `field(default_factory=dict)` | — |
| `page_link_maps` | `dict[str, dict[str, str]]` | `field(default_factory=dict)` | — |
| `index_content` | `str` | `''` | — |
| `manifest` | `SyncManifest \| None` | `None` | — |
| `inventory` | `dict` | `field(default_factory=dict)` | — |
| `source_snapshot` | `SourceSnapshot \| None` | `None` | — |
| `module_page_map` | `dict[str, str]` | `field(default_factory=dict)` | — |
| `entity_occurrence_page_map` | `dict[tuple[str, str, int], str]` | `field(default_factory=dict)` | — |
| `inventory_result` | `InventoryResult \| None` | `None` | — |
| `regenerated_structural_page_paths` | `set[str]` | `field(default_factory=set)` | — |
| `repository_evidence` | `RepositoryEvidence \| None` | `None` | — |
| `governance_moves` | `dict[str, str]` | `field(default_factory=dict)` | — |
| `governance_enabled` | `bool` | `False` | — |
| `governance_uid_reuses` | `int` | `0` | — |
| `governance_new_allocations` | `int` | `0` | — |
| `governance_ambiguous_moves` | `int` | `0` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MigrationPlan (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n1["_apply_chunk (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n2["_apply_plan (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n3["_build_chunks (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n4["_build_migration_plan (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n5["_chunk_has_archive_work (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n6["_chunk_link_map (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n7["_finalize_migration_artifacts (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n8["_finalizers_pending (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n9["_legacy_archive_ignore_applicable (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n10["_matched_archive_count (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n11["_migration_runtime_inputs (src/llm_wiki_cli/commands/migrate_cmd.py)"]
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
| [migrate_cmd](../modules/migrate_cmd.md) | 0 | `archive_name`, `entity_occurrence_page_map`, `governance_ambiguous_moves`, `governance_enabled`, `governance_moves`, `governance_new_allocations`, `governance_uid_reuses`, `index_content`, `inventory`, `inventory_result`, `link_map`, `manifest` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_apply_chunk` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_apply_plan` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_chunks` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_migration_plan` | call | [migrate_cmd](../modules/migrate_cmd.md) |
| `_build_migration_plan` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_chunk_has_archive_work` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_chunk_link_map` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_finalize_migration_artifacts` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_finalizers_pending` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_legacy_archive_ignore_applicable` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_matched_archive_count` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
| `_migration_runtime_inputs` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) |
