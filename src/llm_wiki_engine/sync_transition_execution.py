"""Guarded execution of source-page moves, with retained failure recovery data.

The plan it executes is the application's verified page transition plan (the
``page_transitions`` integration); execution reads only its declared moves.
"""

from __future__ import annotations

from .layout import DEFAULT_LAYOUT

from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import stat
from typing import Any
import uuid

from llm_wiki_engine.filesystem_guard import (
    atomic_write_guarded_bytes,
    atomic_write_private_bytes,
    ensure_guarded_directory,
    guarded_tree_manifest,
    remove_guarded_tree,
    unlink_guarded_bytes,
)
from llm_wiki_engine.knowledge_storage import MAX_EXPANDED_BYTES, KnowledgeStorageError
from llm_wiki_engine.knowledge_storage_io import StorageReadSession, read_guarded
from llm_wiki_engine.markdown_sections import normalize_markdown
from llm_wiki_engine.protected_artifacts import ProtectedArtifactStore
from llm_wiki_engine.sync_ownership import PageTransitionError
from llm_wiki_engine.validation import portable_path_key
from llm_wiki_engine.host import emit


@contextmanager
def preview_maintenance_preimages(
    live_wiki: Path, staged_wiki: Path, plan, *, max_bytes: int = MAX_EXPANDED_BYTES
) -> Iterator[dict[str, bytes]]:
    """Hold the verified prior owners' live Markdown stable while simulating their transfer.

    *plan* is the application's page transition plan. Each prior page is read
    from the live wiki and must match its staged copy; after the preview, every
    original is checked again, so a concurrent edit invalidates the preview.
    """
    preimages = {}
    commitments = {}
    prior_origins = set()
    with StorageReadSession(live_wiki, max_bytes=max_bytes).phase() as live:
        for item in plan.transitions:
            if item.previous_owner is None or item.previous_owner.scope != item.owner.scope:
                continue
            if item.old_path is None:
                if item.previous_owner != item.owner:
                    raise PageTransitionError(f"No recorded prior page for transfer from {item.previous_owner.source_path!r} to {item.final_path!r}")
                continue
            if item.previous_owner == item.owner and item.old_path == item.final_path:
                continue
            origin = portable_path_key(item.old_path)
            if origin in prior_origins:
                raise PageTransitionError(f"Multiple transitions claim the prior page {item.old_path!r}")
            prior_origins.add(origin)
            if item.source_path is None:
                raise PageTransitionError(f"Missing prior page {item.old_path!r} for {item.previous_owner.source_path!r}")
            try:
                original = live.read(item.source_path, MAX_EXPANDED_BYTES)
            except KnowledgeStorageError as exc:
                if exc.code == "storage-budget-exhausted" or (exc.code == "storage-limit" and exc.message == "file exceeds byte limit"):
                    raise PageTransitionError(f"Prior pages exceed the combined preview byte limit ({max_bytes}) at {item.old_path!r}") from exc
                raise PageTransitionError(f"Cannot read prior page {item.old_path!r} for {item.previous_owner.source_path!r}: {exc}") from exc
            digest = hashlib.sha256(original).digest()
            try:
                staged_digest, _ = _bounded_page_digest(staged_wiki / item.source_path, len(original))
            except KnowledgeStorageError as exc:
                raise PageTransitionError(f"Prior page changed while staging the preview: {item.source_path!r}") from exc
            if staged_digest != digest:
                raise PageTransitionError(f"Prior page changed while staging the preview: {item.source_path!r}")
            preimages[item.old_path] = original
            observed = live.observations[item.source_path]
            commitments[item.source_path] = (len(original), digest, (observed.identity, observed.directories))
        yield preimages
        # A phase can evict handles. Recheck every original, including evicted pages.
        for relative, (size, digest, identity) in commitments.items():
            try:
                current = _bounded_page_digest(live.root / relative, size)
            except KnowledgeStorageError as exc:
                raise KnowledgeStorageError(relative, "prior page changed during preview", code="storage-mutation") from exc
            if current != (digest, identity):
                raise KnowledgeStorageError(relative, "prior page changed during preview", code="storage-mutation")


def _bounded_page_digest(path: Path, size: int):
    """Hash a regular file at its expected size, holding at most one chunk and its identity."""
    result = hashlib.sha256()
    identity = None
    chunk_bytes = 64 * 1024
    for offset in range(0, max(1, size), chunk_bytes):
        length = min(chunk_bytes, size - offset)
        part = read_guarded(path, length, offset=offset, length=length, file_bytes=size)
        observed = (part.identity, part.directories)
        if identity is not None and observed != identity:
            raise KnowledgeStorageError(path.name, "prior page changed between bounded reads", code="storage-mutation")
        identity = observed
        result.update(part.content)
    return result.digest(), identity


RECOVERY_PREFIX = DEFAULT_LAYOUT.page_move_recovery_prefix


def assert_no_pending_page_moves(wiki_dir: Path) -> None:
    pending = sorted(wiki_dir.glob(f"{RECOVERY_PREFIX}*"))
    if pending:
        raise PageTransitionError(
            f"Unresolved page transition recovery data: {pending[0]}. "
            "Review recovery.json and resolve this recovery directory before retrying."
        )


def _decode(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("cp1252")
    return text.replace("\r\n", "\n").replace("\r", "\n")


class PageTransitionExecution:
    """Keep rename originals until the surrounding generation/commit succeeds.

    This is a bounded page-move recovery boundary, not a wiki transaction. On
    failure partial generated output is retained alongside durable originals;
    subsequent sync refuses to guess ownership from that partial state.
    """

    def __init__(self, wiki_dir: Path, plan: Any, *, preview: bool = False):
        self.root = StorageReadSession(wiki_dir).root
        self.plan = plan
        self.preview = preview
        self.by_path = {item.final_path: item for item in plan.transitions}
        self.retained_paths = {portable_path_key(item.path): item.path for item in plan.retained_page_repairs}
        self.expected: dict[str, bytes | None] = {}
        self.modes: dict[str, int] = {}
        self.recovery_dir: Path | None = None
        self.recovery_identity: tuple[int, int] | None = None
        self.recovery_files: dict[str, bytes] = {}
        self.originals: dict[str, bytes] = {}
        self.applied = False

    def __enter__(self):
        assert_no_pending_page_moves(self.root)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.recovery_dir is not None:
            if exc_type is None:
                try:
                    self._journal("committed")
                    self._cleanup()
                except (OSError, KnowledgeStorageError, PageTransitionError) as error:
                    emit(f"Page transition recovery data retained at {self.recovery_dir}", stream="stderr")
                    raise PageTransitionError(
                        f"Page transition completed, but recovery cleanup failed at {self.recovery_dir}: {error}"
                    ) from error
            elif self.preview:
                emit("Page transition preview failed; the original wiki was not modified.", stream="stderr")
            else:
                emit(
                    f"Page transition recovery data retained at {self.recovery_dir}",
                    stream="stderr",
                )
        return False

    def _journal(self, state: str) -> None:
        assert self.recovery_dir is not None
        content = (json.dumps({
            "version": 1,
            "state": state,
            "moves": [{
                "source": move.source_path,
                "destination": move.final_path,
                "backup": move.staging_slot,
                "sha256": hashlib.sha256(self.originals[move.source_path]).hexdigest(),
                "mode": self.modes[move.final_path],
            } for move in self.plan.staged_moves],
            "retained_pages": [{
                "source": repair.path,
                "backup": repair.staging_slot,
                "sha256": hashlib.sha256(self.originals[repair.path]).hexdigest(),
                "mode": self.modes[repair.path],
            } for repair in self.plan.retained_page_repairs],
        }, indent=2, sort_keys=True) + "\n").encode("utf-8")
        atomic_write_private_bytes(
            self.recovery_dir / "recovery.json", content,
            expected_existing=self.recovery_files.get("recovery.json"),
        )
        self.recovery_files["recovery.json"] = content

    def _verified_recovery_manifest(self):
        assert self.recovery_dir is not None
        metadata = self.recovery_dir.lstat()
        if (metadata.st_dev, metadata.st_ino) != self.recovery_identity:
            raise PageTransitionError(f"Recovery directory changed: {self.recovery_dir}")
        manifest = guarded_tree_manifest(self.recovery_dir)
        expected_hashes = {
            name: hashlib.sha256(content).hexdigest()
            for name, content in self.recovery_files.items()
        }
        if (
            any(not stat.S_ISREG(entry[1]) for entry in manifest)
            or {entry[0]: entry[6] for entry in manifest} != expected_hashes
        ):
            raise PageTransitionError(f"Recovery files changed; retained {self.recovery_dir}")
        return manifest

    def _cleanup(self) -> None:
        assert self.recovery_dir is not None
        manifest = self._verified_recovery_manifest()
        try:
            remove_guarded_tree(
                self.recovery_dir,
                expected_identity=self.recovery_identity,
                expected_manifest=manifest,
            )
        except OSError as exc:
            raise PageTransitionError(f"Could not remove committed recovery directory {self.recovery_dir}: {exc}") from exc

    def apply(self, current_plan: Any) -> None:
        if self.applied or current_plan != self.plan:
            raise PageTransitionError("Page transition plan changed or was applied twice")
        assert_no_pending_page_moves(self.root)
        try:
            # Capture every source, then persist every original, before removing
            # even the first original pathname or placing a destination.
            captured = StorageReadSession(self.root)
            with captured.phase():
                for move in self.plan.staged_moves:
                    self.originals[move.source_path] = captured.read(move.source_path, MAX_EXPANDED_BYTES)
                    observed = captured.observations[move.source_path]
                    self.modes[move.final_path] = stat.S_IMODE(observed.identity[2])
                for repair in self.plan.retained_page_repairs:
                    content = captured.read(repair.path, MAX_EXPANDED_BYTES)
                    if content != repair.expected_bytes:
                        raise PageTransitionError(f"Retained page changed before application: {repair.path}")
                    self.originals[repair.path] = content
                    self.expected[repair.path] = content
                    self.modes[repair.path] = stat.S_IMODE(captured.observations[repair.path].identity[2])
            if self.plan.staged_moves or self.plan.retained_page_repairs:
                store = ProtectedArtifactStore(
                    self.root / f"{RECOVERY_PREFIX}{uuid.uuid4().hex}", create=True
                )
                self.recovery_dir = store.root
                metadata = self.recovery_dir.lstat()
                self.recovery_identity = (metadata.st_dev, metadata.st_ino)
                self._journal("capturing")
                for move in self.plan.staged_moves:
                    data = self.originals[move.source_path]
                    atomic_write_private_bytes(
                        self.recovery_dir / move.staging_slot, data, expected_existing=None
                    )
                    self.recovery_files[move.staging_slot] = data
                for repair in self.plan.retained_page_repairs:
                    data = self.originals[repair.path]
                    atomic_write_private_bytes(
                        self.recovery_dir / repair.staging_slot, data, expected_existing=None
                    )
                    self.recovery_files[repair.staging_slot] = data
                self._journal("prepared")
                self._verified_recovery_manifest()
                for move in self.plan.staged_moves:
                    unlink_guarded_bytes(
                        self.root / move.source_path, expected=self.originals[move.source_path]
                    )
                for move in self.plan.staged_moves:
                    data = self.originals[move.source_path]
                    ensure_guarded_directory((self.root / move.final_path).parent)
                    atomic_write_guarded_bytes(
                        self.root / move.final_path, data,
                        mode=self.modes[move.final_path], expected_existing=None,
                    )
                    self.expected[move.final_path] = data
                    kind = "entity" if move.final_path.startswith("entities/") else "module"
                    emit(f"  RENAME {kind}: {Path(move.source_path).stem} -> {Path(move.final_path).stem}")
                self._journal("applied")
            self.applied = True
        except (OSError, KnowledgeStorageError) as exc:
            raise PageTransitionError(f"Cannot apply page transitions: {exc}") from exc

    def _expected(self, relative: str) -> bytes | None:
        if not self.applied:
            raise PageTransitionError("Page writes require completed rename staging")
        if relative not in self.expected:
            item = self.by_path[relative]
            if item.source_path is None:
                self.expected[relative] = None
            else:
                observed = read_guarded(self.root / relative, MAX_EXPANDED_BYTES)
                self.expected[relative] = observed.content
                self.modes[relative] = stat.S_IMODE(observed.identity[2])
        return self.expected[relative]

    def read_text(self, relative: str) -> str | None:
        try:
            content = self._expected(relative)
            if content is None:
                try:
                    (self.root / relative).lstat()
                except FileNotFoundError:
                    return None
                raise PageTransitionError(f"Unexpected page appeared during application: {relative}")
            if content is not None and read_guarded(self.root / relative, MAX_EXPANDED_BYTES).content != content:
                raise PageTransitionError(f"Page changed during application: {relative}")
            return _decode(content) if content is not None else None
        except (OSError, KnowledgeStorageError) as exc:
            raise PageTransitionError(f"Cannot read owned page {relative!r}: {exc}") from exc

    def write(self, relative: str, text: str) -> str:
        try:
            old = self._expected(relative)
            content = normalize_markdown(text)
            if old is not None and normalize_markdown(_decode(old)) == content:
                self.read_text(relative)
                return "unchanged"
            ensure_guarded_directory((self.root / relative).parent)
            data = content.encode("utf-8")
            atomic_write_guarded_bytes(
                self.root / relative, data, mode=self.modes.get(relative, 0o600),
                expected_existing=old,
            )
            self.expected[relative] = data
            return "created" if old is None else "updated"
        except (OSError, KnowledgeStorageError) as exc:
            raise PageTransitionError(f"Cannot write owned page {relative!r}: {exc}") from exc
