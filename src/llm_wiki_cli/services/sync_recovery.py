"""Explicit recovery of unchanged new Markdown pages from a rejected sync."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any
from uuid import UUID, uuid4

from .filesystem_guard import (
    atomic_write_guarded_bytes,
    ensure_guarded_directory,
    fresh_no_follow_stat,
    unlink_guarded_bytes,
)
from .io import first_unsafe_path_component
from .knowledge_storage import canonical_bytes, digest
from .knowledge_storage_io import _absolute_path, _identity, read_guarded
from .maintenance_protocol import governance_writer_lock, storage_writer_lock
from .request_json import _pairs, _constant
from .source_snapshot import SourceSnapshot
from .wiki_write_basis import ACTIVE_SYNC_JOURNAL

MAX_BYTES = 64 * 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_PAGES = 10_000
ANCHORS = (
    ".llm-wiki-manifest.json",
    ".llm-wiki-knowledge.json",
    ".llm-wiki-surface.json",
    ".llm-wiki-maintenance-adoption.json",
    ".llm-wiki-governance.json",
)
SCHEMA = "llm-wiki-sync-new-page-recovery/v1"


class SyncRecoveryError(ValueError):
    """A recovery proof or operation cannot be admitted safely."""


def _safe(path: Path) -> None:
    if first_unsafe_path_component(path) is not None:
        raise SyncRecoveryError(f"Sync recovery refuses unsafe path: {path}")


def _page(name: str) -> str:
    if not isinstance(name, str):
        raise SyncRecoveryError("Sync recovery page names must be strings")
    path = PurePosixPath(name)
    if (
        path.is_absolute()
        or str(path) != name
        or any(part in {".", ".."} or part.startswith(".") for part in path.parts)
        or "\\" in name
        or ":" in name
        or path.suffix != ".md"
    ):
        raise SyncRecoveryError(
            "Sync recovery requires a canonical relative Markdown path"
        )
    return name


def _authority(root: Path):
    result = {}
    for name in ANCHORS:
        path = root / name
        _safe(path)
        result[name] = read_guarded(path, MAX_BYTES) if path.exists() else None
    return result


def _anchors(root: Path) -> dict[str, str | None]:
    return {
        name: digest(row.content) if row is not None else None
        for name, row in _authority(root).items()
    }


def _root_identity(root: Path) -> list[int]:
    _safe(root)
    info = root.stat()
    if not root.is_dir():
        raise SyncRecoveryError("Sync recovery wiki must be an existing directory")
    return [info.st_dev, info.st_ino]


def _policy_inputs(snapshot: SourceSnapshot) -> dict[str, str | None]:
    paths = {
        snapshot.root / ".gitignore",
        snapshot.root
        / (snapshot.source_selection_path or ".llm-wiki/source-selection.json"),
    }
    paths.update(snapshot.root / name for name in snapshot.captured_gitignore_paths)
    paths.update(
        snapshot.root / name
        for name, kinds in snapshot.captured_input_kinds.items()
        if "selection" in kinds
    )
    result = {}
    for path in sorted(paths):
        relative = path.relative_to(snapshot.root).as_posix()
        expected = snapshot.captured_content_hashes.get(relative)
        current = (
            digest(read_guarded(path, MAX_FILE).content) if path.exists() else None
        )
        if (
            relative == ".gitignore"
            and not snapshot.respect_ignores
            and relative not in snapshot.captured_content_hashes
        ):
            expected = current  # Not an input to this explicitly unfiltered capture.
        if current != expected:
            raise SyncRecoveryError("Source selection changed before sync writes")
        result[str(path)] = expected
    return result


def _owned_pages(manifest) -> set[str]:
    """Missing pages with committed outgoing owners are never new-page writes."""
    if manifest is None:
        return {"index.md", "log.md"}
    return {
        "index.md",
        "log.md",
        *manifest.page_source_mappings,
        *manifest.evidence_baselines,
        *manifest.tombstones,
    }


@dataclass
class NewPageJournal:
    root: Path
    snapshot: SourceSnapshot
    manifest: Any = None
    before: set[str] = field(init=False)
    record: dict[str, Any] = field(init=False)
    directory: Path | None = None
    written_bytes: int = 0

    def __post_init__(self):
        self.before = {
            path.relative_to(self.root).as_posix() for path in self.root.rglob("*.md")
        } | _owned_pages(self.manifest)
        self.record = {
            "schema_version": SCHEMA,
            "transaction_id": str(uuid4()),
            "status": "writing",
            "wiki_root": str(self.root),
            "wiki_identity": _root_identity(self.root),
            "anchors": _anchors(self.root),
            "preexisting_pages": sorted(self.before),
            "source_paths": sorted(
                str(self.snapshot.root / name)
                for name in self.snapshot.selected_regular_paths
            ),
            "policy_inputs": _policy_inputs(self.snapshot),
            "pages": {},
        }

    def _persist(self):
        raw = canonical_bytes(self.record)
        if len(raw) > MAX_FILE:
            raise SyncRecoveryError("Sync recovery journal exceeds its byte bound")
        if self.directory is None:
            from .knowledge_governance import _governance_lock_root

            base = _governance_lock_root(self.root)
            if base == self.root:
                # Canonicalize the trusted OS temp directory (e.g. macOS /var),
                # then create a unique guarded operation directory beneath it.
                base = Path(tempfile.gettempdir()).resolve() / "llm-wiki-sync-recovery"
            self.directory = base / "sync-new-pages" / self.record["transaction_id"]
        assert self.directory is not None
        ensure_guarded_directory(self.directory, mode=0o700)
        path = self.directory / "sync-recovery.json"
        previous = read_guarded(path, MAX_FILE).content if path.exists() else None
        atomic_write_guarded_bytes(path, raw, expected_existing=previous)

    def before_write(self, path: Path, content: bytes | None):
        path = _absolute_path(path)
        if not path.is_relative_to(self.root) or path.suffix != ".md":
            return
        name = path.relative_to(self.root).as_posix()
        if name in self.before or content is None:
            return
        if any(
            len(self.record[key]) > MAX_PAGES
            for key in ("preexisting_pages", "source_paths", "policy_inputs")
        ):
            raise SyncRecoveryError(
                "Sync recovery baseline inventory exceeds its bound"
            )
        name = _page(name)
        if str(path) in self.record["source_paths"]:
            raise SyncRecoveryError("Sync recovery cannot record a source-owned page")
        rows = self.record["pages"].get(name, [])
        if path.exists() or path.is_symlink():
            current = read_guarded(path, MAX_FILE)
            if not any(
                row["identity"] == list(current.identity)
                and row["hash"] == digest(current.content)
                for row in rows
            ):
                raise SyncRecoveryError(
                    f"New sync page changed outside this operation: {name}"
                )
        if (
            len(content) > MAX_FILE
            or self.written_bytes + len(content) > MAX_BYTES
            or (
                len(self.record["pages"]) >= MAX_PAGES
                and name not in self.record["pages"]
            )
        ):
            raise SyncRecoveryError("Sync recovery postimages exceed their bound")
        self.written_bytes += len(content)
        rows = self.record["pages"].setdefault(name, [])
        rows.append({"hash": digest(content), "bytes": len(content), "identity": None})
        self._persist()
        assert self.directory is not None
        backup = self.directory / (rows[-1]["hash"][7:] + ".bin")
        if backup.exists():
            if read_guarded(backup, MAX_FILE).content != content:
                raise SyncRecoveryError("Sync recovery postimage collision")
        else:
            atomic_write_guarded_bytes(backup, content, expected_existing=None)

    def after_write(self, path: Path, content: bytes | None):
        path = _absolute_path(path)
        if not path.is_relative_to(self.root):
            return
        name = path.relative_to(self.root).as_posix()
        rows = self.record["pages"].get(name)
        if rows and content is not None:
            actual = read_guarded(path, MAX_FILE)
            if actual.content != content or rows[-1]["hash"] != digest(content):
                raise SyncRecoveryError("New sync page changed during publication")
            rows[-1]["identity"] = list(actual.identity)
            self._persist()

    def discard_committed(self):
        """Remove only this successful operation's verified private scratch."""
        assert self.directory is not None
        directory = self.directory
        identity = _root_identity(directory)
        expected = {"sync-recovery.json": canonical_bytes(self.record)}
        for rows in self.record["pages"].values():
            for row in rows:
                name = row["hash"][7:] + ".bin"
                raw = read_guarded(directory / name, MAX_FILE).content
                if len(raw) != row["bytes"] or digest(raw) != row["hash"]:
                    raise SyncRecoveryError("Committed sync scratch changed")
                expected[name] = raw
        if {path.name for path in directory.iterdir()} != set(expected):
            raise SyncRecoveryError("Committed sync scratch contains unrelated entries")
        for name, raw in expected.items():
            if read_guarded(directory / name, MAX_FILE).content != raw:
                raise SyncRecoveryError("Committed sync scratch changed")
        # Keep the committed marker until all postimages have been removed.
        for name in [
            *sorted(set(expected) - {"sync-recovery.json"}),
            "sync-recovery.json",
        ]:
            if _root_identity(directory) != identity:
                raise SyncRecoveryError("Committed sync scratch directory changed")
            unlink_guarded_bytes(directory / name, expected=expected[name])
        if _root_identity(directory) != identity:
            raise SyncRecoveryError("Committed sync scratch directory changed")
        directory.rmdir()  # Never recursively remove an unexpected entry.


@contextmanager
def capture_new_sync_pages(wiki_dir, snapshot, manifest=None):
    """Retain rejected writes; never repair them implicitly."""
    journal = NewPageJournal(_absolute_path(wiki_dir), snapshot, manifest)
    token = ACTIVE_SYNC_JOURNAL.set(journal)
    try:
        yield
    except BaseException:
        if journal.record["pages"]:
            journal.record["status"] = "rejected"
            try:
                journal._persist()
                assert journal.directory is not None
                expected = digest(canonical_bytes(journal.record))
                print(
                    json.dumps(
                        {
                            "new_page_recovery": {
                                "recovery_dir": str(journal.directory),
                                "expected_journal_hash": expected,
                                "argv": [
                                    "llm-wiki",
                                    "maintenance",
                                    "recover-new-pages",
                                    "--wiki-dir",
                                    str(journal.root),
                                    "--recovery-dir",
                                    str(journal.directory),
                                    "--expected-journal-hash",
                                    expected,
                                    "--dry-run",
                                ],
                            }
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
            except (ValueError, OSError) as exc:
                print(f"New-page recovery journal unavailable: {exc}", file=sys.stderr)
        raise
    else:
        if journal.record["pages"]:
            journal.record["status"] = "committed"
            try:
                journal._persist()
                journal.discard_committed()
            except (ValueError, OSError) as exc:
                print(
                    f"Sync completed; private new-page scratch retained: {exc}",
                    file=sys.stderr,
                )
    finally:
        ACTIVE_SYNC_JOURNAL.reset(token)


def recover_new_sync_pages(
    wiki_dir, *, recovery_dir, expected_journal_hash, dry_run=False
):
    """Remove only unchanged transaction-created pages, preserving postimages."""
    root, directory = _absolute_path(wiki_dir), _absolute_path(recovery_dir)
    if type(dry_run) is not bool or directory == root or directory.is_relative_to(root):
        raise SyncRecoveryError(
            "Sync recovery requires a boolean dry-run and an external recovery directory"
        )
    raw = read_guarded(directory / "sync-recovery.json", MAX_FILE).content
    if (
        not isinstance(expected_journal_hash, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_journal_hash)
        or digest(raw) != expected_journal_hash
    ):
        raise SyncRecoveryError(
            "Sync recovery journal differs from the rejection-bound hash"
        )
    record = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    fields = {
        "schema_version",
        "transaction_id",
        "status",
        "wiki_root",
        "wiki_identity",
        "anchors",
        "preexisting_pages",
        "source_paths",
        "policy_inputs",
        "pages",
    }
    if (
        not isinstance(record, dict)
        or set(record) != fields
        or record["schema_version"] != SCHEMA
        or record["status"] != "rejected"
    ):
        raise SyncRecoveryError("Sync recovery requires a rejected transaction journal")
    if (
        not isinstance(record["wiki_identity"], list)
        or len(record["wiki_identity"]) != 2
        or any(type(value) is not int for value in record["wiki_identity"])
        or record["wiki_root"] != str(root)
        or record["wiki_identity"] != _root_identity(root)
    ):
        raise SyncRecoveryError("Sync recovery belongs to another wiki identity")
    if (
        not isinstance(record["pages"], dict)
        or not 1 <= len(record["pages"]) <= MAX_PAGES
    ):
        raise SyncRecoveryError("Sync recovery page inventory is invalid")
    if not isinstance(record["preexisting_pages"], list) or not isinstance(
        record["source_paths"], list
    ):
        raise SyncRecoveryError("Sync recovery baseline is invalid")
    try:
        transaction = UUID(record["transaction_id"])
        if transaction.version != 4 or str(transaction) != record["transaction_id"]:
            raise SyncRecoveryError("transaction identity is not canonical")
        for key in ("preexisting_pages", "source_paths"):
            values = record[key]
            if (
                len(values) > MAX_PAGES
                or any(not isinstance(value, str) for value in values)
                or len(set(values)) != len(values)
            ):
                raise SyncRecoveryError("baseline inventory is invalid")
        for rows in record["pages"].values():
            if not isinstance(rows, list) or not rows or len(rows) > MAX_PAGES:
                raise SyncRecoveryError("postimage inventory is invalid")
            for row in rows:
                if not isinstance(row, dict) or set(row) != {
                    "hash",
                    "bytes",
                    "identity",
                }:
                    raise SyncRecoveryError("postimage fields are invalid")
                if (
                    not isinstance(row["hash"], str)
                    or not re.fullmatch(r"sha256:[0-9a-f]{64}", row["hash"])
                    or type(row["bytes"]) is not int
                    or not 0 <= row["bytes"] <= MAX_FILE
                ):
                    raise SyncRecoveryError("postimage commitment is invalid")
                identity = row["identity"]
                if identity is not None and (
                    not isinstance(identity, list)
                    or len(identity) != 6
                    or any(type(value) is not int for value in identity)
                ):
                    raise SyncRecoveryError("postimage identity is invalid")
    except (ValueError, TypeError, AttributeError) as exc:
        raise SyncRecoveryError(f"Invalid sync recovery journal: {exc}") from exc
    with governance_writer_lock(root), storage_writer_lock(root):
        policy_inputs = record["policy_inputs"]
        if not isinstance(policy_inputs, dict) or len(policy_inputs) > MAX_PAGES:
            raise SyncRecoveryError("Sync recovery selection commitments are invalid")
        policy_observations = {}
        for name, expected in policy_inputs.items():
            policy = Path(name)
            if not policy.is_absolute():
                raise SyncRecoveryError(
                    "Sync recovery selection paths must be native absolute paths"
                )
            _safe(policy)
            observation = read_guarded(policy, MAX_FILE) if policy.exists() else None
            current = digest(observation.content) if observation is not None else None
            if current != expected:
                raise SyncRecoveryError(
                    "Source selection changed since the rejected sync"
                )
            policy_observations[policy] = observation
        authority = _authority(root)
        if {
            name: digest(row.content) if row is not None else None
            for name, row in authority.items()
        } != record["anchors"]:
            raise SyncRecoveryError(
                "Sync recovery cannot replace changed committed authority"
            )
        from .sync_manifest import SyncManifest

        manifest = (
            SyncManifest.load(root)
            if record["anchors"][".llm-wiki-manifest.json"] is not None
            else None
        )
        owned = _owned_pages(manifest)
        planned = []
        total = 0
        for name, rows in sorted(record["pages"].items()):
            name = _page(name)
            path = root / name
            _safe(path)
            if (
                name in record["preexisting_pages"]
                or name in owned
                or str(path) in record["source_paths"]
            ):
                raise SyncRecoveryError(
                    "Sync recovery refuses preexisting or source-owned pages"
                )
            if (
                not isinstance(rows, list)
                or not rows
                or any(not isinstance(row, dict) for row in rows)
            ):
                raise SyncRecoveryError("Sync recovery postimage inventory is invalid")
            if not path.exists() and not any(
                row.get("identity") is not None for row in rows
            ):
                continue
            actual = read_guarded(path, MAX_FILE)
            total += len(actual.content)
            if total > MAX_BYTES:
                raise SyncRecoveryError(
                    "Sync recovery postimages exceed their byte bound"
                )
            if not any(
                row.get("identity") == list(actual.identity)
                and row.get("hash") == digest(actual.content)
                and row.get("bytes") == len(actual.content)
                for row in rows
            ):
                raise SyncRecoveryError(
                    f"Sync recovery refuses edited or replaced page: {name}"
                )
            backup = directory / (digest(actual.content)[7:] + ".bin")
            if read_guarded(backup, MAX_FILE).content != actual.content:
                raise SyncRecoveryError("Sync recovery postimage backup differs")
            planned.append((path, actual))
        if not dry_run:
            removed = 0
            try:
                for path, page_observation in planned:
                    if _root_identity(root) != record["wiki_identity"]:
                        raise SyncRecoveryError(
                            "Wiki identity changed during sync recovery"
                        )
                    # Check identities without repeatedly hashing large roots.
                    observations = {root / name: row for name, row in authority.items()}
                    observations.update(policy_observations)
                    for anchor, observation in observations.items():
                        _safe(anchor)
                        if observation is None:
                            if anchor.exists():
                                raise SyncRecoveryError(
                                    "Committed authority changed during sync recovery"
                                )
                        elif (
                            _identity(fresh_no_follow_stat(anchor))
                            != observation.identity
                        ):
                            raise SyncRecoveryError(
                                "Committed authority changed during sync recovery"
                            )
                    _safe(path)
                    metadata = fresh_no_follow_stat(path)
                    if (
                        metadata.st_nlink != 1
                        or _identity(metadata) != page_observation.identity
                    ):
                        raise SyncRecoveryError(
                            "New page changed after recovery preflight"
                        )
                    unlink_guarded_bytes(path, expected=page_observation.content)
                    removed += 1
                if _anchors(root) != record["anchors"]:
                    raise SyncRecoveryError(
                        "Committed authority changed during sync recovery"
                    )
            except (OSError, ValueError) as exc:
                raise SyncRecoveryError(
                    f"Recovery stopped after {removed} page(s); postimages remain at {directory}: {exc}"
                ) from exc
        return {
            "schema_version": SCHEMA,
            "ok": True,
            "dry_run": dry_run,
            "transaction_id": record["transaction_id"],
            "pages": [p.relative_to(root).as_posix() for p, _ in planned],
            "recovery_dir": str(directory),
            "retry_requires_sync": True,
            "atomic": False,
            "whole_snapshot_validated": False,
            "qualification": "Only unchanged new pages are removed; existing prose and committed authority are not restored. Postimages remain in the recovery directory.",
        }
