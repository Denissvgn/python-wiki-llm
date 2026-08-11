# MigrationChunk

**Location:** `src/llm_wiki_cli/commands/migrate_cmd.py:169`
**Kind:** Class
**Bases:** —
**Module:** [migrate_cmd](../modules/migrate_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A bounded subset of currently pending migration work.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `number` | `int` | *required* | — |
| `total` | `int` | *required* | — |
| `targets` | `list[TargetPage]` | *required* | — |
| `unmatched` | `list[ExistingPage]` | *required* | — |
| `include_finalizers` | `bool` | `False` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `page_operations` | `() -> int` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MigrationChunk (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n1["_apply_chunk (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n2["_apply_plan (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n3["_build_chunks (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n4["_chunk_has_archive_work (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n5["_chunk_link_map (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n6["_print_chunk_plan (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/migrate_cmd.md"
    click n1 "../modules/migrate_cmd.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/migrate_cmd.md"
    click n5 "../modules/migrate_cmd.md"
    click n6 "../modules/migrate_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [migrate_cmd](../modules/migrate_cmd.md) | 1 | `include_finalizers`, `number`, `targets`, `total`, `unmatched` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_apply_chunk` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) | — |
| `_apply_plan` | call | [migrate_cmd](../modules/migrate_cmd.md) | 1 |
| `_build_chunks` | call | [migrate_cmd](../modules/migrate_cmd.md) | 2 |
| `_build_chunks` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) | — |
| `_chunk_has_archive_work` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) | — |
| `_chunk_link_map` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) | — |
| `_print_chunk_plan` | type_reference | [migrate_cmd](../modules/migrate_cmd.md) | — |
