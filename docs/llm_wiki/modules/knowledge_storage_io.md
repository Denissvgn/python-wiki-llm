# knowledge_storage_io Module

**Path:** `src/llm_wiki_cli/services/knowledge_storage_io.py`

## Description

Reads bounded complete files or exact pack ranges through guarded regular files and retained directory identities. Requests record content and filesystem observations, charge final rereads to their budgets and reject replacement or permission/content changes. Different ranges from one pack must share the same file and ancestor identities. Platform guards prevent following redirected paths.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `WindowsDirectoryGuardError`, `WindowsFileGuardError`, `fresh_no_follow_stat`, `guard_windows_directory_chain`, `open_windows_readonly_file`, `windows_object_identity`, `_windows_path_handle_metadata` |
| `.io` | `first_unsafe_path_component` |
| `.knowledge_storage` | `KnowledgeStorageError`, `MAX_EXPANDED_BYTES` |
| `.validation` | `is_portable_relative_path` |
| `__future__` | `annotations` |
| `contextlib` | `ExitStack` |
| `dataclasses` | `dataclass` |
| `os` | `os` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/knowledge_storage_io.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (9) |
| Outbound | `src` (4) |

> All 13 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ReadObservation](../entities/ReadObservation.md) | 57 | — | — |
| [StorageReadSession](../entities/StorageReadSession.md) | 149 | — | Request-owned file observations, with charged authoritative rechecks. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_identity` | `(value: os.stat_result) -> tuple[int, ...]` | — | — |
| `_assert_windows_file_binding` | `(path: Path, named: os.stat_result, opened: os.stat_result) -> None` | — | Compare stable Windows fields across pathname and descriptor channels. |
| `_require_relative_name` | `(relative: str) -> None` | — | — |
| `_absolute_path` | `(path: Path) -> Path` | — | — |
| `read_guarded` | `(path: Path, maximum: int, *, offset: int = 0, length: int \| None = None, file_bytes: int \| None = None) -> ReadObservation` | — | Read a regular file through pinned/no-follow ancestors and bound its bytes. |