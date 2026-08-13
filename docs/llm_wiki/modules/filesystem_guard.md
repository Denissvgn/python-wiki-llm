# filesystem_guard Module

**Path:** `src/llm_wiki_cli/services/filesystem_guard.py`

## Description

Small cross-platform guards for security-sensitive workspace writes.

POSIX callers should prefer descriptor-relative operations.  Windows does not
expose ``openat`` through the Python standard library, so pathname writers pin
every directory in the destination chain with native handles opened without
``FILE_SHARE_DELETE``.  A pinned chain cannot be renamed or replaced by a
junction while the guarded write is in progress.  That rename guarantee
requires ordinary ``FILE_LIST_DIRECTORY`` access; if Windows denies it, the
guard fails closed instead of falling back to an attribute-only handle.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `contextlib` | `contextmanager` |
| `ctypes` | `ctypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes`, `wintypes` |
| `dataclasses` | `dataclass` |
| `hashlib` | `hashlib` |
| `msvcrt` | `msvcrt`, `msvcrt`, `msvcrt` |
| `os` | `os` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `typing` | `BinaryIO`, `Iterator`, `Sequence` |
| `uuid` | `uuid` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/filesystem_guard.py"]
    n0 --> n1
    click n1 "../modules/filesystem_guard.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (15) |

> All 15 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [WindowsDirectoryGuardError](../entities/WindowsDirectoryGuardError.md) | 44 | `OSError` | Raised when a Windows directory chain cannot be pinned safely. |
| [_WindowsDirectoryGuardUnavailableError](../entities/WindowsDirectoryGuardUnavailableError.md) | 48 | `WindowsDirectoryGuardError` | Raised when Windows denies access required to pin a directory. |
| [WindowsFileGuardError](../entities/WindowsFileGuardError.md) | 52 | `OSError` | Raised when a Windows input file cannot be opened without redirection. |
| [WindowsSecurityGuardError](../entities/WindowsSecurityGuardError.md) | 56 | `OSError` | Raised when a Windows object lacks the required restrictive DACL. |
| [WindowsDurabilityError](../entities/WindowsDurabilityError.md) | 60 | `OSError` | Raised when Windows cannot confirm durable filesystem metadata. |
| [WindowsIdentityUnavailableError](../entities/WindowsIdentityUnavailableError.md) | 64 | `OSError` | Raised when Windows cannot expose a stable filesystem object identity. |
| [WindowsObjectIdentity](../entities/WindowsObjectIdentity.md) | 69 | — | Immutable Windows device and file identifier exposed by a real stat call. |
| [_WindowsPathHandleMetadata](../entities/WindowsPathHandleMetadata.md) | 83 | — | Metadata with consistent semantics across Windows path and handle stats. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `fresh_no_follow_stat` | `(path: str \| Path) -> os.stat_result` | — | Return uncached metadata for one path without following its leaf. |
| `windows_object_identity` | `(result: os.stat_result, *, context: str) -> WindowsObjectIdentity` | — | Extract identity from ``os.stat``/``os.fstat`` Windows metadata. |
| `windows_object_identity_from_values` | `(*, device: int, file_id: int, context: str) -> WindowsObjectIdentity` | — | Build a Windows identity, failing closed when either component is absent. |
| `_windows_path_handle_metadata` | `(result: os.stat_result) -> _WindowsPathHandleMetadata` | — | Return metadata safe to compare between Windows path and handle stats. |
| `guard_windows_directory_chain` | `(root: Path, relative_components: Sequence[str], *, create_missing: bool = False, require_restrictive_dacl: bool = False) -> Iterator[Path]` | `@contextmanager` | Pin ``root`` and each child directory without delete sharing. |
| `_open_windows_directory_guard` | `(path: Path, *, require_restrictive_dacl: bool = False) -> int` | — | — |
| `open_windows_readonly_file` | `(path: Path, *, require_restrictive_dacl: bool = False, require_single_link: bool = True) -> Iterator[tuple[BinaryIO, os.stat_result]]` | `@contextmanager` | Open one regular Windows file without following a reparse point. |
| `_open_windows_readonly_file_handle` | `(path: Path, *, require_restrictive_dacl: bool = False, require_single_link: bool = True) -> int` | — | — |
| `create_private_windows_directory` | `(path: Path) -> None` | — | Create one private directory through a write-through atomic rename. |
| `open_windows_private_write_file` | `(path: Path) -> int` | — | Create one private write-through file and return an owning CRT fd. |
| `open_windows_guarded_lock_file` | `(path: Path) -> tuple[int, bool]` | — | Open/create a non-reparse lock leaf and return ``(fd, created)``. |
| `replace_windows_file_write_through` | `(source: Path, target: Path) -> None` | — | Atomically replace ``target`` and request write-through metadata. |
| `move_windows_path_write_through` | `(source: Path, target: Path, *, replace_existing: bool) -> None` | — | Move one file or directory and persist its namespace update. |
| `verify_windows_restrictive_dacl` | `(path: Path) -> None` | — | Fail closed unless ``path`` has the protected-store Windows DACL. |
| `windows_current_user_sid` | `() -> str` | — | Return the current process-token user SID as canonical text. |
| `windows_path_owner_sid` | `(path: str \| Path) -> str` | — | Return the owner SID of one Windows path without following its leaf. |
| `_windows_handle_owner_sid` | `(handle: int, *, context: str) -> str` | — | — |
| `_open_windows_file_metadata_guard` | `(path: Path) -> int` | — | — |
| `_assert_windows_regular_file_handle` | `(handle: int, path: Path) -> None` | — | — |
| `_windows_handle_information` | `(handle: int, path: Path) -> ctypes.Structure` | — | — |
| `_private_windows_security_attributes` | `(*, directory: bool) -> Iterator[ctypes.Structure]` | `@contextmanager` | — |
| `_current_windows_user_sid` | `() -> str` | — | — |
| `_windows_sid_string` | `(sid: ctypes.c_void_p) -> str` | — | — |
| `_verify_windows_handle_restrictive_dacl` | `(handle: int, *, context: str) -> None` | — | — |
| `_close_windows_handle` | `(handle: int) -> None` | — | — |
| `_windows_api_path` | `(path: Path) -> str` | — | — |
| `_read_posix_descriptor` | `(descriptor: int) -> bytes` | — | Read one already-open descriptor from its current offset. |
| `_restore_posix_quarantined_entry` | `(parent_fd: int, quarantine_name: str, target_name: str) -> bool` | — | Restore a claimed entry without replacing a concurrent target. |
| `_restore_posix_entry_between` | `(source_fd: int, quarantine_name: str, target_fd: int, target_name: str) -> bool` | — | Restore a claimed entry across pinned directories without replacement. |
| `_guarded_tree_manifest_posix_fd` | `(directory_fd: int, *, prefix: str = '') -> GuardedTreeManifest` | — | Inventory one pinned POSIX directory tree without following links. |
| `_guarded_tree_manifest_windows_path` | `(root: Path) -> GuardedTreeManifest` | — | Inventory a Windows tree while its full directory chain is pinned. |
| `_guarded_tree_entry_windows_path` | `(candidate: Path, relative: str) -> GuardedTreeManifestEntry` | — | Capture one pinned Windows entry with stable leaf identity. |
| `guarded_tree_manifest` | `(path: Path) -> GuardedTreeManifest` | — | Return a deterministic manifest from a pinned, no-follow tree root. |
| `atomic_write_private_bytes` | `(path: Path, data: bytes, *, expected_existing: bytes \| None \| object = _EXPECTED_EXISTING_UNSET) -> Path` | — | Atomically write one private file without following destination paths. |
| `atomic_write_executable_bytes` | `(path: Path, data: bytes, *, expected_existing: bytes \| None \| object = _EXPECTED_EXISTING_UNSET) -> Path` | — | Atomically write one executable file beneath a pinned directory chain. |
| `atomic_write_guarded_bytes` | `(path: Path, data: bytes, *, mode: int = 384, require_single_link: bool = True, expected_existing: bytes \| None \| object = _EXPECTED_EXISTING_UNSET) -> Path` | — | Atomically replace bytes beneath a pinned, no-follow directory chain. |
| `ensure_guarded_directory` | `(path: Path, *, mode: int = 493) -> Path` | — | Create one directory chain without following a redirected component. |
| `unlink_guarded_bytes` | `(path: Path, *, expected: bytes) -> None` | — | Unlink one exact regular file without following a rebound parent path. |
| `remove_guarded_tree` | `(path: Path, *, expected_identity: tuple[int, int] \| None = None, expected_manifest: GuardedTreeManifest \| None = None) -> None` | — | Remove one confirmed directory tree through a private quarantine. |
| `_atomic_write_private_bytes_posix` | `(target: Path, data: bytes, *, mode: int = 384, require_single_link: bool = True, expected_existing: bytes \| None \| object = _EXPECTED_EXISTING_UNSET) -> None` | — | — |
| `_commit_windows_absent_snapshot` | `(temporary: Path, target: Path) -> None` | — | Commit a staged file only while the inspected target remains absent. |
| `_atomic_write_private_bytes_windows` | `(target: Path, data: bytes, *, expected_existing: bytes \| None \| object = _EXPECTED_EXISTING_UNSET, require_single_link: bool = True) -> None` | — | — |
| `_atomic_write_guarded_bytes_windows` | `(target: Path, data: bytes, *, expected_existing: bytes \| None \| object = _EXPECTED_EXISTING_UNSET, require_single_link: bool = True) -> None` | — | Write a public Windows file with inherited ACL and snapshot binding. |
