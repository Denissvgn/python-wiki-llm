"""Complete maintenance recovery catalogs backed by immutable deduplicated bytes."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
import json
from pathlib import Path
import re
import time

from .filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory, fresh_no_follow_stat, remove_guarded_tree, unlink_guarded_bytes
from .knowledge_storage import MAX_EXPANDED_BYTES, canonical_bytes, digest
from .knowledge_storage_io import _absolute_path, read_guarded
from .validation import is_portable_relative_path

CATALOG_SCHEMA = "llm-wiki-maintenance-recovery/v2"
CATALOG_FILENAME = "maintenance-recovery.json"
COMPLETION_FILENAME = "maintenance-completion.json"
_COMPLETION_SCHEMA = "llm-wiki-maintenance-completion/v1"
_SHARED_STORE = "managed-sibling/v1"
_LOCAL_STORE = "local/v1"
_HEX = re.compile(r"^[0-9a-f]{64}$")
_MAX_CATALOG_BYTES = 8_388_608
_MAX_SCAN_BYTES = 64 * 1024 * 1024
_MAX_FILES = 100_000
_SIDECARS = {CATALOG_FILENAME, COMPLETION_FILENAME, "publication-journal.json"}
_LOCK_FILENAME = "maintenance-recovery.lock"


def _portable_name(value):
    return is_portable_relative_path(value)


def _invalid(message):
    from .maintenance_protocol import MaintenanceProtocolError

    return MaintenanceProtocolError("recovery-invalid", message)


def _owner(owner_root, marker):
    from .maintenance_state import validate_maintenance_adoption

    parsed = validate_maintenance_adoption(marker)
    return {"wiki_root": str(_absolute_path(Path(owner_root))), "adoption_id": parsed["adoption_id"]}


def recovery_catalog_key(owner_root, marker, file_hashes: Mapping[str, str]) -> str:
    """Bind managed directory identity to exact bytes and one wiki/adoption."""
    return digest(canonical_bytes({"owner": _owner(owner_root, marker), "files": dict(file_hashes)}))[7:]


def _managed_store(root: Path) -> Path | None:
    candidate = root.parent if root.name == "committed" else root
    if _HEX.fullmatch(candidate.name) and candidate.parent.name == "maintenance-preimages":
        return candidate.parent
    return None


@contextmanager
def _store_lock(store):
    from .knowledge_governance import governance_lock

    with governance_lock(store, _lock_filename=_LOCK_FILENAME):
        yield


def _blob_path(root: Path, metadata, logical_hash: str) -> Path:
    if not isinstance(logical_hash, str) or not logical_hash.startswith("sha256:") or not _HEX.fullmatch(logical_hash[7:]):
        raise _invalid("Recovery blob hash is not canonical")
    if metadata["blob_store"] == _SHARED_STORE:
        parent = _managed_store(root)
        if parent is None:
            raise _invalid("Managed recovery catalog is outside its fixed storage layout")
    elif metadata["blob_store"] == _LOCAL_STORE:
        parent = root
    else:
        raise _invalid("Unknown recovery blob storage mode")
    return parent / ".objects" / logical_hash[7:9] / (logical_hash[7:] + ".blob")


def _read_json(path: Path, maximum=_MAX_CATALOG_BYTES):
    from .request_json import _pairs, _constant

    raw = read_guarded(path, maximum).content
    return raw, json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)


def _validate_catalog(metadata):
    from .maintenance_state import validate_maintenance_adoption

    if (not isinstance(metadata, dict)
            or set(metadata) != {"schema_version", "marker", "kind", "files", "owner", "blob_store"}
            or metadata["schema_version"] != CATALOG_SCHEMA
            or metadata["kind"] not in {"committed", "captured-preimage", "prepared-adoption"}
            or metadata["blob_store"] not in {_SHARED_STORE, _LOCAL_STORE}):
        raise _invalid("Unsupported complete maintenance recovery catalog")
    marker = validate_maintenance_adoption(metadata["marker"])
    owner = metadata["owner"]
    if (not isinstance(owner, dict) or set(owner) != {"wiki_root", "adoption_id"}
            or owner["adoption_id"] != marker["adoption_id"]
            or not isinstance(owner["wiki_root"], str)
            or not Path(owner["wiki_root"]).is_absolute()
            or str(Path(owner["wiki_root"])) != owner["wiki_root"]
            or ".." in Path(owner["wiki_root"]).parts):
        raise _invalid("Recovery catalog owner is not canonical")
    files = metadata["files"]
    if not isinstance(files, dict) or len(files) > _MAX_FILES:
        raise _invalid("Invalid recovery catalog inventory")
    for name, info in files.items():
        if (not _portable_name(name)
                or not isinstance(info, dict) or set(info) != {"hash", "bytes"}
                or type(info["bytes"]) is not int or not 0 <= info["bytes"] <= MAX_EXPANDED_BYTES
                or not isinstance(info["hash"], str) or not info["hash"].startswith("sha256:")
                or not _HEX.fullmatch(info["hash"][7:])):
            raise _invalid("Invalid recovery file commitment")
    return metadata


def _validate_layout(root, metadata):
    if metadata["blob_store"] == _SHARED_STORE:
        directory = root.parent if root.name == "committed" else root
        expected = recovery_catalog_key(metadata["owner"]["wiki_root"], metadata["marker"],
            {name: info["hash"] for name, info in metadata["files"].items()})
        if _managed_store(root) is None or directory.name != expected:
            raise _invalid("Recovery catalog directory differs from its owner and byte commitments")


def _immutable_write(path: Path, raw: bytes) -> None:
    ensure_guarded_directory(path.parent, mode=0o700)
    previous = read_guarded(path, max(1, len(raw))).content if path.exists() or path.is_symlink() else None
    if previous is not None:
        if previous != raw:
            raise _invalid("Recovery storage contains bytes different from its commitment")
        return
    try:
        atomic_write_guarded_bytes(path, raw, expected_existing=None)
    except (OSError, ValueError):
        # Another wiki may concurrently publish the same immutable blob.
        if read_guarded(path, max(1, len(raw))).content != raw:
            raise


def save_recovery_catalog(directory, files: Mapping[str, bytes], *, marker, kind="committed", owner_root):
    """Publish complete file commitments after all exact immutable blobs exist."""
    root = _absolute_path(Path(directory))
    with _store_lock(_managed_store(root) or root):
        return _save_recovery_catalog(root, files, marker=marker, kind=kind, owner_root=owner_root)


def _save_recovery_catalog(root, files, *, marker, kind, owner_root):
    ensure_guarded_directory(root, mode=0o700)
    metadata = {
        "schema_version": CATALOG_SCHEMA, "marker": marker, "kind": kind,
        "files": {}, "owner": _owner(owner_root, marker),
        "blob_store": _SHARED_STORE if _managed_store(root) is not None else _LOCAL_STORE,
    }
    if len(files) > _MAX_FILES:
        raise _invalid("Recovery file inventory exceeds its bound")
    for name in sorted(files):
        raw = files[name]
        if not _portable_name(name) or not isinstance(raw, bytes) or len(raw) > MAX_EXPANDED_BYTES:
            raise _invalid("Invalid recovery file")
        logical_hash = digest(raw)
        metadata["files"][name] = {"hash": logical_hash, "bytes": len(raw)}
        _immutable_write(_blob_path(root, metadata, logical_hash), raw)
    raw_metadata = canonical_bytes(_validate_catalog(metadata))
    _validate_layout(root, metadata)
    if len(raw_metadata) > _MAX_CATALOG_BYTES:
        raise _invalid("Recovery catalog exceeds its metadata bound")
    _immutable_write(root / CATALOG_FILENAME, raw_metadata)
    if kind == "captured-preimage":
        # Reusing a previous generation starts a new attempt. A failure must
        # never inherit the previous attempt's permission for retention.
        completion = root / COMPLETION_FILENAME
        if completion.exists() or completion.is_symlink():
            raw = read_guarded(completion, _MAX_CATALOG_BYTES).content
            unlink_guarded_bytes(completion, expected=raw)
    return metadata


def load_recovery_catalog(directory, metadata) -> dict[str, bytes]:
    """Verify complete exact bytes before the caller validates their semantics."""
    root = _absolute_path(Path(directory))
    with _store_lock(_managed_store(root) or root):
        return _load_recovery_catalog(root, metadata)


def _load_recovery_catalog(root, metadata):
    _validate_catalog(metadata)
    _validate_layout(root, metadata)
    files = {}
    for name, info in metadata["files"].items():
        content = read_guarded(_blob_path(root, metadata, info["hash"]), max(1, info["bytes"])).content
        if len(content) != info["bytes"] or digest(content) != info["hash"]:
            raise _invalid("Recovery blob differs from its file commitment")
        files[name] = content
    return files


def mark_recovery_complete(preimage_directory, committed_directory) -> None:
    """Positively mark one successfully verified managed publication."""
    preimage = _absolute_path(Path(preimage_directory))
    committed = _absolute_path(Path(committed_directory))
    store = _managed_store(preimage)
    if store is None or _managed_store(committed) != store:
        return  # Explicit/local recoveries never gain automatic retention.
    with _store_lock(store):
        _mark_recovery_complete(preimage, committed)


def _mark_recovery_complete(preimage_directory, committed_directory):
    observed = []
    for directory in (preimage_directory, committed_directory):
        root = _absolute_path(Path(directory))
        raw, metadata = _read_json(root / CATALOG_FILENAME)
        _validate_catalog(metadata)
        _validate_layout(root, metadata)
        if metadata["blob_store"] != _SHARED_STORE:
            return  # Explicit/local recoveries are never automatically retained.
        observed.append((root, raw, metadata))
    if observed[0][2]["owner"] != observed[1][2]["owner"]:
        raise _invalid("Completed recovery catalogs belong to different owners")
    completed_ns = time.time_ns()
    for root, raw, metadata in observed:
        path = root / COMPLETION_FILENAME
        completion = canonical_bytes({
            "schema_version": _COMPLETION_SCHEMA, "owner": metadata["owner"],
            "catalog_hash": digest(raw), "completed_ns": completed_ns,
        })
        previous = read_guarded(path, _MAX_CATALOG_BYTES).content if path.exists() or path.is_symlink() else None
        atomic_write_guarded_bytes(path, completion, expected_existing=previous)


def retain_recovery_catalogs(store, *, owner_root, marker, newest_committed, keep_successful=2):
    """Retire only positively completed catalogs in one exact owner namespace.

    Store-wide serialization protects blobs published before their catalog is
    committed. Unknown or damaged catalogs prevent blob collection entirely.
    """
    if type(keep_successful) is not int or not 1 <= keep_successful <= 100:
        raise ValueError("Recovery retention count must be between 1 and 100")
    root = _absolute_path(Path(store))
    with _store_lock(root):
        report = _retain_recovery_catalogs(root, owner_root=owner_root, marker=marker,
            newest_committed=newest_committed, keep_successful=keep_successful)
        report.update(_collect_recovery_blobs(root))
        return report


def _retain_recovery_catalogs(root, *, owner_root, marker, newest_committed, keep_successful):
    owner = _owner(owner_root, marker)
    newest = _absolute_path(Path(newest_committed))
    eligible = {"committed": [], "captured-preimage": []}
    skipped = removed = scanned_bytes = 0
    entries = sorted(root.iterdir())
    if len(entries) > _MAX_FILES:
        return {"removed_catalogs": 0, "skipped_catalogs": len(entries), "blob_gc": "deferred"}
    for entry in entries:
        if not _HEX.fullmatch(entry.name):
            continue
        for candidate in (entry, entry / "committed"):
            metadata_path = candidate / CATALOG_FILENAME
            if not metadata_path.exists() and not metadata_path.is_symlink():
                continue
            try:
                absolute = _absolute_path(candidate)
                raw, metadata = _read_json(metadata_path)
                scanned_bytes += len(raw)
                if scanned_bytes > _MAX_SCAN_BYTES:
                    return {"removed_catalogs": 0, "skipped_catalogs": len(entries), "blob_gc": "deferred"}
                _validate_catalog(metadata)
                _validate_layout(absolute, metadata)
                completion_raw, completion = _read_json(candidate / COMPLETION_FILENAME)
                if (metadata["blob_store"] != _SHARED_STORE or metadata["owner"] != owner
                        or metadata["kind"] not in eligible or not isinstance(completion, dict)
                        or set(completion) != {"schema_version", "owner", "catalog_hash", "completed_ns"}
                        or completion["schema_version"] != _COMPLETION_SCHEMA
                        or completion["owner"] != owner or completion["catalog_hash"] != digest(raw)
                        or type(completion["completed_ns"]) is not int or completion["completed_ns"] < 0
                        or any(p.name not in _SIDECARS | {"committed"} for p in candidate.iterdir())):
                    skipped += 1
                    continue
                eligible[metadata["kind"]].append((completion["completed_ns"], absolute, raw, completion_raw))
            except (ValueError, OSError, TypeError, KeyError):
                skipped += 1  # Failed/active, old or unrecognized recoveries stay pinned.
    retired = set()
    for candidates in eligible.values():
        candidates.sort(key=lambda row: (row[0], str(row[1])), reverse=True)
        for _completed, candidate, raw, completion_raw in candidates[keep_successful:]:
            if candidate == newest:
                continue
            journal = candidate / "publication-journal.json"
            if journal.exists() or journal.is_symlink():
                journal_raw = read_guarded(journal, MAX_EXPANDED_BYTES).content
                unlink_guarded_bytes(journal, expected=journal_raw)
            unlink_guarded_bytes(candidate / COMPLETION_FILENAME, expected=completion_raw)
            unlink_guarded_bytes(candidate / CATALOG_FILENAME, expected=raw)
            retired.add(candidate)
            if candidate.name == "committed":
                retired.add(candidate.parent)
            removed += 1
    for directory in sorted(retired, key=lambda path: len(path.parts), reverse=True):
        try:
            if not any(directory.iterdir()):
                metadata = fresh_no_follow_stat(directory)
                remove_guarded_tree(directory, expected_identity=(metadata.st_dev, metadata.st_ino), expected_manifest=())
        except (OSError, ValueError):
            pass  # A concurrent addition is preserved by exact empty-tree CAS.
    return {"removed_catalogs": removed, "skipped_catalogs": skipped, "blob_gc": "deferred"}


def collect_recovery_blobs(store):
    """Collect verified unreachable blobs under the shared writer barrier."""
    root = _absolute_path(Path(store))
    with _store_lock(root):
        return _collect_recovery_blobs(root)


def _shared_references(root):
    references = set()
    scanned_bytes = 0
    entries = sorted(root.iterdir())
    if len(entries) > _MAX_FILES:
        raise _invalid("Recovery catalog scan exceeds its directory bound")
    for entry in entries:
        if entry.name in {".objects", _LOCK_FILENAME}:
            continue
        if not _HEX.fullmatch(entry.name) or not _absolute_path(entry).is_dir():
            raise _invalid("Unrecognized recovery catalog storage entry")
        for candidate in (entry, entry / "committed"):
            if not candidate.exists() and not candidate.is_symlink():
                continue
            absolute = _absolute_path(candidate)
            if not absolute.is_dir():
                raise _invalid("Recovery catalog entry is not a directory")
            metadata_path = absolute / CATALOG_FILENAME
            if not metadata_path.exists() and not metadata_path.is_symlink():
                if any(child.name != "committed" for child in absolute.iterdir()):
                    raise _invalid("Incomplete recovery catalog prevents blob collection")
                continue
            raw, metadata = _read_json(metadata_path)
            scanned_bytes += len(raw)
            if scanned_bytes > _MAX_SCAN_BYTES:
                raise _invalid("Recovery catalog scan exceeds its byte bound")
            if isinstance(metadata, dict) and metadata.get("schema_version") == "llm-wiki-maintenance-recovery/v1":
                if set(metadata) != {"schema_version", "marker", "kind", "files"}:
                    raise _invalid("Unrecognized legacy recovery prevents blob collection")
                continue  # Complete v1 snapshots refer only to their own files.
            _validate_catalog(metadata)
            _validate_layout(absolute, metadata)
            if (raw != canonical_bytes(metadata) or metadata["blob_store"] != _SHARED_STORE
                    or _managed_store(absolute) != root
                    or any(child.name not in _SIDECARS | {"committed"} for child in absolute.iterdir())):
                raise _invalid("Unrecognized recovery catalog prevents blob collection")
            references.update(info["hash"] for info in metadata["files"].values())
            if len(references) > _MAX_FILES:
                raise _invalid("Recovery blob references exceed their bound")
    return references


def _collect_recovery_blobs(root):
    try:
        references = _shared_references(root)
        objects = root / ".objects"
        if not objects.exists() and not objects.is_symlink():
            return {"blob_gc": "complete", "removed_blobs": 0, "reclaimed_bytes": 0}
        objects = _absolute_path(objects)
        candidates = []
        visited = 0
        prefixes = sorted(objects.iterdir())
        if len(prefixes) > 256:
            raise _invalid("Recovery blob prefixes exceed their bound")
        for prefix in prefixes:
            if not re.fullmatch(r"[0-9a-f]{2}", prefix.name) or not _absolute_path(prefix).is_dir():
                raise _invalid("Unknown recovery blob prefix")
            for path in sorted(prefix.iterdir()):
                visited += 1
                if visited > _MAX_FILES:
                    raise _invalid("Recovery blob scan exceeds its bound")
                if (not path.name.endswith(".blob") or not _HEX.fullmatch(path.name[:-5])
                        or not path.name.startswith(prefix.name)):
                    raise _invalid("Unknown recovery blob storage entry")
                logical_hash = "sha256:" + path.name[:-5]
                if logical_hash not in references:
                    content = read_guarded(path, MAX_EXPANDED_BYTES).content
                    if digest(content) != logical_hash:
                        raise _invalid("Unreferenced recovery blob is not authentic")
                    candidates.append((path, len(content)))
    except (OSError, ValueError, TypeError, KeyError):
        return {"blob_gc": "incomplete", "removed_blobs": 0, "reclaimed_bytes": 0}
    removed = reclaimed = 0
    for path, size in candidates:
        try:
            content = read_guarded(path, max(1, size)).content
            if len(content) != size or digest(content) != "sha256:" + path.name[:-5]:
                raise _invalid("Recovery blob changed before collection")
            unlink_guarded_bytes(path, expected=content)
            removed += 1
            reclaimed += len(content)
        except (OSError, ValueError):
            return {"blob_gc": "incomplete", "removed_blobs": removed, "reclaimed_bytes": reclaimed}
    return {"blob_gc": "complete", "removed_blobs": removed, "reclaimed_bytes": reclaimed}
