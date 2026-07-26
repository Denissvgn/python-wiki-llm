# pyright: reportAttributeAccessIssue=false
"""Protected, bounded artifact storage for controller-owned lifecycle state.

The store deliberately has no calibration-specific schema knowledge.  It owns
only the filesystem trust boundary: a new/empty root, portable relative names,
regular files and directories, descriptor-relative POSIX operations, guarded
Windows pathname operations, atomic replacement, immutable write-once
artifacts, and a dedicated non-blocking root lock.
"""

from __future__ import annotations

import ctypes
import errno
import json
import os
import re
import stat
import sys
import unicodedata
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterator, Mapping, Sequence, cast

from .filesystem_guard import (
    WindowsDirectoryGuardError,
    WindowsDurabilityError,
    WindowsFileGuardError,
    WindowsSecurityGuardError,
    create_private_windows_directory,
    fresh_no_follow_stat,
    guard_windows_directory_chain,
    move_windows_path_write_through,
    open_windows_guarded_lock_file,
    open_windows_private_write_file,
    open_windows_readonly_file,
    replace_windows_file_write_through,
    verify_windows_restrictive_dacl,
    windows_current_user_sid,
)


DEFAULT_MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
DEFAULT_MAX_PROJECTION_BYTES = 32 * 1024 * 1024
ROOT_LOCK_FILENAME = "controller.lock"

_LOCK_SIZE = 1
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
    | {f"com{number}" for number in ("¹", "²", "³")}
    | {f"lpt{number}" for number in ("¹", "²", "³")}
)
_WINDOWS_FORBIDDEN_PATH_CHARS = frozenset('<>:"|?*')
_TEMP_SUFFIX = ".protected-tmp"
_DARWIN_ACL_TYPE_EXTENDED = 0x00000100
_DESCRIPTOR_RELATIVE_IO_AVAILABLE = (
    os.name != "nt"
    and hasattr(os, "O_DIRECTORY")
    and hasattr(os, "O_NOFOLLOW")
    and os.open in os.supports_dir_fd
    and os.stat in os.supports_dir_fd
    and os.stat in os.supports_follow_symlinks
    and os.rename in os.supports_dir_fd
    and os.link in os.supports_dir_fd
    and os.unlink in os.supports_dir_fd
)


class ProtectedArtifactError(RuntimeError):
    """Base error for protected artifact storage."""


class ProtectedArtifactIntegrityError(ProtectedArtifactError):
    """Raised when artifact filesystem or canonical-byte invariants fail."""


class ProtectedArtifactLimitError(ProtectedArtifactError):
    """Raised when an artifact exceeds its configured byte limit."""


class ProtectedArtifactLockError(ProtectedArtifactError):
    """Raised when the controller root lock cannot be acquired."""


class ProtectedArtifactDurabilityError(ProtectedArtifactError):
    """Raised when committed filesystem metadata cannot be made durable."""


def validate_portable_relative_path(relative: str | Path) -> str:
    """Return one normalized portable path or reject it.

    Artifact paths use ``/`` as their canonical separator.  Backslashes are
    accepted as input for callers running on Windows, then normalized.
    Components must already be NFC-normalized so two supported filesystems
    cannot silently assign different names to the same artifact.
    """

    raw = os.fspath(relative)
    if not isinstance(raw, str):
        raise ProtectedArtifactIntegrityError("Artifact paths must be text.")
    normalized = raw.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized in {".", ".."}
        or normalized != normalized.strip()
        or path.is_absolute()
        or _WINDOWS_ABSOLUTE_RE.match(raw)
        or "." in path.parts
        or ".." in path.parts
        or path.as_posix() != normalized
    ):
        raise ProtectedArtifactIntegrityError(
            f"Artifact path must be a non-empty portable relative path: {raw!r}"
        )
    for component in path.parts:
        _validate_portable_component(component, context=normalized)
    return path.as_posix()


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize a JSON object to deterministic UTF-8 bytes."""

    if not isinstance(payload, Mapping):
        raise ProtectedArtifactIntegrityError(
            "Protected JSON artifacts must contain an object."
        )
    try:
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ProtectedArtifactIntegrityError(
            f"Protected artifact is not canonical JSON: {exc}"
        ) from exc
    return (serialized + "\n").encode("utf-8")


class ProtectedArtifactStore:
    """A reusable protected filesystem boundary rooted at one directory."""

    def __init__(self, root: str | Path, *, create: bool = False) -> None:
        requested = Path(os.path.abspath(os.fspath(Path(root).expanduser())))
        if create:
            _create_or_require_empty_root(requested)
        else:
            _assert_regular_directory(requested, context="protected artifact root")
        try:
            resolved = requested.resolve(strict=True)
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot resolve protected artifact root {requested}: {exc}"
            ) from exc
        _assert_regular_directory(resolved, context="protected artifact root")
        self._root = resolved
        self._root_identity = _directory_identity(resolved)
        self.verify_host_protection()

    @property
    def root(self) -> Path:
        """Return the resolved protected root."""

        return self._root

    def verify_host_protection(self) -> None:
        """Fail closed unless the complete store has supported host protection."""

        self._assert_root_current()
        if _supports_descriptor_relative_io():
            _assert_tree_safe(self._root)
        elif _uses_windows_guarded_io():
            self._verify_windows_tree()
        else:  # pragma: no cover - supported platforms select one safe branch
            raise ProtectedArtifactIntegrityError(
                "Platform cannot verify protected artifact host permissions."
            )
        self._assert_root_current()

    def verify_access_protection(self) -> dict[str, str]:
        """Verify protection and return host-derived admission evidence."""

        self.verify_host_protection()
        if _supports_descriptor_relative_io():
            if sys.platform == "darwin":
                return {
                    "mechanism": "darwin-owner-only-no-extended-acl",
                    "principal": f"uid:{_current_posix_uid()}",
                    "directory_mode": "0700",
                    "file_mode": "0600",
                    "extended_acl": "absent",
                }
            return {
                "mechanism": "posix-owner-only",
                "principal": f"uid:{_current_posix_uid()}",
                "directory_mode": "0700",
                "file_mode": "0600",
            }
        if _uses_windows_guarded_io():
            try:
                principal = windows_current_user_sid()
            except WindowsSecurityGuardError as exc:
                raise ProtectedArtifactIntegrityError(
                    f"Cannot derive protected Windows principal: {exc}"
                ) from exc
            return {
                "mechanism": "windows-protected-dacl",
                "principal": f"sid:{principal}",
                "allowed_system_principals": "S-1-5-18,S-1-5-32-544",
            }
        raise ProtectedArtifactIntegrityError(
            "Platform cannot report protected artifact access protection."
        )

    @contextmanager
    def lock(self) -> Iterator[None]:
        """Acquire the dedicated controller lock without waiting."""

        self._assert_root_current()
        if _supports_descriptor_relative_io():
            descriptor = self._open_posix_lock()
            windows_lock = False
        elif _uses_windows_guarded_io():
            descriptor = self._open_windows_lock()
            windows_lock = True
        else:  # pragma: no cover - supported platforms select one safe branch
            raise ProtectedArtifactIntegrityError(
                "Platform lacks protected descriptor-relative or guarded I/O."
            )

        locked = False
        try:
            try:
                if windows_lock:
                    import msvcrt

                    os.lseek(descriptor, 0, os.SEEK_SET)
                    locking = getattr(msvcrt, "locking")
                    locking(
                        descriptor,
                        int(getattr(msvcrt, "LK_NBLCK")),
                        _LOCK_SIZE,
                    )
                else:
                    import fcntl

                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except (BlockingIOError, OSError) as exc:
                raise ProtectedArtifactLockError(
                    "Another protected controller already holds controller.lock."
                ) from exc

            diagnostic = f"{os.getpid()}\n".encode("ascii")
            os.ftruncate(descriptor, 0)
            os.lseek(descriptor, 0, os.SEEK_SET)
            _write_all(descriptor, diagnostic)
            os.fsync(descriptor)
            yield
        finally:
            if locked:
                if windows_lock:
                    import msvcrt

                    try:
                        os.lseek(descriptor, 0, os.SEEK_SET)
                        locking = getattr(msvcrt, "locking")
                        locking(
                            descriptor,
                            int(getattr(msvcrt, "LK_UNLCK")),
                            _LOCK_SIZE,
                        )
                    except OSError:
                        pass
                else:
                    import fcntl

                    try:
                        fcntl.flock(descriptor, fcntl.LOCK_UN)
                    except OSError:
                        pass
            os.close(descriptor)
            self._assert_root_current()

    def exists(self, relative: str | Path) -> bool:
        """Return whether a regular protected artifact exists."""

        portable = validate_portable_relative_path(relative)
        try:
            self._read_bytes(portable, maximum_bytes=0, existence_only=True)
        except FileNotFoundError:
            return False
        return True

    def read_json(
        self,
        relative: str | Path,
        *,
        max_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    ) -> dict[str, Any]:
        """Read one bounded canonical JSON object."""

        maximum = _validate_maximum_bytes(max_bytes)
        portable = validate_portable_relative_path(relative)
        data = self._read_bytes(portable, maximum_bytes=maximum)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Protected JSON artifact {portable!r} is not UTF-8."
            ) from exc
        try:
            payload = json.loads(
                text,
                object_pairs_hook=_unique_json_object,
                parse_constant=_reject_json_constant,
            )
        except (json.JSONDecodeError, ProtectedArtifactIntegrityError) as exc:
            raise ProtectedArtifactIntegrityError(
                f"Protected JSON artifact {portable!r} is malformed: {exc}"
            ) from exc
        if not isinstance(payload, dict):
            raise ProtectedArtifactIntegrityError(
                f"Protected JSON artifact {portable!r} must contain an object."
            )
        if canonical_json_bytes(payload) != data:
            raise ProtectedArtifactIntegrityError(
                f"Protected JSON artifact {portable!r} is not canonical."
            )
        return payload

    def read_text(
        self,
        relative: str | Path,
        *,
        max_bytes: int = DEFAULT_MAX_PROJECTION_BYTES,
    ) -> str:
        """Read one bounded UTF-8 text artifact."""

        maximum = _validate_maximum_bytes(max_bytes)
        portable = validate_portable_relative_path(relative)
        data = self._read_bytes(portable, maximum_bytes=maximum)
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Protected text artifact {portable!r} is not UTF-8."
            ) from exc

    def write_immutable_json(
        self,
        relative: str | Path,
        payload: Mapping[str, Any],
        *,
        max_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    ) -> Path:
        """Atomically create one immutable JSON artifact.

        Replaying byte-identical canonical JSON is an idempotent no-op.
        Reusing the path for different bytes is an integrity failure.
        """

        maximum = _validate_maximum_bytes(max_bytes)
        portable = validate_portable_relative_path(relative)
        data = canonical_json_bytes(payload)
        _assert_within_limit(portable, data, maximum)
        self._write_bytes(portable, data, immutable=True)
        return self._root / PurePosixPath(portable)

    def write_snapshot_json(
        self,
        relative: str | Path,
        payload: Mapping[str, Any],
        *,
        max_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    ) -> Path:
        """Atomically replace one mutable canonical JSON snapshot."""

        maximum = _validate_maximum_bytes(max_bytes)
        portable = validate_portable_relative_path(relative)
        data = canonical_json_bytes(payload)
        _assert_within_limit(portable, data, maximum)
        self._write_bytes(portable, data, immutable=False)
        return self._root / PurePosixPath(portable)

    def write_projection_text(
        self,
        relative: str | Path,
        text: str,
        *,
        max_bytes: int = DEFAULT_MAX_PROJECTION_BYTES,
    ) -> Path:
        """Atomically replace one bounded UTF-8 text projection."""

        if not isinstance(text, str):
            raise ProtectedArtifactIntegrityError(
                "Protected text projection must be text."
            )
        maximum = _validate_maximum_bytes(max_bytes)
        portable = validate_portable_relative_path(relative)
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        data = normalized.encode("utf-8")
        _assert_within_limit(portable, data, maximum)
        self._write_bytes(portable, data, immutable=False)
        return self._root / PurePosixPath(portable)

    def _assert_root_current(self) -> None:
        try:
            current = _directory_identity(self._root)
        except ProtectedArtifactIntegrityError:
            raise
        if current != self._root_identity:
            raise ProtectedArtifactIntegrityError(
                "Protected artifact root changed identity."
            )

    def _verify_windows_tree(self) -> None:
        pending: list[tuple[str, ...]] = [()]
        try:
            while pending:
                components = pending.pop()
                with guard_windows_directory_chain(
                    self._root,
                    components,
                    require_restrictive_dacl=True,
                ) as directory:
                    entries = list(os.scandir(directory))
                    _assert_portable_entry_names(entry.name for entry in entries)
                    for entry in entries:
                        payload = fresh_no_follow_stat(entry.path)
                        if stat.S_ISDIR(payload.st_mode):
                            _assert_regular_directory_stat(
                                payload,
                                context=f"protected directory {entry.name!r}",
                            )
                            pending.append((*components, entry.name))
                            continue
                        _assert_regular_file_stat(
                            payload,
                            context=f"protected artifact {entry.name!r}",
                        )
                        if not components and entry.name == ROOT_LOCK_FILENAME:
                            verify_windows_restrictive_dacl(Path(entry.path))
                            continue
                        with open_windows_readonly_file(
                            Path(entry.path),
                            require_restrictive_dacl=True,
                        ) as (_stream, opened):
                            _assert_regular_file_stat(
                                opened,
                                context=f"protected artifact {entry.name!r}",
                            )
                            if _file_identity(opened) != _file_identity(payload):
                                raise ProtectedArtifactIntegrityError(
                                    "Protected artifact changed during Windows host "
                                    f"protection verification: {entry.path}"
                                )
        except ProtectedArtifactError:
            raise
        except (
            OSError,
            WindowsDirectoryGuardError,
            WindowsFileGuardError,
            WindowsSecurityGuardError,
        ) as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot verify protected Windows artifact tree: {exc}"
            ) from exc

    def _read_bytes(
        self,
        portable: str,
        *,
        maximum_bytes: int,
        existence_only: bool = False,
    ) -> bytes:
        self._assert_root_current()
        parts = PurePosixPath(portable).parts
        try:
            if _supports_descriptor_relative_io():
                data = self._read_posix(parts, maximum_bytes, existence_only)
            elif _uses_windows_guarded_io():
                data = self._read_windows(parts, maximum_bytes, existence_only)
            else:  # pragma: no cover - supported platforms select one safe branch
                raise ProtectedArtifactIntegrityError(
                    "Platform lacks protected descriptor-relative or guarded I/O."
                )
        except (FileNotFoundError, ProtectedArtifactError):
            raise
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot safely read protected artifact {portable!r}: {exc}"
            ) from exc
        self._assert_root_current()
        return data

    def _write_bytes(self, portable: str, data: bytes, *, immutable: bool) -> None:
        self._assert_root_current()
        parts = PurePosixPath(portable).parts
        try:
            if _supports_descriptor_relative_io():
                self._write_posix(parts, data, immutable=immutable)
            elif _uses_windows_guarded_io():
                self._write_windows(parts, data, immutable=immutable)
            else:  # pragma: no cover - supported platforms select one safe branch
                raise ProtectedArtifactIntegrityError(
                    "Platform lacks protected descriptor-relative or guarded I/O."
                )
        except ProtectedArtifactError:
            raise
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot safely write protected artifact {portable!r}: {exc}"
            ) from exc
        self._assert_root_current()

    def _read_posix(
        self,
        parts: Sequence[str],
        maximum_bytes: int,
        existence_only: bool,
    ) -> bytes:
        with self._open_posix_parent(parts, create=False) as (parent_fd, name):
            _assert_no_portable_collision_fd(parent_fd, name)
            flags = (
                os.O_RDONLY
                | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | os.O_NOFOLLOW
            )
            descriptor = os.open(name, flags, dir_fd=parent_fd)
            try:
                before = os.fstat(descriptor)
                _assert_regular_file_stat(before, context=parts[-1])
                _assert_darwin_no_extended_acl_fd(
                    descriptor,
                    context=f"protected artifact {'/'.join(parts)!r}",
                )
                if existence_only:
                    return b""
                data = _read_bounded_fd(
                    descriptor,
                    maximum_bytes=maximum_bytes,
                    label="/".join(parts),
                )
                after = os.fstat(descriptor)
                if _file_identity(before) != _file_identity(after):
                    raise ProtectedArtifactIntegrityError(
                        f"Protected artifact {'/'.join(parts)!r} changed while read."
                    )
                current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                _assert_regular_file_stat(current, context=parts[-1])
                if _file_identity(current) != _file_identity(after):
                    raise ProtectedArtifactIntegrityError(
                        f"Protected artifact {'/'.join(parts)!r} was replaced while read."
                    )
                return data
            finally:
                os.close(descriptor)

    def _read_windows(
        self,
        parts: Sequence[str],
        maximum_bytes: int,
        existence_only: bool,
    ) -> bytes:
        parent = self._existing_windows_parent(parts[:-1])
        target = parent / parts[-1]
        try:
            with guard_windows_directory_chain(
                self._root,
                parts[:-1],
                require_restrictive_dacl=True,
            ):
                _assert_path_entry_portable(parent, parts[-1])
                if not os.path.lexists(target):
                    raise FileNotFoundError(target)
                with open_windows_readonly_file(
                    target,
                    require_restrictive_dacl=True,
                ) as (stream, before):
                    _assert_regular_file_stat(before, context=parts[-1])
                    if existence_only:
                        return b""
                    if before.st_size > maximum_bytes:
                        raise ProtectedArtifactLimitError(
                            f"Protected artifact {'/'.join(parts)!r} exceeds the "
                            f"{maximum_bytes}-byte limit."
                        )
                    data = stream.read(maximum_bytes + 1)
                    if len(data) > maximum_bytes:
                        raise ProtectedArtifactLimitError(
                            f"Protected artifact {'/'.join(parts)!r} exceeds the "
                            f"{maximum_bytes}-byte limit."
                        )
                    after = os.fstat(stream.fileno())
                    if _file_identity(before) != _file_identity(after):
                        raise ProtectedArtifactIntegrityError(
                            f"Protected artifact {'/'.join(parts)!r} changed while read."
                        )
                    return data
        except FileNotFoundError:
            raise
        except (
            WindowsDirectoryGuardError,
            WindowsFileGuardError,
            WindowsSecurityGuardError,
        ) as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot safely read protected artifact {'/'.join(parts)!r}: {exc}"
            ) from exc

    def _write_posix(
        self, parts: Sequence[str], data: bytes, *, immutable: bool
    ) -> None:
        with self._open_posix_parent(parts, create=True) as (parent_fd, name):
            _assert_no_portable_collision_fd(parent_fd, name)
            existing = _read_existing_from_fd(parent_fd, name, len(data))
            if immutable and existing is not None:
                if existing == data:
                    return
                raise ProtectedArtifactIntegrityError(
                    f"Immutable protected artifact {'/'.join(parts)!r} already "
                    "exists with different bytes."
                )
            if not immutable:
                _assert_relative_target_regular(parent_fd, name)

            temp_name = f".{name}.{uuid.uuid4().hex}{_TEMP_SUFFIX}"
            temp_identity: tuple[int, int, int, int] | None = None
            temp_exists = False
            try:
                flags = (
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | os.O_NOFOLLOW
                    | getattr(os, "O_BINARY", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                )
                descriptor = os.open(temp_name, flags, 0o600, dir_fd=parent_fd)
                temp_exists = True
                try:
                    temp_stat = os.fstat(descriptor)
                    _assert_regular_file_stat(temp_stat, context=temp_name)
                    _assert_darwin_no_extended_acl_fd(
                        descriptor,
                        context=f"temporary protected artifact {temp_name!r}",
                    )
                    _write_all(descriptor, data)
                    os.fsync(descriptor)
                    temp_identity = _file_identity(os.fstat(descriptor))
                finally:
                    os.close(descriptor)

                if immutable:
                    created_target = False
                    try:
                        os.link(
                            temp_name,
                            name,
                            src_dir_fd=parent_fd,
                            dst_dir_fd=parent_fd,
                            follow_symlinks=False,
                        )
                        created_target = True
                    except FileExistsError:
                        existing = _read_existing_from_fd(parent_fd, name, len(data))
                        if existing != data:
                            raise ProtectedArtifactIntegrityError(
                                "Immutable protected artifact "
                                f"{'/'.join(parts)!r} raced with different bytes."
                            )
                    _unlink_owned_temp(parent_fd, temp_name, temp_identity)
                    temp_exists = False
                    if created_target:
                        committed = os.stat(
                            name, dir_fd=parent_fd, follow_symlinks=False
                        )
                        _assert_regular_file_stat(committed, context=name)
                        if _file_identity(committed) != temp_identity:
                            raise ProtectedArtifactIntegrityError(
                                f"Immutable protected artifact {'/'.join(parts)!r} "
                                "changed during commit."
                            )
                else:
                    _assert_relative_target_regular(parent_fd, name)
                    os.rename(
                        temp_name,
                        name,
                        src_dir_fd=parent_fd,
                        dst_dir_fd=parent_fd,
                    )
                    temp_exists = False
                    replaced = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                    _assert_regular_file_stat(replaced, context=name)
                    if _file_identity(replaced) != temp_identity:
                        raise ProtectedArtifactIntegrityError(
                            f"Protected artifact {'/'.join(parts)!r} changed during "
                            "atomic replacement."
                        )
                _fsync_directory(parent_fd)
            except ProtectedArtifactError:
                raise
            except OSError as exc:
                raise ProtectedArtifactIntegrityError(
                    f"Cannot write protected artifact {'/'.join(parts)!r}: {exc}"
                ) from exc
            finally:
                if temp_exists and temp_identity is not None:
                    _unlink_owned_temp(parent_fd, temp_name, temp_identity)

    def _write_windows(
        self, parts: Sequence[str], data: bytes, *, immutable: bool
    ) -> None:
        try:
            with guard_windows_directory_chain(
                self._root,
                parts[:-1],
                create_missing=True,
                require_restrictive_dacl=True,
            ) as parent:
                _assert_directory_entries_portable(parent)
                name = parts[-1]
                _assert_path_entry_portable(parent, name)
                target = parent / name
                existing = _read_existing_windows(target, len(data))
                if immutable and existing is not None:
                    if existing == data:
                        return
                    raise ProtectedArtifactIntegrityError(
                        "Immutable protected artifact "
                        f"{'/'.join(parts)!r} already exists with different bytes."
                    )
                if not immutable:
                    _assert_path_target_regular(target)

                temp = parent / f".{name}.{uuid.uuid4().hex}{_TEMP_SUFFIX}"
                temp_identity: tuple[int, int, int, int] | None = None
                temp_exists = False
                try:
                    descriptor = open_windows_private_write_file(temp)
                    temp_exists = True
                    try:
                        temp_stat = os.fstat(descriptor)
                        _assert_regular_file_stat(temp_stat, context=temp.name)
                        _write_all(descriptor, data)
                        os.fsync(descriptor)
                        temp_identity = _file_identity(os.fstat(descriptor))
                    finally:
                        os.close(descriptor)

                    if immutable:
                        created_target = False
                        try:
                            move_windows_path_write_through(
                                temp,
                                target,
                                replace_existing=False,
                            )
                            created_target = True
                            temp_exists = False
                        except FileExistsError:
                            existing = _read_existing_windows(target, len(data))
                            if existing != data:
                                raise ProtectedArtifactIntegrityError(
                                    "Immutable protected artifact "
                                    f"{'/'.join(parts)!r} raced with different bytes."
                                )
                            _unlink_owned_temp_path(temp, temp_identity)
                            temp_exists = False
                        if created_target:
                            with open_windows_readonly_file(
                                target,
                                require_restrictive_dacl=True,
                            ) as (_stream, committed):
                                _assert_regular_file_stat(committed, context=name)
                                if _file_identity(committed) != temp_identity:
                                    raise ProtectedArtifactIntegrityError(
                                        "Immutable protected artifact "
                                        f"{'/'.join(parts)!r} changed during commit."
                                    )
                    else:
                        _assert_path_target_regular(target)
                        replace_windows_file_write_through(temp, target)
                        temp_exists = False
                        with open_windows_readonly_file(
                            target,
                            require_restrictive_dacl=True,
                        ) as (_stream, replaced):
                            _assert_regular_file_stat(replaced, context=name)
                            if _file_identity(replaced) != temp_identity:
                                raise ProtectedArtifactIntegrityError(
                                    "Protected artifact "
                                    f"{'/'.join(parts)!r} changed during replacement."
                                )
                finally:
                    if temp_exists and temp_identity is not None:
                        _unlink_owned_temp_path(temp, temp_identity)
        except ProtectedArtifactError:
            raise
        except (WindowsDirectoryGuardError, WindowsSecurityGuardError) as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot pin protected Windows write path: {exc}"
            ) from exc
        except WindowsDurabilityError as exc:
            raise ProtectedArtifactDurabilityError(
                f"Cannot confirm durable Windows artifact metadata: {exc}"
            ) from exc
        except WindowsFileGuardError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot safely create or inspect protected Windows file: {exc}"
            ) from exc
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot write protected artifact {'/'.join(parts)!r}: {exc}"
            ) from exc

    @contextmanager
    def _open_posix_parent(
        self,
        parts: Sequence[str],
        *,
        create: bool,
    ) -> Iterator[tuple[int, str]]:
        flags = (
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            descriptor = os.open(self._root, flags)
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot safely open protected artifact root: {exc}"
            ) from exc
        try:
            opened_root = os.fstat(descriptor)
            _assert_regular_directory_stat(
                opened_root, context="protected artifact root"
            )
            _assert_darwin_no_extended_acl_fd(
                descriptor,
                context="protected artifact root",
            )
            if _directory_stat_identity(opened_root) != self._root_identity:
                raise ProtectedArtifactIntegrityError(
                    "Protected artifact root changed while opened."
                )
            for component in parts[:-1]:
                _assert_directory_fd_entries_portable(descriptor)
                _assert_no_portable_collision_fd(descriptor, component)
                try:
                    child = os.open(component, flags, dir_fd=descriptor)
                except FileNotFoundError:
                    if not create:
                        raise
                    os.mkdir(component, 0o700, dir_fd=descriptor)
                    _fsync_directory(descriptor)
                    child = os.open(component, flags, dir_fd=descriptor)
                child_stat = os.fstat(child)
                _assert_regular_directory_stat(
                    child_stat, context=f"artifact directory {component!r}"
                )
                _assert_darwin_no_extended_acl_fd(
                    child,
                    context=f"artifact directory {component!r}",
                )
                os.close(descriptor)
                descriptor = child
            _assert_directory_fd_entries_portable(descriptor)
            yield descriptor, parts[-1]
        finally:
            os.close(descriptor)

    def _existing_windows_parent(self, components: Sequence[str]) -> Path:
        current = self._root
        for component in components:
            _assert_directory_entries_portable(current)
            _assert_path_entry_portable(current, component)
            current /= component
            if not os.path.lexists(current):
                raise FileNotFoundError(current)
            _assert_regular_directory(
                current, context=f"artifact directory {component}"
            )
        return current

    def _open_posix_lock(self) -> int:
        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        with self._open_posix_parent((ROOT_LOCK_FILENAME,), create=False) as (
            parent_fd,
            name,
        ):
            _assert_no_portable_collision_fd(parent_fd, name)
            _assert_relative_target_regular(parent_fd, name)
            try:
                descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
            except OSError as exc:
                raise ProtectedArtifactIntegrityError(
                    f"Cannot safely open {ROOT_LOCK_FILENAME}: {exc}"
                ) from exc
            try:
                _assert_regular_file_stat(
                    os.fstat(descriptor), context=ROOT_LOCK_FILENAME
                )
                _assert_darwin_no_extended_acl_fd(
                    descriptor,
                    context=ROOT_LOCK_FILENAME,
                )
                _fsync_directory(parent_fd)
            except Exception:
                os.close(descriptor)
                raise
            return descriptor

    def _open_windows_lock(self) -> int:
        target = self._root / ROOT_LOCK_FILENAME
        try:
            with guard_windows_directory_chain(
                self._root,
                (),
                require_restrictive_dacl=True,
            ):
                _assert_directory_entries_portable(self._root)
                _assert_path_entry_portable(self._root, ROOT_LOCK_FILENAME)
                descriptor, _created = open_windows_guarded_lock_file(target)
                try:
                    lock_stat = os.fstat(descriptor)
                    _assert_regular_file_stat(lock_stat, context=ROOT_LOCK_FILENAME)
                    if lock_stat.st_size == 0:
                        _write_all(descriptor, b"\0")
                        os.fsync(descriptor)
                    os.lseek(descriptor, 0, os.SEEK_SET)
                except Exception:
                    os.close(descriptor)
                    raise
                return descriptor
        except (
            WindowsDirectoryGuardError,
            WindowsFileGuardError,
            WindowsSecurityGuardError,
        ) as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot pin protected root lock path: {exc}"
            ) from exc
        except WindowsDurabilityError as exc:
            raise ProtectedArtifactDurabilityError(
                f"Cannot confirm durable protected root lock metadata: {exc}"
            ) from exc


def _create_or_require_empty_root(root: Path) -> None:
    if os.path.lexists(root):
        _assert_regular_directory(root, context="new protected artifact root")
        before = _directory_identity(root)
        try:
            entries = list(os.scandir(root))
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot inspect new protected artifact root {root}: {exc}"
            ) from exc
        if entries:
            raise ProtectedArtifactIntegrityError(
                "A new protected artifact root must be empty; found "
                f"{sorted(entry.name for entry in entries)[0]!r}."
            )
        if _directory_identity(root) != before:
            raise ProtectedArtifactIntegrityError(
                "New protected artifact root changed while emptiness was verified."
            )
        return

    parent = root.parent
    _assert_regular_directory(
        parent,
        context="protected artifact root parent",
        require_owner_only=False,
    )
    if _supports_descriptor_relative_io():
        flags = (
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        )
        parent_fd = os.open(parent, flags)
        try:
            before = os.fstat(parent_fd)
            _assert_regular_directory_stat(
                before,
                context="artifact root parent",
                require_owner_only=False,
            )
            _assert_no_portable_collision_fd(parent_fd, root.name)
            os.mkdir(root.name, 0o700, dir_fd=parent_fd)
            _fsync_directory(parent_fd)
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot create protected artifact root {root}: {exc}"
            ) from exc
        finally:
            os.close(parent_fd)
    elif _uses_windows_guarded_io():
        try:
            with guard_windows_directory_chain(parent, ()):
                _assert_directory_entries_portable(parent)
                _assert_path_entry_portable(parent, root.name)
                create_private_windows_directory(root)
        except WindowsDurabilityError as exc:
            raise ProtectedArtifactDurabilityError(
                f"Cannot confirm durable protected root metadata: {exc}"
            ) from exc
        except (
            OSError,
            WindowsDirectoryGuardError,
            WindowsSecurityGuardError,
        ) as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot create protected artifact root {root}: {exc}"
            ) from exc
    else:  # pragma: no cover - supported platforms select one safe branch
        raise ProtectedArtifactIntegrityError(
            "Platform cannot safely create a protected artifact root."
        )
    _assert_regular_directory(root, context="new protected artifact root")


def _supports_descriptor_relative_io() -> bool:
    return _DESCRIPTOR_RELATIVE_IO_AVAILABLE


def _uses_windows_guarded_io() -> bool:
    return os.name == "nt"


def _assert_tree_safe(root: Path) -> None:
    stack = [root]
    while stack:
        directory = stack.pop()
        _assert_regular_directory(directory, context="protected artifact directory")
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot inspect protected artifact directory {directory}: {exc}"
            ) from exc
        _assert_portable_entry_names(entry.name for entry in entries)
        for entry in entries:
            try:
                payload = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ProtectedArtifactIntegrityError(
                    f"Cannot inspect protected artifact entry {entry.path}: {exc}"
                ) from exc
            if stat.S_ISDIR(payload.st_mode):
                _assert_regular_directory_stat(
                    payload, context=f"protected directory {entry.name!r}"
                )
                stack.append(Path(entry.path))
            else:
                _assert_regular_file_stat(
                    payload, context=f"protected artifact {entry.name!r}"
                )
                _assert_darwin_no_extended_acl_path(
                    Path(entry.path),
                    context=f"protected artifact {entry.name!r}",
                    expected=payload,
                )


def _assert_regular_directory(
    path: Path,
    *,
    context: str,
    require_owner_only: bool = True,
) -> None:
    if not os.path.lexists(path):
        raise ProtectedArtifactIntegrityError(f"{context} does not exist: {path}")
    try:
        payload = path.lstat()
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect {context} {path}: {exc}"
        ) from exc
    _assert_regular_directory_stat(
        payload,
        context=f"{context} {path}",
        require_owner_only=require_owner_only,
    )
    if require_owner_only:
        _assert_darwin_no_extended_acl_path(
            path,
            context=f"{context} {path}",
            directory=True,
            expected=payload,
        )


def _assert_regular_directory_stat(
    payload: os.stat_result,
    *,
    context: str,
    require_owner_only: bool = True,
) -> None:
    if (
        not stat.S_ISDIR(payload.st_mode)
        or stat.S_ISLNK(payload.st_mode)
        or _is_reparse_point(payload)
    ):
        raise ProtectedArtifactIntegrityError(
            f"{context} must be a regular directory, not a link or reparse point."
        )
    if require_owner_only:
        _assert_posix_owner_only(
            payload,
            expected_mode=0o700,
            context=context,
        )


def _assert_regular_file_stat(payload: os.stat_result, *, context: str) -> None:
    _assert_regular_file_kind_stat(payload, context=context)
    if int(getattr(payload, "st_nlink", 1)) != 1:
        raise ProtectedArtifactIntegrityError(
            f"{context} must not have additional hard links."
        )


def _assert_regular_file_kind_stat(
    payload: os.stat_result,
    *,
    context: str,
) -> None:
    if (
        not stat.S_ISREG(payload.st_mode)
        or stat.S_ISLNK(payload.st_mode)
        or _is_reparse_point(payload)
    ):
        raise ProtectedArtifactIntegrityError(
            f"{context} must be a regular file, not a link or reparse point."
        )
    _assert_posix_owner_only(
        payload,
        expected_mode=0o600,
        context=context,
    )


def _assert_posix_owner_only(
    payload: os.stat_result,
    *,
    expected_mode: int,
    context: str,
) -> None:
    if os.name == "nt":
        return
    actual_owner = int(payload.st_uid)
    expected_owner = _current_posix_uid()
    if actual_owner != expected_owner:
        raise ProtectedArtifactIntegrityError(
            f"{context} must be owned by uid {expected_owner}, not uid {actual_owner}."
        )
    actual_mode = stat.S_IMODE(payload.st_mode)
    if actual_mode != expected_mode:
        raise ProtectedArtifactIntegrityError(
            f"{context} must use owner-only mode {expected_mode:04o}, "
            f"not {actual_mode:04o}."
        )


def _current_posix_uid() -> int:
    getter = getattr(os, "geteuid", None)
    if not callable(getter):
        raise ProtectedArtifactIntegrityError(
            "Platform cannot identify the protected artifact owner."
        )
    typed_getter = cast(Callable[[], int], getter)
    return int(typed_getter())


def _assert_darwin_no_extended_acl_path(
    path: Path,
    *,
    context: str,
    directory: bool = False,
    expected: os.stat_result | None = None,
) -> None:
    """Reject a macOS filesystem object with any extended ACL entries."""

    if sys.platform != "darwin":
        return
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    if directory:
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect the extended ACL for {context}: {exc}"
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if directory:
            _assert_regular_directory_stat(opened, context=context)
            identity = _directory_stat_identity
        else:
            _assert_regular_file_stat(opened, context=context)
            identity = _file_identity
        opened_identity = identity(opened)
        expected_identity = identity(expected) if expected is not None else None
        if expected_identity is not None and opened_identity != expected_identity:
            raise ProtectedArtifactIntegrityError(
                f"{context} changed while its macOS extended ACL was inspected."
            )
        _assert_darwin_no_extended_acl_fd(descriptor, context=context)
        try:
            rebound = os.stat(path, follow_symlinks=False)
        except OSError as exc:
            raise ProtectedArtifactIntegrityError(
                f"Cannot re-inspect {context} after its macOS extended ACL "
                f"was inspected: {exc}"
            ) from exc
        if directory:
            _assert_regular_directory_stat(rebound, context=context)
        else:
            _assert_regular_file_stat(rebound, context=context)
        rebound_identity = identity(rebound)
        if rebound_identity != opened_identity or (
            expected_identity is not None and rebound_identity != expected_identity
        ):
            raise ProtectedArtifactIntegrityError(
                f"{context} changed while its macOS extended ACL was inspected."
            )
    finally:
        os.close(descriptor)


def _assert_darwin_no_extended_acl_fd(descriptor: int, *, context: str) -> None:
    """Reject an open macOS filesystem object with any extended ACL entries."""

    if sys.platform != "darwin":
        return
    entry_count = _darwin_extended_acl_entry_count(descriptor)
    if entry_count:
        raise ProtectedArtifactIntegrityError(
            f"{context} must not have a macOS extended ACL."
        )


def _darwin_extended_acl_entry_count(descriptor: int) -> int:
    """Return zero only when a descriptor has no macOS extended ACL object."""

    try:
        libc = ctypes.CDLL(None, use_errno=True)
        acl_get_fd_np = libc.acl_get_fd_np
        acl_free = libc.acl_free
    except (AttributeError, OSError) as exc:
        raise ProtectedArtifactIntegrityError(
            "Cannot load the macOS extended-ACL inspection functions."
        ) from exc

    acl_get_fd_np.argtypes = [ctypes.c_int, ctypes.c_int]
    acl_get_fd_np.restype = ctypes.c_void_p
    acl_free.argtypes = [ctypes.c_void_p]
    acl_free.restype = ctypes.c_int

    ctypes.set_errno(0)
    acl = acl_get_fd_np(descriptor, _DARWIN_ACL_TYPE_EXTENDED)
    if not acl:
        error = ctypes.get_errno()
        if error == errno.ENOENT:
            return 0
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect the macOS extended ACL (errno {error or 'unknown'})."
        )
    try:
        return 1
    finally:
        acl_free(acl)


def _is_reparse_point(payload: os.stat_result) -> bool:
    return bool(
        getattr(payload, "st_reparse_tag", 0)
        or getattr(payload, "st_file_attributes", 0) & 0x00000400
    )


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        payload = path.lstat()
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected directory identity {path}: {exc}"
        ) from exc
    _assert_regular_directory_stat(payload, context=f"protected directory {path}")
    return _directory_stat_identity(payload)


def _directory_stat_identity(payload: os.stat_result) -> tuple[int, int]:
    return (payload.st_dev, payload.st_ino)


def _file_identity(payload: os.stat_result) -> tuple[int, int, int, int]:
    return (
        payload.st_dev,
        payload.st_ino,
        payload.st_size,
        int(getattr(payload, "st_mtime_ns", int(payload.st_mtime * 1_000_000_000))),
    )


def _validate_portable_component(component: str, *, context: str) -> None:
    if component != unicodedata.normalize("NFC", component):
        raise ProtectedArtifactIntegrityError(
            f"Artifact path is not NFC-normalized: {context!r}"
        )
    if component.endswith((" ", ".")) or any(
        character in _WINDOWS_FORBIDDEN_PATH_CHARS or ord(character) < 32
        for character in component
    ):
        raise ProtectedArtifactIntegrityError(
            f"Artifact path is not portable across supported systems: {context!r}"
        )
    if component.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_NAMES:
        raise ProtectedArtifactIntegrityError(
            f"Artifact path uses a reserved Windows name: {context!r}"
        )


def _portable_name_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def _assert_portable_entry_names(names: Iterator[str] | Sequence[str]) -> None:
    seen: dict[str, str] = {}
    for name in names:
        _validate_portable_component(name, context=name)
        key = _portable_name_key(name)
        previous = seen.get(key)
        if previous is not None and previous != name:
            raise ProtectedArtifactIntegrityError(
                "Protected artifact names collide on a case-insensitive or "
                f"Unicode-normalizing filesystem: {previous!r} and {name!r}."
            )
        seen[key] = name


def _assert_directory_fd_entries_portable(directory_fd: int) -> None:
    try:
        names = os.listdir(directory_fd)
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected artifact directory: {exc}"
        ) from exc
    _assert_portable_entry_names(iter(names))


def _assert_directory_entries_portable(directory: Path) -> None:
    try:
        names = [entry.name for entry in os.scandir(directory)]
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected artifact directory {directory}: {exc}"
        ) from exc
    _assert_portable_entry_names(iter(names))


def _assert_no_portable_collision_fd(directory_fd: int, name: str) -> None:
    key = _portable_name_key(name)
    try:
        names = os.listdir(directory_fd)
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected artifact directory: {exc}"
        ) from exc
    for existing in names:
        if _portable_name_key(existing) == key and existing != name:
            raise ProtectedArtifactIntegrityError(
                "Protected artifact path collides on a case-insensitive or "
                f"Unicode-normalizing filesystem: {existing!r} and {name!r}."
            )


def _assert_path_entry_portable(parent: Path, name: str) -> None:
    key = _portable_name_key(name)
    try:
        entries = list(os.scandir(parent))
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected artifact directory {parent}: {exc}"
        ) from exc
    for entry in entries:
        if _portable_name_key(entry.name) == key and entry.name != name:
            raise ProtectedArtifactIntegrityError(
                "Protected artifact path collides on a case-insensitive or "
                f"Unicode-normalizing filesystem: {entry.name!r} and {name!r}."
            )


def _assert_relative_target_regular(parent_fd: int, name: str) -> None:
    try:
        payload = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected artifact target {name!r}: {exc}"
        ) from exc
    _assert_regular_file_stat(payload, context=f"protected artifact {name!r}")
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(name, flags, dir_fd=parent_fd)
    try:
        opened = os.fstat(descriptor)
        _assert_regular_file_stat(opened, context=f"protected artifact {name!r}")
        _assert_darwin_no_extended_acl_fd(
            descriptor,
            context=f"protected artifact {name!r}",
        )
        if _file_identity(opened) != _file_identity(payload):
            raise ProtectedArtifactIntegrityError(
                f"Protected artifact {name!r} changed while inspected."
            )
    finally:
        os.close(descriptor)


def _assert_path_target_regular(target: Path) -> None:
    if not os.path.lexists(target):
        return
    try:
        payload = target.lstat()
    except OSError as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot inspect protected artifact target {target}: {exc}"
        ) from exc
    _assert_regular_file_stat(payload, context=f"protected artifact {target.name!r}")


def _read_existing_from_fd(
    parent_fd: int,
    name: str,
    expected_size: int,
) -> bytes | None:
    flags = (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        return None
    try:
        payload = os.fstat(descriptor)
        _assert_regular_file_stat(payload, context=f"protected artifact {name!r}")
        _assert_darwin_no_extended_acl_fd(
            descriptor,
            context=f"protected artifact {name!r}",
        )
        data = os.read(descriptor, expected_size + 1)
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        _assert_regular_file_stat(current, context=f"protected artifact {name!r}")
        if _file_identity(current) != _file_identity(payload):
            raise ProtectedArtifactIntegrityError(
                f"Protected artifact {name!r} was replaced while read."
            )
        return data
    finally:
        os.close(descriptor)


def _read_existing_windows(target: Path, expected_size: int) -> bytes | None:
    if not os.path.lexists(target):
        return None
    _assert_path_target_regular(target)
    try:
        with open_windows_readonly_file(
            target,
            require_restrictive_dacl=True,
        ) as (stream, payload):
            _assert_regular_file_stat(
                payload, context=f"protected artifact {target.name!r}"
            )
            if payload.st_size > expected_size:
                return stream.read(expected_size + 1)
            return stream.read(expected_size + 1)
    except (WindowsFileGuardError, WindowsSecurityGuardError) as exc:
        raise ProtectedArtifactIntegrityError(
            f"Cannot safely read protected artifact {target}: {exc}"
        ) from exc


def _read_bounded_fd(
    descriptor: int,
    *,
    maximum_bytes: int,
    label: str,
) -> bytes:
    payload = os.fstat(descriptor)
    if payload.st_size > maximum_bytes:
        raise ProtectedArtifactLimitError(
            f"Protected artifact {label!r} exceeds the {maximum_bytes}-byte limit."
        )
    chunks: list[bytes] = []
    remaining = maximum_bytes + 1
    while remaining > 0:
        chunk = os.read(descriptor, min(remaining, 1024 * 1024))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    data = b"".join(chunks)
    if len(data) > maximum_bytes:
        raise ProtectedArtifactLimitError(
            f"Protected artifact {label!r} exceeds the {maximum_bytes}-byte limit."
        )
    return data


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    written = 0
    while written < len(view):
        count = os.write(descriptor, view[written:])
        if count <= 0:  # pragma: no cover - defensive OS contract check
            raise OSError(errno.EIO, "short protected artifact write")
        written += count


def _unlink_owned_temp(
    parent_fd: int,
    name: str,
    expected_identity: tuple[int, int, int, int],
) -> None:
    try:
        payload = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    _assert_regular_file_kind_stat(payload, context=f"owned temporary {name!r}")
    if _file_identity(payload) != expected_identity:
        raise ProtectedArtifactIntegrityError(
            f"Owned temporary {name!r} changed identity; refusing cleanup."
        )
    os.unlink(name, dir_fd=parent_fd)


def _unlink_owned_temp_path(
    target: Path,
    expected_identity: tuple[int, int, int, int],
) -> None:
    if not os.path.lexists(target):
        return
    payload = target.lstat()
    _assert_regular_file_kind_stat(payload, context=f"owned temporary {target.name!r}")
    if _file_identity(payload) != expected_identity:
        raise ProtectedArtifactIntegrityError(
            f"Owned temporary {target.name!r} changed identity; refusing cleanup."
        )
    target.unlink()


def _fsync_directory(directory_fd: int) -> None:
    try:
        os.fsync(directory_fd)
    except OSError as exc:
        raise ProtectedArtifactDurabilityError(
            f"Cannot confirm durable protected directory metadata: {exc}"
        ) from exc


def _validate_maximum_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ProtectedArtifactLimitError("Artifact byte limit must be positive.")
    return value


def _assert_within_limit(label: str, data: bytes, maximum_bytes: int) -> None:
    if len(data) > maximum_bytes:
        raise ProtectedArtifactLimitError(
            f"Protected artifact {label!r} exceeds the {maximum_bytes}-byte limit."
        )


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise ProtectedArtifactIntegrityError(f"Duplicate JSON object key {key!r}.")
        payload[key] = value
    return payload


def _reject_json_constant(value: str) -> Any:
    raise ProtectedArtifactIntegrityError(
        f"Non-finite JSON number {value!r} is forbidden."
    )


__all__ = [
    "DEFAULT_MAX_ARTIFACT_BYTES",
    "DEFAULT_MAX_PROJECTION_BYTES",
    "ROOT_LOCK_FILENAME",
    "ProtectedArtifactDurabilityError",
    "ProtectedArtifactError",
    "ProtectedArtifactIntegrityError",
    "ProtectedArtifactLimitError",
    "ProtectedArtifactLockError",
    "ProtectedArtifactStore",
    "canonical_json_bytes",
    "validate_portable_relative_path",
]
