"""Immutable adoption detection and guarded maintenance publication basis."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot

from .filesystem_guard import ensure_guarded_directory, atomic_write_guarded_bytes
from .io import first_unsafe_path_component
from .knowledge_storage import canonical_bytes, digest, MAX_EXPANDED_BYTES
from .knowledge_storage_io import read_guarded, _absolute_path

ADOPTION_FILENAME = ".llm-wiki-maintenance-adoption.json"
STORAGE_LOCK_FILENAME = "llm-wiki-storage.lock"
_OWNED_STORAGE: ContextVar[tuple | None] = ContextVar("llm_wiki_storage_owner", default=None)
_OWNED_GOVERNANCE: ContextVar[tuple | None] = ContextVar("llm_wiki_governance_owner", default=None)


class MaintenanceProtocolError(ValueError):
    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(message)


def _identity():
    try:
        task = asyncio.current_task()
    except RuntimeError:
        task = None
    return os.getpid(), threading.get_ident(), id(task) if task is not None else None


@contextmanager
def storage_writer_lock(wiki_dir: str | Path) -> Iterator[None]:
    """Reuse only the same verified operation's non-reentrant storage lock."""
    from .knowledge_governance import governance_lock

    root = _absolute_path(Path(wiki_dir))
    key = (str(root), *_identity())
    if _OWNED_STORAGE.get() == key:
        yield
        return
    with governance_lock(root, _lock_filename=STORAGE_LOCK_FILENAME):
        token = _OWNED_STORAGE.set(key)
        try:
            yield
        finally:
            _OWNED_STORAGE.reset(token)


@contextmanager
def governance_writer_lock(wiki_dir: str | Path) -> Iterator[None]:
    from .knowledge_governance import governance_lock

    root = _absolute_path(Path(wiki_dir))
    key = (str(root), *_identity())
    if _OWNED_GOVERNANCE.get() == key:
        yield
        return
    if _OWNED_STORAGE.get() == key:
        raise MaintenanceProtocolError("lock-order", "Governance lock must precede storage publication")
    with governance_lock(root):
        token = _OWNED_GOVERNANCE.set(key)
        try:
            yield
        finally:
            _OWNED_GOVERNANCE.reset(token)


def load_adoption_marker(wiki_dir: str | Path) -> dict | None:
    from .maintenance_state import validate_maintenance_adoption
    from .request_json import _pairs, _constant

    path = _absolute_path(Path(wiki_dir)) / ADOPTION_FILENAME
    if not path.exists() and not path.is_symlink():
        return None
    try:
        raw = read_guarded(path, 65536).content
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        marker = validate_maintenance_adoption(value)
        if raw != canonical_bytes(marker):
            raise ValueError("adoption marker must retain canonical immutable bytes")
        return marker
    except (ValueError, OSError, TypeError) as exc:
        raise MaintenanceProtocolError("adoption-invalid", f"Maintenance adoption marker is invalid: {exc}") from exc


def guard_maintenance_owner(wiki_dir: str | Path, manifest=None):
    """Never seed or repair an adopted wiki whose durable authority was lost."""
    from .sync_manifest import SyncManifest
    from .maintenance_state import maintenance_state_hash, validate_maintenance_state

    root = _absolute_path(Path(wiki_dir))
    marker = load_adoption_marker(root)
    try:
        if manifest is None:
            manifest = SyncManifest.load(root)
    except FileNotFoundError:
        if marker is None:
            return None
        raise MaintenanceProtocolError("owner-missing", "Maintenance owner is missing; restore a complete committed recovery snapshot") from None
    except (ValueError, OSError, TypeError) as exc:
        if marker is None:
            raise
        raise MaintenanceProtocolError("owner-invalid", "Adopted maintenance owner is invalid; complete recovery is required") from exc
    state = getattr(manifest, "maintenance_state", None)
    if marker is None:
        if state is not None:
            raise MaintenanceProtocolError("adoption-missing", "Maintenance owner exists without its immutable adoption marker")
        return None
    if state is None:
        raise MaintenanceProtocolError("owner-incompatible", "Adoption marker exists with a legacy owner; complete recovery is required")
    state = validate_maintenance_state(state)
    marker_hash = digest(canonical_bytes(marker))
    if state["adoption_id"] != marker["adoption_id"] or state["guard_hash"] != marker_hash:
        raise MaintenanceProtocolError("adoption-mismatch", "Maintenance authority does not bind the immutable marker")
    commitments = manifest.artifact_hashes
    if commitments is None or commitments.maintenance_adoption_hash != marker_hash:
        raise MaintenanceProtocolError("adoption-mismatch", "Manifest does not commit the immutable maintenance marker")
    payload = manifest.to_payload()
    if payload.get("version") != 7 or payload.get("adoption_id") != marker["adoption_id"] or payload.get("maintenance_state_hash") != maintenance_state_hash(state):
        raise MaintenanceProtocolError("owner-mismatch", "Maintenance owner identity or state commitment disagrees")
    return marker


def snapshot_wiki(wiki_dir: str | Path) -> dict[str, bytes]:
    root = _absolute_path(Path(wiki_dir))
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative in {"llm-wiki-storage.lock", "llm-wiki-governance.lock"} or relative.startswith((".llm-wiki-locks/", ".llm-wiki-page-moves-")):
            continue
        if first_unsafe_path_component(path) is not None:
            raise MaintenanceProtocolError("unsafe-wiki", "Maintenance preimage cannot follow symbolic links")
        if path.is_dir():
            continue
        raw = read_guarded(path, MAX_EXPANDED_BYTES).content
        result[relative] = raw
    return result


@dataclass
class WikiWriteBasis:
    root: Path
    expected: dict[str, bytes]
    source_snapshot: SourceSnapshot | None = None
    recovery_directory: Path | None = None
    eligible_images: dict[str, list[str | None]] | None = None
    preimages: dict[str, bytes] = field(init=False)

    def __post_init__(self):
        self.preimages = dict(self.expected)

    def _relative(self, path: Path) -> str | None:
        absolute = _absolute_path(path)
        return absolute.relative_to(self.root).as_posix() if absolute.is_relative_to(self.root) else None

    def before_write(self, path: Path, content: bytes | None) -> None:
        relative = self._relative(path)
        if relative is None:
            return
        if relative == ".llm-wiki-manifest.json":
            self.assert_current()
        else:
            self.assert_source_current()
        previous = self.expected.get(relative)
        if relative == ADOPTION_FILENAME and previous is not None and previous != content:
            raise MaintenanceProtocolError("adoption-immutable", "Maintenance adoption marker cannot be replaced or removed")
        if path.exists() or path.is_symlink():
            current = read_guarded(_absolute_path(path), MAX_EXPANDED_BYTES).content
        else:
            current = None
        if current != previous:
            raise MaintenanceProtocolError("wiki-changed", f"Captured wiki input changed before publication: {relative}")
        if self.recovery_directory is not None:
            if self.eligible_images is None:
                self.eligible_images = {name: [digest(raw)] for name, raw in self.expected.items()}
            images = self.eligible_images.setdefault(relative, [None])
            planned_hash = digest(content) if content is not None else None
            if planned_hash not in images:
                images.append(planned_hash)
            # Record the eligible postimage before the atomic replacement.
            journal_path = self.recovery_directory / "publication-journal.json"
            old_journal = read_guarded(journal_path, MAX_EXPANDED_BYTES).content if journal_path.exists() else None
            atomic_write_guarded_bytes(journal_path, canonical_bytes({
                "schema_version": "llm-wiki-maintenance-publication/v1",
                "preimage_metadata_hash": digest(read_guarded(self.recovery_directory / "maintenance-recovery.json", MAX_EXPANDED_BYTES).content),
                "eligible_images": self.eligible_images,
            }), expected_existing=old_journal)


    def after_write(self, path: Path, content: bytes | None) -> None:
        relative = self._relative(path)
        if relative is None:
            return
        if content is None:
            self.expected.pop(relative, None)
            return
        if relative == ADOPTION_FILENAME and relative in self.expected and self.expected[relative] != content:
            raise MaintenanceProtocolError("adoption-immutable", "Maintenance adoption marker cannot be replaced")
        if read_guarded(_absolute_path(path), max(1, len(content))).content != content:
            raise MaintenanceProtocolError("wiki-changed", "Published wiki bytes changed during the operation")
        self.expected[relative] = content

    def assert_current(self) -> None:
        self.assert_source_current()
        if snapshot_wiki(self.root) != self.expected:
            raise MaintenanceProtocolError("wiki-changed", "Wiki changed outside its captured publication operation")

    def assert_source_current(self) -> None:
        if self.source_snapshot is not None:
            from .source_snapshot import source_snapshot_matches_current_files

            if not source_snapshot_matches_current_files(self.source_snapshot):
                raise MaintenanceProtocolError("source-changed", "Source changed after maintenance capture")


def save_recovery_snapshot(directory: Path, files: dict[str, bytes], *, marker: dict | None, kind="committed"):
    root = _absolute_path(directory)
    ensure_guarded_directory(root, mode=0o700)
    metadata = {"schema_version": "llm-wiki-maintenance-recovery/v1", "marker": marker, "kind": kind,
                "files": {name: {"hash": digest(raw), "bytes": len(raw)} for name, raw in sorted(files.items())}}
    for name, raw in {**files, "maintenance-recovery.json": canonical_bytes(metadata)}.items():
        path = root / name
        ensure_guarded_directory(path.parent, mode=0o700)
        prior = read_guarded(path, MAX_EXPANDED_BYTES).content if path.exists() or path.is_symlink() else None
        if prior is not None and prior != raw:
            raise MaintenanceProtocolError("recovery-mismatch", "Recovery directory contains another preimage")
        if prior is None:
            atomic_write_guarded_bytes(path, raw, expected_existing=None)
    return metadata


def _recovery_directory(root: Path, files: dict[str, bytes]) -> Path:
    from .knowledge_governance import _governance_lock_root

    lock_root = _governance_lock_root(root)
    parent = lock_root if lock_root != root else root.parent / ".llm-wiki-maintenance-recovery"
    key = digest(canonical_bytes({name: digest(raw) for name, raw in sorted(files.items())}))[7:]
    return parent / "maintenance-preimages" / key


@contextmanager
def maintenance_write_operation(wiki_dir: str | Path, *, dry_run=False, recovery_dir: Path | None = None):
    """Hold locks from capture to publication; adopted writes retain preimages."""
    from .wiki_write_basis import ACTIVE_WRITE_BASIS

    root = _absolute_path(Path(wiki_dir))
    if dry_run:
        guard_maintenance_owner(root)
        yield None
        return
    if load_adoption_marker(root) is None:
        guard_maintenance_owner(root)
        yield None
        return
    with governance_writer_lock(root), storage_writer_lock(root):
        marker = guard_maintenance_owner(root)
        if marker is None:
            yield None
            return
        files = snapshot_wiki(root)
        directory = _absolute_path(Path(recovery_dir)) if recovery_dir is not None else _recovery_directory(root, files)
        if directory == root or directory.is_relative_to(root):
            raise MaintenanceProtocolError("recovery-path", "Recovery preimages must be outside the managed wiki")
        save_recovery_snapshot(directory, files, marker=marker, kind="captured-preimage")
        basis = WikiWriteBasis(root, dict(files), recovery_directory=directory)
        token = ACTIVE_WRITE_BASIS.set(basis)
        try:
            yield basis
            basis.assert_current()
            committed = snapshot_wiki(root)
            committed_directory = _recovery_directory(root, committed) / "committed"
            save_recovery_snapshot(committed_directory, committed, marker=marker)
        finally:
            ACTIVE_WRITE_BASIS.reset(token)


def unlink_maintenance_page(path: Path) -> None:
    """Delete managed prose against the operation's captured exact preimage."""
    from .wiki_write_basis import ACTIVE_WRITE_BASIS
    from .filesystem_guard import unlink_guarded_bytes

    basis = ACTIVE_WRITE_BASIS.get()
    if basis is None:
        path.unlink()
        return
    absolute = _absolute_path(path)
    relative = absolute.relative_to(basis.root).as_posix()
    expected = basis.expected.get(relative)
    if expected is None:
        raise MaintenanceProtocolError("wiki-changed", "Managed deletion lacks a captured preimage")
    unlink_guarded_bytes(absolute, expected=expected)
