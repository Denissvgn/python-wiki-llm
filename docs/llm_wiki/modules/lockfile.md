# lockfile Module

**Path:** `src/llm_wiki_engine/lockfile.py`

## Description

_Auto-generated from `src/llm_wiki_engine/lockfile.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `.host` | `emit` |
| `errno` | `errno` |
| `fcntl` | `fcntl`, `fcntl` |
| `math` | `math` |
| `msvcrt` | `msvcrt`, `msvcrt` |
| `os` | `os` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `time` | `time` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n1["src/llm_wiki_engine/host.py"]
    n2["src/llm_wiki_engine/lockfile.py"]
    n0 --> n2
    n2 --> n1
    click n0 "../modules/trigger_cmd.md"
    click n1 "../modules/host.md"
    click n2 "../modules/lockfile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [trigger_cmd](../modules/trigger_cmd.md) |
| Outbound | [host](../modules/host.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [LockAcquisitionError](../entities/LockAcquisitionError.md) | 24 | `Exception` | Raised when the wiki lock cannot be acquired (another sync is running). |
| [WikiLock](../entities/WikiLock.md) | 28 | — | Exclusive file lock to prevent concurrent wiki syncs. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_is_lock_contention_error` | `(exc: OSError) -> bool` | — | Return whether *exc* represents a held non-blocking file lock. |
