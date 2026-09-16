"""Guarded, bounded filesystem access for committed knowledge objects."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Any

from .filesystem_guard import guard_windows_directory_chain, open_windows_readonly_file
from .io import first_unsafe_path_component
from .knowledge_storage import KnowledgeStorageError, MAX_EXPANDED_BYTES
from .validation import is_portable_relative_path


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def _require_relative_name(relative: str) -> None:
    if not is_portable_relative_path(relative):
        raise KnowledgeStorageError("path", "requires a portable relative name")


def _absolute_path(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    if first_unsafe_path_component(path) is not None:
        raise KnowledgeStorageError("path", "symlink, reparse point or unsafe path")
    # The project's shared path policy permits root-owned platform aliases such
    # as macOS /var. Resolve only that trusted first component, never user paths.
    if len(path.parts) > 1:
        first = Path(path.anchor) / path.parts[1]
        if first.is_symlink():
            path = first.resolve().joinpath(*path.parts[2:])
    return path


@dataclass(frozen=True)
class ReadObservation:
    content: bytes
    identity: tuple[int, ...]
    directories: tuple[tuple[str, tuple[int, int]], ...]


def read_guarded(path: Path, maximum: int) -> ReadObservation:
    """Read a regular file through pinned/no-follow ancestors and bound its bytes."""
    if type(maximum) is not int or not 0 <= maximum <= MAX_EXPANDED_BYTES:
        raise KnowledgeStorageError("maximum", "invalid read limit")
    target = _absolute_path(path)
    try:
        if os.name == "nt":
            with guard_windows_directory_chain(Path(target.anchor), target.parent.parts[1:]):
                with open_windows_readonly_file(target) as (stream, _):
                    before = os.fstat(stream.fileno())
                    if before.st_size > maximum or not stat.S_ISREG(before.st_mode):
                        raise KnowledgeStorageError(target.name, "file exceeds limit or is not regular", code="storage-limit")
                    content = stream.read(before.st_size + 1)
                    after = os.fstat(stream.fileno())
                    current = target.lstat()
                    directories = tuple((str(p), (p.stat().st_dev, p.stat().st_ino)) for p in target.parents)
        else:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
            with ExitStack() as stack:
                parent_fd = os.open(target.anchor, flags)
                stack.callback(os.close, parent_fd)
                pinned: list[tuple[int, str, tuple[int, int]]] = []
                directories_list = []
                parent_path = Path(target.anchor)
                for part in target.parent.parts[1:]:
                    child = os.open(part, flags, dir_fd=parent_fd)
                    stack.callback(os.close, child)
                    child_stat = os.fstat(child)
                    identity = (child_stat.st_dev, child_stat.st_ino)
                    pinned.append((parent_fd, part, identity))
                    parent_path /= part
                    directories_list.append((str(parent_path), identity))
                    parent_fd = child
                fd = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                             | getattr(os, "O_CLOEXEC", 0), dir_fd=parent_fd)
                with os.fdopen(fd, "rb") as stream:
                    before = os.fstat(stream.fileno())
                    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                        raise KnowledgeStorageError(target.name, "must be one regular file without hard links")
                    if before.st_size > maximum:
                        raise KnowledgeStorageError(target.name, "file exceeds byte limit", code="storage-limit")
                    content = stream.read(before.st_size + 1)
                    after = os.fstat(stream.fileno())
                    current = os.stat(target.name, dir_fd=parent_fd, follow_symlinks=False)
                for ancestor, name, identity in pinned:
                    observed = os.stat(name, dir_fd=ancestor, follow_symlinks=False)
                    if (observed.st_dev, observed.st_ino) != identity or not stat.S_ISDIR(observed.st_mode):
                        raise KnowledgeStorageError(target.name, "parent changed during read", code="storage-mutation")
                directories = tuple(directories_list)
        if len(content) > maximum:
            raise KnowledgeStorageError(target.name, "file exceeds byte limit", code="storage-limit")
        if _identity(before) != _identity(after) or _identity(after) != _identity(current):
            raise KnowledgeStorageError(target.name, "file changed during read", code="storage-mutation")
        return ReadObservation(content, _identity(after), directories)
    except KnowledgeStorageError:
        raise
    except OSError as exc:
        raise KnowledgeStorageError(target.name, "required file is missing or cannot be read safely",
                                    code="storage-missing" if isinstance(exc, FileNotFoundError) else "storage-invalid") from exc


class StorageReadSession:
    """Request-owned file observations, with charged authoritative rechecks."""

    def __init__(self, wiki_dir: str | Path, *, max_bytes: int = MAX_EXPANDED_BYTES):
        if type(max_bytes) is not int or not 0 < max_bytes <= MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("max_bytes", "invalid read budget")
        self.root = _absolute_path(Path(wiki_dir))
        self.maximum = max_bytes
        self.bytes_read = 0
        self.reads = 0
        self.observations: dict[str, ReadObservation] = {}

    def read(self, relative: str, maximum: int) -> bytes:
        _require_relative_name(relative)
        remaining = self.maximum - self.bytes_read
        if remaining < 0:
            raise KnowledgeStorageError("read", "inspection budget exhausted", code="storage-budget-exhausted")
        try:
            observed = read_guarded(self.root / relative, min(maximum, remaining))
        except KnowledgeStorageError as exc:
            if exc.code == "storage-limit" and remaining < maximum:
                raise KnowledgeStorageError("read", "inspection budget exhausted", code="storage-budget-exhausted") from exc
            raise
        self.bytes_read += len(observed.content)
        self.reads += 1
        prior = self.observations.get(relative)
        if prior is not None and prior != observed:
            raise KnowledgeStorageError(relative, "input changed during the request", code="storage-mutation")
        self.observations[relative] = observed
        return observed.content

    def recheck(self) -> None:
        for relative, observation in tuple(self.observations.items()):
            self.read(relative, len(observation.content))

    def receipt(self) -> dict[str, Any]:
        return {"bytes_read": self.bytes_read, "read_operations": self.reads,
                "files": sorted(self.observations)}
