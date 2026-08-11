# SourceFileIntegrity

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:114`
**Kind:** Class
**Bases:** —
**Module:** [source_snapshot](../modules/source_snapshot.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Filesystem identity used for cheap between-stage mutation checks.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `device` | `int` | *required* | — |
| `inode` | `int` | *required* | — |
| `mode_type` | `int` | *required* | — |
| `size` | `int` | *required* | — |
| `mtime_ns` | `int` | *required* | — |
| `ctime_ns` | `int` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceFileIntegrity (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1["_captured_file_integrity (src/llm_wiki_cli/services/source_snapshot.py)"]
    n2["_source_file_integrity (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/source_snapshot.md"
    click n1 "../modules/source_snapshot.md"
    click n2 "../modules/source_snapshot.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_snapshot](../modules/source_snapshot.md) | 0 | `ctime_ns`, `device`, `inode`, `mode_type`, `mtime_ns`, `size` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_captured_file_integrity` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_source_file_integrity` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |
| `_source_file_integrity` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
