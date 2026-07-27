"""Mutation and filesystem-integrity policy for documentation workspaces.

The standalone documentation lifecycle is deliberately stricter than the
managed knowledge-base commands.  It treats both the source project and an
adopted wiki as read-only evidence and gives callers an explicit, small set of
write roots instead of inferring permission from the current working directory.
"""

from __future__ import annotations

import hashlib
import os
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator
from urllib.parse import urlsplit

from .filesystem_guard import (
    WindowsDirectoryGuardError,
    WindowsFileGuardError,
    WindowsIdentityUnavailableError,
    fresh_no_follow_stat,
    guard_windows_directory_chain,
    open_windows_readonly_file,
    windows_object_identity,
    _windows_path_handle_metadata,
)


AGENT_POLICY_FILENAMES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        ".cursorrules",
        ".aider.conf.yml",
        ".aider.conf.yaml",
        "opencode.json",
        "copilot-instructions.md",
    }
)
SOURCE_BASELINE_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        ".tox",
        ".nox",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
    }
)
DEFAULT_MAX_BASELINE_FILES = 100_000
DEFAULT_MAX_BASELINE_FILE_BYTES = 128 * 1024 * 1024
DEFAULT_MAX_BASELINE_TOTAL_BYTES = 2 * 1024 * 1024 * 1024


class DocumentationPolicyError(ValueError):
    """Raised when an external documentation policy cannot be enforced."""


@dataclass(frozen=True)
class TreeBaseline:
    """A deterministic, portable content baseline for a read-only tree."""

    root_display: str
    tree_hash: str
    file_hashes: dict[str, str]
    excluded_directories: tuple[str, ...] = ()

    @property
    def file_count(self) -> int:
        return len(self.file_hashes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_display": self.root_display,
            "tree_hash": self.tree_hash,
            "file_count": self.file_count,
            "file_hashes": dict(self.file_hashes),
            "excluded_directories": list(self.excluded_directories),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TreeBaseline":
        hashes = payload.get("file_hashes")
        if not isinstance(hashes, dict):
            raise DocumentationPolicyError(
                "Tree baseline file_hashes must be an object."
            )
        return cls(
            root_display=str(payload.get("root_display", "")),
            tree_hash=str(payload.get("tree_hash", "")),
            file_hashes={str(key): str(value) for key, value in hashes.items()},
            excluded_directories=tuple(
                str(value) for value in payload.get("excluded_directories", [])
            ),
        )


@dataclass(frozen=True)
class IntegrityDifference:
    root_display: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_display": self.root_display,
            "ok": self.ok,
            "added": list(self.added),
            "removed": list(self.removed),
            "changed": list(self.changed),
        }


@dataclass(frozen=True)
class DocumentationMutationPolicy:
    """Resolved runtime roots and portable policy metadata."""

    workspace_root: Path
    source_root: Path | None
    input_wiki_root: Path | None
    helper_cache_root: Path | None
    capture_root: Path | None
    allowed_write_roots: tuple[Path, ...]
    forbidden_write_roots: tuple[Path, ...]
    trust_source_plugins: bool = False
    live_service_url: str | None = None
    live_service_access_mode: str = "unspecified"
    live_service_observation_allowed: bool = False

    def assert_write_allowed(self, target: str | Path) -> Path:
        resolved = _resolve_path(target)
        if any(_contains(root, resolved) for root in self.forbidden_write_roots):
            raise DocumentationPolicyError(
                f"Write target is inside a read-only evidence root: {resolved}"
            )
        if not any(_contains(root, resolved) for root in self.allowed_write_roots):
            raise DocumentationPolicyError(
                f"Write target is outside the documentation allowlist: {resolved}"
            )
        return resolved

    def to_portable_dict(self) -> dict[str, Any]:
        allowed = ["workspace"]
        if self.helper_cache_root is not None:
            allowed.append("helper_cache")
        if self.capture_root is not None:
            allowed.append("capture")
        forbidden = []
        if self.source_root is not None:
            forbidden.append("source")
        if self.input_wiki_root is not None:
            forbidden.append("input_wiki")
        return {
            "integration_mode": "external_agent_docs",
            "allowed_write_roots": allowed,
            "forbidden_write_roots": forbidden,
            "agent_integration_writes": False,
            "target_cache_writes": False,
            "source_plugins_trusted": self.trust_source_plugins,
            "live_service": {
                "configured": self.live_service_url is not None,
                "access_mode": self.live_service_access_mode,
                "observation_allowed": self.live_service_observation_allowed,
                "responses_are_untrusted_evidence": True,
                "secret_material_persisted": False,
            },
        }


def resolve_documentation_policy(
    workspace_root: str | Path,
    *,
    source_root: str | Path | None = None,
    input_wiki_root: str | Path | None = None,
    helper_cache_root: str | Path | None = None,
    capture_root: str | Path | None = None,
    trust_source_plugins: bool = False,
    live_service_url: str | None = None,
    live_service_access_mode: str = "unspecified",
    live_service_observation_allowed: bool = False,
) -> DocumentationMutationPolicy:
    """Resolve and validate the external documentation mutation policy."""

    workspace = _resolve_path(workspace_root)
    source = _resolve_optional_root(source_root, "source root")
    input_wiki = _resolve_optional_root(input_wiki_root, "input wiki root")
    helper_cache = _resolve_optional_path(helper_cache_root)
    capture = _resolve_optional_path(capture_root)

    for label, forbidden in (("source", source), ("input wiki", input_wiki)):
        if forbidden is None:
            continue
        if _overlap(workspace, forbidden):
            raise DocumentationPolicyError(
                f"Documentation workspace must not overlap the {label} root."
            )

    for label, allowed in (("helper cache", helper_cache), ("capture", capture)):
        if allowed is None:
            continue
        for forbidden_label, forbidden in (
            ("source", source),
            ("input wiki", input_wiki),
        ):
            if forbidden is not None and _overlap(allowed, forbidden):
                raise DocumentationPolicyError(
                    f"The {label} root must not overlap the {forbidden_label} root."
                )

    _validate_live_service(
        live_service_url,
        access_mode=live_service_access_mode,
        observation_allowed=live_service_observation_allowed,
        capture_root=capture,
    )

    allowed_roots = tuple(
        root for root in (workspace, helper_cache, capture) if root is not None
    )
    forbidden_roots = tuple(root for root in (source, input_wiki) if root is not None)
    return DocumentationMutationPolicy(
        workspace_root=workspace,
        source_root=source,
        input_wiki_root=input_wiki,
        helper_cache_root=helper_cache,
        capture_root=capture,
        allowed_write_roots=allowed_roots,
        forbidden_write_roots=forbidden_roots,
        trust_source_plugins=trust_source_plugins,
        live_service_url=live_service_url,
        live_service_access_mode=live_service_access_mode,
        live_service_observation_allowed=live_service_observation_allowed,
    )


def capture_tree_baseline(
    root: str | Path,
    *,
    display: str,
    excluded_directories: Iterable[str] = (),
    max_files: int = DEFAULT_MAX_BASELINE_FILES,
    max_file_bytes: int = DEFAULT_MAX_BASELINE_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_BASELINE_TOTAL_BYTES,
) -> TreeBaseline:
    """Hash regular files without following links or requiring Git."""

    limits = {
        "max_files": max_files,
        "max_file_bytes": max_file_bytes,
        "max_total_bytes": max_total_bytes,
    }
    for label, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise DocumentationPolicyError(f"{label} must be a non-negative integer.")

    resolved = _resolve_existing_directory(root, display)
    excluded = frozenset(str(value) for value in excluded_directories)
    file_hashes: dict[str, str] = {}
    total_bytes = 0
    for rel_path, path, inspected in _walk_regular_files(resolved, excluded=excluded):
        if len(file_hashes) >= max_files:
            raise DocumentationPolicyError(
                f"{display} exceeds the bounded baseline limit of {max_files} files."
            )
        file_bytes = int(inspected.st_size)
        if file_bytes > max_file_bytes:
            raise DocumentationPolicyError(
                f"{display} file {rel_path!r} exceeds the per-file byte limit of "
                f"{max_file_bytes}."
            )
        next_total = total_bytes + file_bytes
        if next_total > max_total_bytes:
            raise DocumentationPolicyError(
                f"{display} exceeds the aggregate byte limit of {max_total_bytes} "
                f"at {rel_path!r}."
            )
        file_hashes[rel_path] = _hash_file(
            path,
            inspected=inspected,
            max_bytes=min(max_file_bytes, max_total_bytes - total_bytes),
        )
        total_bytes = next_total
    return TreeBaseline(
        root_display=display,
        tree_hash=_hash_labeled_hashes(file_hashes),
        file_hashes=file_hashes,
        excluded_directories=tuple(sorted(excluded)),
    )


def compare_tree_baseline(
    baseline: TreeBaseline,
    root: str | Path,
    *,
    max_files: int = DEFAULT_MAX_BASELINE_FILES,
    max_file_bytes: int = DEFAULT_MAX_BASELINE_FILE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_BASELINE_TOTAL_BYTES,
) -> IntegrityDifference:
    current = capture_tree_baseline(
        root,
        display=baseline.root_display,
        excluded_directories=baseline.excluded_directories,
        max_files=max_files,
        max_file_bytes=max_file_bytes,
        max_total_bytes=max_total_bytes,
    )
    before = baseline.file_hashes
    after = current.file_hashes
    return IntegrityDifference(
        root_display=baseline.root_display,
        added=tuple(sorted(set(after) - set(before))),
        removed=tuple(sorted(set(before) - set(after))),
        changed=tuple(
            sorted(
                path for path in set(before) & set(after) if before[path] != after[path]
            )
        ),
    )


def source_tree_baseline(root: str | Path) -> TreeBaseline:
    return capture_tree_baseline(
        root,
        display="source",
        excluded_directories=SOURCE_BASELINE_EXCLUDED_DIRS,
    )


def input_wiki_tree_baseline(root: str | Path) -> TreeBaseline:
    return capture_tree_baseline(root, display="input_wiki")


def hash_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_file(path: str | Path) -> str:
    return _hash_file(Path(path))


def _walk_regular_files(
    root: Path, *, excluded: frozenset[str]
) -> Iterable[tuple[str, Path, os.stat_result]]:
    root_stat = _lstat(root, context="baseline root")
    _assert_safe_directory(root, root_stat, context="baseline root")
    stack: list[tuple[Path, Path, os.stat_result]] = [(Path(), root, root_stat)]
    while stack:
        rel_dir, abs_dir, inspected_dir = stack.pop()
        with _guard_baseline_directory(root, rel_dir):
            try:
                current_dir = fresh_no_follow_stat(abs_dir)
                _assert_safe_directory(
                    abs_dir,
                    current_dir,
                    context="baseline directory",
                )
                _assert_same_file_identity(
                    inspected_dir,
                    current_dir,
                    path=abs_dir,
                    operation="directory traversal",
                )
                with os.scandir(abs_dir) as iterator:
                    entries = sorted(iterator, key=lambda entry: entry.name)
                after_scan = fresh_no_follow_stat(abs_dir)
                _assert_safe_directory(
                    abs_dir,
                    after_scan,
                    context="baseline directory",
                )
                _assert_same_file_identity(
                    current_dir,
                    after_scan,
                    path=abs_dir,
                    operation="directory traversal",
                )
            except OSError as exc:
                raise DocumentationPolicyError(
                    f"Cannot inspect {abs_dir}: {exc}"
                ) from exc
            child_dirs: list[tuple[Path, Path, os.stat_result]] = []
            for entry in entries:
                rel = rel_dir / entry.name
                try:
                    inspected = fresh_no_follow_stat(entry.path)
                except OSError as exc:
                    raise DocumentationPolicyError(
                        f"Cannot inspect {entry.path}: {exc}"
                    ) from exc
                if stat.S_ISLNK(inspected.st_mode):
                    raise DocumentationPolicyError(
                        "Symlinked content is not allowed in a baselined evidence "
                        f"tree: {rel.as_posix()}"
                    )
                if _is_windows_reparse_point(inspected):
                    raise DocumentationPolicyError(
                        "Windows reparse-point content is not allowed in a baselined "
                        f"evidence tree: {rel.as_posix()}"
                    )
                if stat.S_ISDIR(inspected.st_mode):
                    if entry.name not in excluded:
                        child_dirs.append((rel, Path(entry.path), inspected))
                    continue
                if not stat.S_ISREG(inspected.st_mode):
                    raise DocumentationPolicyError(
                        "Non-regular content is not allowed in a baselined evidence "
                        f"tree: {rel.as_posix()}"
                    )
                yield rel.as_posix(), Path(entry.path), inspected
            stack.extend(reversed(child_dirs))


@contextmanager
def _guard_baseline_directory(
    root: Path,
    relative_directory: Path,
) -> Iterator[None]:
    """Pin a Windows baseline directory chain for inspection and leaf reads."""

    if os.name != "nt":
        yield
        return
    try:
        with guard_windows_directory_chain(root, relative_directory.parts):
            yield
    except WindowsDirectoryGuardError as exc:
        relative = relative_directory.as_posix() or "."
        raise DocumentationPolicyError(
            f"Cannot pin Windows baseline directory {relative}: {exc}"
        ) from exc


def _hash_file(
    path: Path,
    *,
    inspected: os.stat_result | None = None,
    max_bytes: int | None = None,
) -> str:
    if os.name == "nt":
        absolute_path = Path(os.path.abspath(os.fspath(path)))
        try:
            with guard_windows_directory_chain(absolute_path.parent, ()):
                return _hash_windows_file(
                    absolute_path,
                    inspected=inspected,
                    max_bytes=max_bytes,
                )
        except WindowsDirectoryGuardError as exc:
            raise DocumentationPolicyError(
                f"Cannot pin the Windows parent of baselined file {absolute_path}: "
                f"{exc}"
            ) from exc

    digest = hashlib.sha256()
    descriptor: int | None = None
    try:
        before = os.lstat(path)
        _assert_safe_regular_file(path, before)
        if inspected is not None:
            _assert_same_file_identity(
                inspected,
                before,
                path=path,
                operation="file hashing",
            )

        flags = os.O_RDONLY
        flags |= getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened_before = os.fstat(descriptor)
        _assert_safe_regular_file(path, opened_before)
        _assert_same_file_identity(
            before,
            opened_before,
            path=path,
            operation="no-follow file open",
        )

        bytes_read = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            bytes_read += len(chunk)
            if max_bytes is not None and bytes_read > max_bytes:
                raise DocumentationPolicyError(
                    f"Baselined file exceeded its byte limit while hashing: {path}"
                )
            digest.update(chunk)

        opened_after = os.fstat(descriptor)
        _assert_stable_file_metadata(opened_before, opened_after, path=path)
    except OSError as exc:
        raise DocumentationPolicyError(f"Cannot hash {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass

    after = _lstat(path, context="hashed file")
    _assert_safe_regular_file(path, after)
    _assert_same_file_identity(
        opened_after,
        after,
        path=path,
        operation="post-hash verification",
    )
    _assert_stable_file_metadata(opened_after, after, path=path)
    return "sha256:" + digest.hexdigest()


def _hash_windows_file(
    path: Path,
    *,
    inspected: os.stat_result | None,
    max_bytes: int | None,
) -> str:
    """Hash one Windows leaf through the native no-redirection read guard."""

    digest = hashlib.sha256()
    try:
        before = fresh_no_follow_stat(path)
        _assert_safe_regular_file(path, before)
        if inspected is not None:
            _assert_same_file_identity(
                inspected,
                before,
                path=path,
                operation="file hashing",
            )

        with open_windows_readonly_file(path) as (handle, opened_before):
            _assert_safe_regular_file(path, opened_before)
            _assert_same_file_identity(
                before,
                opened_before,
                path=path,
                operation="guarded file open",
            )
            _assert_stable_windows_path_handle_metadata(
                before,
                opened_before,
                path=path,
            )

            bytes_read = 0
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if max_bytes is not None and bytes_read > max_bytes:
                    raise DocumentationPolicyError(
                        f"Baselined file exceeded its byte limit while hashing: {path}"
                    )
                digest.update(chunk)

            opened_after = os.fstat(handle.fileno())
            _assert_same_file_identity(
                opened_before,
                opened_after,
                path=path,
                operation="file hashing",
            )
            _assert_stable_file_metadata(opened_before, opened_after, path=path)

            after = fresh_no_follow_stat(path)
            _assert_safe_regular_file(path, after)
            _assert_same_file_identity(
                opened_after,
                after,
                path=path,
                operation="post-hash verification",
            )
            _assert_stable_windows_path_handle_metadata(
                after,
                opened_after,
                path=path,
            )
    except WindowsFileGuardError as exc:
        raise DocumentationPolicyError(
            f"Cannot safely hash Windows baselined file {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise DocumentationPolicyError(f"Cannot hash {path}: {exc}") from exc

    return "sha256:" + digest.hexdigest()


def _lstat(path: Path, *, context: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise DocumentationPolicyError(
            f"Cannot inspect {context} {path}: {exc}"
        ) from exc


def _is_windows_reparse_point(result: os.stat_result) -> bool:
    attributes = int(getattr(result, "st_file_attributes", 0))
    reparse_attribute = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return bool(attributes & reparse_attribute)


def _assert_safe_directory(
    path: Path,
    result: os.stat_result,
    *,
    context: str,
) -> None:
    if stat.S_ISLNK(result.st_mode):
        raise DocumentationPolicyError(f"Symlinked {context} is not allowed: {path}")
    if _is_windows_reparse_point(result):
        raise DocumentationPolicyError(
            f"Windows reparse-point {context} is not allowed: {path}"
        )
    if not stat.S_ISDIR(result.st_mode):
        raise DocumentationPolicyError(f"{context} is not a directory: {path}")


def _assert_safe_regular_file(path: Path, result: os.stat_result) -> None:
    if stat.S_ISLNK(result.st_mode):
        raise DocumentationPolicyError(
            f"Symlinked content is not allowed in a baselined evidence tree: {path}"
        )
    if _is_windows_reparse_point(result):
        raise DocumentationPolicyError(
            "Windows reparse-point content is not allowed in a baselined "
            f"evidence tree: {path}"
        )
    if not stat.S_ISREG(result.st_mode):
        raise DocumentationPolicyError(
            f"Non-regular content is not allowed in a baselined evidence tree: {path}"
        )


def _assert_same_file_identity(
    before: os.stat_result,
    after: os.stat_result,
    *,
    path: Path,
    operation: str,
) -> None:
    if os.name == "nt":
        try:
            same_identity = windows_object_identity(
                before,
                context=f"{operation} before {path}",
            ) == windows_object_identity(
                after,
                context=f"{operation} after {path}",
            )
        except WindowsIdentityUnavailableError as exc:
            raise DocumentationPolicyError(
                f"Windows baseline identity is unavailable during {operation}: {path}"
            ) from exc
        if not same_identity:
            raise DocumentationPolicyError(
                f"Baselined content changed identity during {operation}: {path}"
            )
        return

    before_inode = int(getattr(before, "st_ino", 0))
    after_inode = int(getattr(after, "st_ino", 0))
    if before_inode or after_inode:
        same_identity = before_inode == after_inode and int(
            getattr(before, "st_dev", 0)
        ) == int(getattr(after, "st_dev", 0))
    else:
        same_identity = _stable_metadata_signature(
            before
        ) == _stable_metadata_signature(after)
    if not same_identity:
        raise DocumentationPolicyError(
            f"Baselined content changed identity during {operation}: {path}"
        )


def _assert_stable_file_metadata(
    before: os.stat_result,
    after: os.stat_result,
    *,
    path: Path,
) -> None:
    if _stable_metadata_signature(before) != _stable_metadata_signature(after):
        raise DocumentationPolicyError(
            f"Baselined content changed while it was being hashed: {path}"
        )


def _assert_stable_windows_path_handle_metadata(
    path_result: os.stat_result,
    handle_result: os.stat_result,
    *,
    path: Path,
) -> None:
    if _windows_path_handle_metadata(path_result) != _windows_path_handle_metadata(
        handle_result
    ):
        raise DocumentationPolicyError(
            f"Baselined content changed while it was being hashed: {path}"
        )


def _stable_metadata_signature(result: os.stat_result) -> tuple[int, int, int, int]:
    return (
        int(result.st_mode),
        int(result.st_size),
        int(getattr(result, "st_mtime_ns", int(result.st_mtime * 1_000_000_000))),
        int(getattr(result, "st_ctime_ns", int(result.st_ctime * 1_000_000_000))),
    )


def _hash_labeled_hashes(file_hashes: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, file_hash in sorted(file_hashes.items()):
        digest.update(path.replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _validate_live_service(
    url: str | None,
    *,
    access_mode: str,
    observation_allowed: bool,
    capture_root: Path | None,
) -> None:
    allowed_modes = {"unspecified", "anonymous", "non-secret"}
    if access_mode not in allowed_modes:
        raise DocumentationPolicyError(
            "Live-service access mode must be unspecified, anonymous, or non-secret."
        )
    if url is None:
        if observation_allowed:
            raise DocumentationPolicyError(
                "Live-service observation cannot be enabled without a service URL."
            )
        return
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise DocumentationPolicyError(
            "Live-service URL must be an absolute HTTP(S) URL."
        )
    if parts.username or parts.password or parts.query or parts.fragment:
        raise DocumentationPolicyError(
            "Live-service URL must not contain credentials, query parameters, or fragments."
        )
    if observation_allowed and capture_root is None:
        raise DocumentationPolicyError(
            "Live-service observation requires an explicit disposable capture root."
        )


def _resolve_existing_directory(path: str | Path, label: str) -> Path:
    candidate = Path(path).expanduser()
    inspected = _lstat(candidate, context=label)
    _assert_safe_directory(candidate, inspected, context=label)
    resolved = _resolve_path(candidate)
    candidate_after_resolution = _lstat(candidate, context=label)
    _assert_safe_directory(candidate, candidate_after_resolution, context=label)
    _assert_same_file_identity(
        inspected,
        candidate_after_resolution,
        path=candidate,
        operation="baseline-root resolution",
    )
    resolved_stat = _lstat(resolved, context=label)
    _assert_safe_directory(resolved, resolved_stat, context=label)
    _assert_same_file_identity(
        candidate_after_resolution,
        resolved_stat,
        path=resolved,
        operation="baseline-root resolution",
    )
    return resolved


def _resolve_optional_root(path: str | Path | None, label: str) -> Path | None:
    if path is None:
        return None
    return _resolve_existing_directory(path, label)


def _resolve_optional_path(path: str | Path | None) -> Path | None:
    return None if path is None else _resolve_path(path)


def _resolve_path(path: str | Path) -> Path:
    try:
        return Path(path).expanduser().resolve(strict=False)
    except OSError as exc:
        raise DocumentationPolicyError(f"Cannot resolve path {path!s}: {exc}") from exc


def _contains(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
    except ValueError:
        return False
    return True


def _overlap(left: Path, right: Path) -> bool:
    return _contains(left, right) or _contains(right, left)


__all__ = [
    "AGENT_POLICY_FILENAMES",
    "DEFAULT_MAX_BASELINE_FILE_BYTES",
    "DEFAULT_MAX_BASELINE_FILES",
    "DEFAULT_MAX_BASELINE_TOTAL_BYTES",
    "DocumentationMutationPolicy",
    "DocumentationPolicyError",
    "IntegrityDifference",
    "SOURCE_BASELINE_EXCLUDED_DIRS",
    "TreeBaseline",
    "capture_tree_baseline",
    "compare_tree_baseline",
    "hash_bytes",
    "hash_file",
    "input_wiki_tree_baseline",
    "resolve_documentation_policy",
    "source_tree_baseline",
]
