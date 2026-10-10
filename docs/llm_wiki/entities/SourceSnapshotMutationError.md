# SourceSnapshotMutationError

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:112`
**Kind:** Class
**Bases:** `SourceSnapshotError`
**Module:** [source_snapshot](../modules/source_snapshot.md)

## Description

Reports a change between source hashing and capture. The owning context read retries within its declared policy or returns an explicit mutation failure; restored bytes cannot silently bind an observation to a different read.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceSnapshotMutationError (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1["SourceSnapshotError (src/llm_wiki_cli/services/source_snapshot.py)"]
    n2["_advance_owned_ignore_snapshot (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n3["_ensure_legacy_gitignore (src/llm_wiki_cli/commands/migrate_cmd.py)"]
    n4["src/llm_wiki_cli/services/context_packet.py"]
    n5["_implementation_observations (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_build_source_snapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n7["_missing_source_path_no_follow (src/llm_wiki_cli/services/source_snapshot.py)"]
    n8["_path_bound_file_integrity (src/llm_wiki_cli/services/source_snapshot.py)"]
    n9["_read_ignore_control (src/llm_wiki_cli/services/source_snapshot.py)"]
    n10["_sha256_file (src/llm_wiki_cli/services/source_snapshot.py)"]
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
    click n0 "../modules/source_snapshot.md"
    click n1 "../modules/source_snapshot.md"
    click n2 "../modules/migrate_cmd.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/source_snapshot.md"
    click n7 "../modules/source_snapshot.md"
    click n8 "../modules/source_snapshot.md"
    click n9 "../modules/source_snapshot.md"
    click n10 "../modules/source_snapshot.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_snapshot](../modules/source_snapshot.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `SourceSnapshotError` | [source_snapshot](../modules/source_snapshot.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_advance_owned_ignore_snapshot` | call | [migrate_cmd](../modules/migrate_cmd.md) | 3 |
| `_ensure_legacy_gitignore` | call | [migrate_cmd](../modules/migrate_cmd.md) | 4 |
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `_implementation_observations` | call | [extraction_service](../modules/extraction_service.md) | 2 |
| `_build_source_snapshot` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
| `_missing_source_path_no_follow` | call | [source_snapshot](../modules/source_snapshot.md) | 3 |
| `_path_bound_file_integrity` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
| `_read_ignore_control` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
| `_sha256_file` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
