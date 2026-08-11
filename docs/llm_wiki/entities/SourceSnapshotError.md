# SourceSnapshotError

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:92`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [source_snapshot](../modules/source_snapshot.md)

## Description

Field-specific failure selecting captured source snapshot state.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceSnapshotError (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/context_packet.py"]
    n3["src/llm_wiki_cli/services/documentation_native.py"]
    n4["_git_changed_files (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_git_name_status_paths (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_build_source_snapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n7["_prune_dirnames (src/llm_wiki_cli/services/source_snapshot.py)"]
    n8["_record_gitignore_rules (src/llm_wiki_cli/services/source_snapshot.py)"]
    n9["_record_source_file (src/llm_wiki_cli/services/source_snapshot.py)"]
    n10["_resolve_snapshot_selection (src/llm_wiki_cli/services/source_snapshot.py)"]
    n11["_validate_repository_path (src/llm_wiki_cli/services/source_snapshot.py)"]
    n12["build_source_snapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n13["SourceSnapshot.hashes_for (src/llm_wiki_cli/services/source_snapshot.py)"]
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
    click n0 "../modules/source_snapshot.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/documentation_native.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/source_snapshot.md"
    click n7 "../modules/source_snapshot.md"
    click n8 "../modules/source_snapshot.md"
    click n9 "../modules/source_snapshot.md"
    click n10 "../modules/source_snapshot.md"
    click n11 "../modules/source_snapshot.md"
    click n12 "../modules/source_snapshot.md"
    click n13 "../modules/source_snapshot.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_snapshot](../modules/source_snapshot.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
| `_git_changed_files` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_git_name_status_paths` | call | [extraction_service](../modules/extraction_service.md) | 3 |
| `_build_source_snapshot` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |
| `_prune_dirnames` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
| `_record_gitignore_rules` | call | [source_snapshot](../modules/source_snapshot.md) | 7 |
| `_record_source_file` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
| `_resolve_snapshot_selection` | call | [source_snapshot](../modules/source_snapshot.md) | 4 |
| `_validate_repository_path` | call | [source_snapshot](../modules/source_snapshot.md) | 3 |
| `build_source_snapshot` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |
| `SourceSnapshot.hashes_for` | call | [source_snapshot](../modules/source_snapshot.md) | 3 |

> References: showing 12 of 13 logical references; 1 omitted by the 12-row generated summary limit.
