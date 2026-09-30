"""Guarded execution of source-page moves, with retained failure recovery data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import sys
import uuid

from .filesystem_guard import (
    atomic_write_guarded_bytes,
    atomic_write_private_bytes,
    ensure_guarded_directory,
    guarded_tree_manifest,
    remove_guarded_tree,
    unlink_guarded_bytes,
)
from .knowledge_storage import MAX_EXPANDED_BYTES, KnowledgeStorageError
from .knowledge_storage_io import StorageReadSession, read_guarded
from .markdown_sections import normalize_markdown
from .protected_artifacts import ProtectedArtifactStore
from .sync_transitions import PageTransitionError, PageTransitionPlan


RECOVERY_PREFIX = ".llm-wiki-page-moves-"


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

    def __init__(self, wiki_dir: Path, plan: PageTransitionPlan, *, preview: bool = False):
        self.root = StorageReadSession(wiki_dir).root
        self.plan = plan
        self.preview = preview
        self.by_path = {item.final_path: item for item in plan.transitions}
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
                    print(f"Page transition recovery data retained at {self.recovery_dir}", file=sys.stderr)
                    raise PageTransitionError(
                        f"Page transition completed, but recovery cleanup failed at {self.recovery_dir}: {error}"
                    ) from error
            elif self.preview:
                print("Page transition preview failed; the original wiki was not modified.", file=sys.stderr)
            else:
                print(
                    f"Page transition recovery data retained at {self.recovery_dir}",
                    file=sys.stderr,
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

    def apply(self, current_plan: PageTransitionPlan) -> None:
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
            if self.plan.staged_moves:
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
                    print(f"  RENAME {kind}: {Path(move.source_path).stem} -> {Path(move.final_path).stem}")
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
