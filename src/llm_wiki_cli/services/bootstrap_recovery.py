"""Recover only journaled first-use output before capturing fresh evidence."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path, PurePosixPath
import re
from uuid import uuid4

from .filesystem_guard import (
    atomic_write_guarded_bytes,
    ensure_guarded_directory,
    remove_guarded_tree,
    unlink_guarded_bytes,
)
from .knowledge_governance import _governance_lock_root
from .knowledge_storage import MAX_EXPANDED_BYTES, canonical_bytes, digest
from .knowledge_storage_io import _absolute_path, read_guarded
from .maintenance_protocol import (
    MaintenanceProtocolError,
    WikiWriteBasis,
    governance_writer_lock,
    storage_writer_lock,
    guard_maintenance_owner,
    save_recovery_snapshot,
    snapshot_wiki,
)
from .request_json import _pairs, _constant
from .validation import is_portable_relative_path
from .wiki_write_basis import ACTIVE_BOOTSTRAP_JOURNAL

SCHEMA = "llm-wiki-bootstrap-recovery/v1"
MAX_RECORD_BYTES = 8 * 1024 * 1024
LOCK_FILES = {"llm-wiki-governance.lock", "llm-wiki-storage.lock"}


def _record_path(root: Path) -> Path:
    lock_root = _governance_lock_root(root)
    parent = lock_root if lock_root != root else root.parent / ".llm-wiki"
    if parent == root:
        parent = root.parent / ".llm-wiki-bootstrap-recovery"
    return (
        parent / "bootstrap-recovery" / digest(str(root).encode())[7:] / "active.json"
    )


def _json(raw: bytes):
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)


def _invalid(message: str) -> MaintenanceProtocolError:
    return MaintenanceProtocolError("bootstrap-recovery-invalid", message)


def _load_record(root: Path):
    path = _record_path(root)
    if not path.exists() and not path.is_symlink():
        return None
    try:
        raw = read_guarded(path, MAX_RECORD_BYTES).content
        record = _json(raw)
        if (
            not isinstance(record, dict)
            or set(record)
            != {
                "schema_version",
                "wiki_root",
                "operation_id",
                "status",
                "metadata_hash",
                "directories",
            }
            or record["schema_version"] != SCHEMA
            or record["wiki_root"] != str(root)
            or record["status"] not in {"writing", "complete", "restored", "abandoned"}
            or not isinstance(record["operation_id"], str)
            or re.fullmatch(r"[0-9a-f]{32}", record["operation_id"]) is None
            or not isinstance(record["directories"], list)
            or any(not _safe_name(name) for name in record["directories"])
            or raw != canonical_bytes(record)
        ):
            raise _invalid(
                "Bootstrap recovery record is invalid; preserve it and the wiki for inspection"
            )
        return record
    except (OSError, ValueError, TypeError) as exc:
        raise _invalid(f"Cannot validate bootstrap recovery record: {exc}") from exc


def pending_bootstrap(wiki_dir: str | Path) -> bool:
    record = _load_record(_absolute_path(Path(wiki_dir)))
    return record is not None and record["status"] == "writing"


def guard_incomplete_bootstrap(root: Path) -> None:
    active = ACTIVE_BOOTSTRAP_JOURNAL.get()
    if active is not None and active.root == root:
        return
    if pending_bootstrap(root):
        raise MaintenanceProtocolError(
            "bootstrap-incomplete",
            "Interrupted bootstrap requires retrying the same bootstrap command. "
            "Only unchanged journaled output can be recovered; preserve any user edits. "
            "Sync cannot establish the missing bootstrap evidence.",
        )


def _safe_name(name) -> bool:
    return (
        isinstance(name, str)
        and is_portable_relative_path(name)
        and name not in LOCK_FILES
    )


def _directories(root: Path) -> set[str]:
    # snapshot_wiki validates every descendant before this enumeration.
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_dir()}


def _save_record(root: Path, record: dict) -> None:
    path = _record_path(root)
    prior = read_guarded(path, MAX_RECORD_BYTES).content if path.exists() else None
    atomic_write_guarded_bytes(path, canonical_bytes(record), expected_existing=prior)


def _complete(root: Path, record: dict, *, status="complete") -> None:
    _save_record(root, {**record, "status": status})


def _recovery_inputs(root: Path, record: dict):
    directory = _record_path(root).parent / record["operation_id"]
    raw = read_guarded(
        directory / "maintenance-recovery.json", MAX_RECORD_BYTES
    ).content
    metadata = _json(raw)
    if (
        digest(raw) != record["metadata_hash"]
        or not isinstance(metadata, dict)
        or set(metadata) != {"schema_version", "marker", "kind", "files"}
        or metadata["schema_version"] != "llm-wiki-maintenance-recovery/v1"
        or metadata["marker"] is not None
        or metadata["kind"] != "bootstrap-preimage"
        or not isinstance(metadata["files"], dict)
        or len(metadata["files"]) > 100_000
    ):
        raise _invalid("Bootstrap preimage does not match its operation")
    files = {}
    for name, info in metadata["files"].items():
        if (
            not _safe_name(name)
            or not isinstance(info, dict)
            or set(info) != {"hash", "bytes"}
            or type(info["bytes"]) is not int
            or not 0 <= info["bytes"] <= MAX_EXPANDED_BYTES
        ):
            raise _invalid("Invalid bootstrap preimage file")
        content = read_guarded(directory / name, max(1, info["bytes"])).content
        if len(content) != info["bytes"] or digest(content) != info["hash"]:
            raise _invalid("Bootstrap preimage bytes changed")
        files[name] = content
    # A first-use journal can never restore an adopted or established owner.
    if any(
        name.startswith(
            (
                ".llm-wiki-manifest",
                ".llm-wiki-maintenance",
                ".llm-wiki-knowledge",
                ".llm-wiki-governance",
            )
        )
        for name in files
    ):
        raise _invalid("Bootstrap recovery cannot reconstruct existing authority")
    eligible = {name: [digest(content)] for name, content in files.items()}
    journal_path = directory / "publication-journal.json"
    if journal_path.exists() or journal_path.is_symlink():
        journal = _json(read_guarded(journal_path, MAX_EXPANDED_BYTES).content)
        if (
            not isinstance(journal, dict)
            or set(journal)
            != {"schema_version", "preimage_metadata_hash", "eligible_images"}
            or journal["schema_version"] != "llm-wiki-maintenance-publication/v1"
            or journal["preimage_metadata_hash"] != digest(raw)
            or not isinstance(journal["eligible_images"], dict)
        ):
            raise _invalid("Invalid bootstrap publication journal")
        for name, images in journal["eligible_images"].items():
            if (
                not _safe_name(name)
                or not isinstance(images, list)
                or not images
                or images[0] != (digest(files[name]) if name in files else None)
                or any(
                    value is not None
                    and (
                        not isinstance(value, str)
                        or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
                    )
                    for value in images
                )
            ):
                raise _invalid("Invalid bootstrap publication images")
            eligible[name] = images
    return files, eligible


def _recover(root: Path, record: dict) -> None:
    """Validate the entire tree before restoring with exact-byte comparisons."""
    try:
        files, eligible = _recovery_inputs(root, record)
        from .wiki_lifecycle import is_pristine_wiki_target

        if is_pristine_wiki_target(root):
            # The user may have preserved the entire incomplete tree elsewhere.
            # A fresh target needs no recovery writes or inherited evidence.
            _complete(root, record, status="abandoned")
            return
        current = snapshot_wiki(root, include_transient=True)
        for name in set(current) | set(eligible):
            observed = digest(current[name]) if name in current else None
            if name not in eligible or observed not in eligible[name]:
                raise MaintenanceProtocolError(
                    "bootstrap-recovery-conflict",
                    f"Bootstrap recovery refuses changed or unrelated file: {name}. "
                    "No files were changed. Preserve the incomplete wiki and its edits "
                    "outside the configured wiki path before starting a new bootstrap.",
                )
        old_directories = set(record["directories"])
        allowed_directories = old_directories | {
            str(parent)
            for name in eligible
            for parent in PurePosixPath(name).parents
            if str(parent) != "."
        }
        directories = _directories(root)
        if directories - allowed_directories:
            raise MaintenanceProtocolError(
                "bootstrap-recovery-conflict",
                "Bootstrap recovery refuses unrelated directories; preserve the wiki and its edits",
            )
        # Existing bytes are never replaced merely because their names look generated.
        for name in sorted(set(current) | set(files)):
            before, after = current.get(name), files.get(name)
            if before == after:
                continue
            path = root / name
            if after is None:
                assert before is not None
                unlink_guarded_bytes(path, expected=before)
            else:
                ensure_guarded_directory(path.parent)
                atomic_write_guarded_bytes(path, after, expected_existing=before)
        for name in sorted(
            directories - old_directories,
            key=lambda value: len(PurePosixPath(value).parts),
            reverse=True,
        ):
            remove_guarded_tree(root / name, expected_manifest=())
        if snapshot_wiki(root, include_transient=True) != files:
            raise MaintenanceProtocolError(
                "bootstrap-recovery-conflict",
                "Wiki changed during bootstrap recovery; preserve the remaining journal and edits",
            )
        _complete(root, record, status="restored")
    except MaintenanceProtocolError:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise _invalid(f"Bootstrap recovery remains incomplete: {exc}") from exc


@contextmanager
def bootstrap_write_operation(wiki_dir: str | Path, *, preflight):
    """Lock before mutation and retain first-use preimages across interruption."""
    root = _absolute_path(Path(wiki_dir))
    with governance_writer_lock(root), storage_writer_lock(root):
        record = _load_record(root)
        if record is not None and record["status"] == "writing":
            _recover(root, record)
        guard_maintenance_owner(root)
        preflight()
        files = snapshot_wiki(root, include_transient=True)
        operation_id = uuid4().hex
        directory = _record_path(root).parent / operation_id
        metadata = save_recovery_snapshot(
            directory, files, marker=None, kind="bootstrap-preimage"
        )
        record = {
            "schema_version": SCHEMA,
            "wiki_root": str(root),
            "operation_id": operation_id,
            "status": "writing",
            "metadata_hash": digest(canonical_bytes(metadata)),
            "directories": sorted(_directories(root)),
        }
        _save_record(root, record)
        basis = WikiWriteBasis(
            root, dict(files), recovery_directory=directory, include_transient=True
        )
        token = ACTIVE_BOOTSTRAP_JOURNAL.set(basis)
        try:
            yield basis
            basis.assert_current()
            _complete(root, record)
        finally:
            ACTIVE_BOOTSTRAP_JOURNAL.reset(token)
