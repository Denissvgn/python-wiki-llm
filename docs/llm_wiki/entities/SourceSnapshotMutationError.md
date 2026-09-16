# SourceSnapshotMutationError

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:110`
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
    n2["src/llm_wiki_cli/services/context_packet.py"]
    n3["_build_source_snapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n4["_read_ignore_control (src/llm_wiki_cli/services/source_snapshot.py)"]
    n5["_sha256_file (src/llm_wiki_cli/services/source_snapshot.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/source_snapshot.md"
    click n1 "../modules/source_snapshot.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/source_snapshot.md"
    click n4 "../modules/source_snapshot.md"
    click n5 "../modules/source_snapshot.md"
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
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `_build_source_snapshot` | call | [source_snapshot](../modules/source_snapshot.md) | 2 |
| `_read_ignore_control` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |
| `_sha256_file` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |