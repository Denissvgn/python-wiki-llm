"""Bounded content-addressed persistence for advisory sync analysis captures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .canonical_json import canonical_chunks
from .filesystem_guard import (
    atomic_write_guarded_bytes, ensure_guarded_directory, fresh_no_follow_stat,
    remove_guarded_tree, unlink_guarded_bytes,
)
from .io import first_unsafe_path_component, write_bytes_atomic
from .knowledge_storage_io import read_guarded

SCHEMA = "llm-wiki-sync-analysis-storage/v1"
MAX_SHARD_BYTES = 4 * 1024 * 1024
MAX_NODES = 100_000
MAX_DEPTH = 32
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ATTEMPT_SCHEMA = "llm-wiki-sync-analysis-attempt/v1"
_ATTEMPT_OWNER = "owner.json"
_LOCK_FILENAME = "llm-wiki-sync-analysis.lock"


def measure(payload, maximum):
    """Hash the existing canonical encoding without allocating a whole capture."""
    size = 0
    hasher = hashlib.sha256()
    previous = None
    for chunk in canonical_chunks(payload, chunk_bytes=max(64, min(65_536, maximum + 1))):
        size += len(chunk)
        if size > maximum:
            return None
        if previous is not None:
            hasher.update(previous)
        previous = chunk
    assert previous is not None and previous.endswith(b"\n")
    hasher.update(previous[:-1])
    return size, "sha256:" + hasher.hexdigest()


def _small_bytes(value, maximum):
    chunks = []
    size = 0
    for chunk in canonical_chunks(value):
        size += len(chunk)
        if size > maximum:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _objects(path):
    return path.with_name(path.name + ".objects")


def _pending(path):
    return path.with_name(path.name + ".pending")


def _current_root(path, maximum):
    return read_guarded(path, maximum).content if path.exists() or path.is_symlink() else None


def _root_shards(raw):
    if raw is None:
        return set()
    value = json.loads(raw)
    if isinstance(value, dict) and value.get("schema_version") in (None, "llm-wiki-sync-analysis/v2"):
        return set()
    if (not isinstance(value, dict)
            or set(value) != {"schema_version", "payload_hash", "payload_bytes", "tree"}
            or value["schema_version"] != SCHEMA
            or not isinstance(value["payload_hash"], str) or not _HASH.fullmatch(value["payload_hash"])
            or type(value["payload_bytes"]) is not int or value["payload_bytes"] < 1):
        raise ValueError("unknown sync analysis catalog prevents attempt cleanup")
    pending = [(value["tree"], 0)]
    references = set()
    count = 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH or not isinstance(node, dict):
            raise ValueError("invalid sync analysis reference tree")
        if node.get("kind") == "value":
            logical_hash = node.get("hash")
            if (set(node) != {"kind", "hash", "bytes"}
                    or not isinstance(logical_hash, str) or not _HASH.fullmatch(logical_hash)
                    or type(node["bytes"]) is not int or not 1 <= node["bytes"] <= MAX_SHARD_BYTES):
                raise ValueError("invalid sync analysis reference")
            references.add(logical_hash)
        elif node.get("kind") in {"object", "array"}:
            items = node.get("items")
            expected = dict if node["kind"] == "object" else list
            if set(node) != {"kind", "items"} or not isinstance(items, expected):
                raise ValueError("invalid sync analysis reference container")
            pending.extend((child, depth + 1) for child in (items.values() if isinstance(items, dict) else items))
        else:
            raise ValueError("invalid sync analysis reference kind")
    return references


def _pending_records(path):
    directory = _pending(path)
    if not directory.exists() and not directory.is_symlink():
        return None
    if first_unsafe_path_component(directory) is not None or not directory.is_dir():
        raise ValueError("redirected sync analysis attempt journal")
    entries = sorted(directory.iterdir())
    if len(entries) > MAX_NODES + 1:
        raise ValueError("sync analysis attempt journal exceeds its entry limit")
    expected = _small_bytes({"schema_version": _ATTEMPT_SCHEMA, "cache_name": path.name}, 8192)
    if expected is None:
        raise ValueError("sync analysis attempt owner exceeds its byte limit")
    if read_guarded(directory / _ATTEMPT_OWNER, 8192).content != expected:
        raise ValueError("unrecognized sync analysis attempt owner")
    records = {}
    for entry in entries:
        if entry.name == _ATTEMPT_OWNER:
            continue
        logical_hash = "sha256:" + entry.stem
        if entry.suffix != ".json" or not _HASH.fullmatch(logical_hash):
            raise ValueError("unknown sync analysis attempt journal entry")
        raw = read_guarded(entry, 512).content
        info = json.loads(raw)
        if (not isinstance(info, dict) or set(info) != {"hash", "bytes"}
                or info["hash"] != logical_hash or type(info["bytes"]) is not int
                or not 1 <= info["bytes"] <= MAX_SHARD_BYTES or _small_bytes(info, 512) != raw):
            raise ValueError("invalid sync analysis attempt shard")
        records[logical_hash] = (info["bytes"], raw)
    return records


def _prepare_pending(path):
    directory = _pending(path)
    if directory.exists() or directory.is_symlink():
        # An empty directory may be the boundary immediately before its owner
        # marker was published. Existing unknown contents are never adopted.
        if first_unsafe_path_component(directory) is not None or not directory.is_dir():
            raise ValueError("redirected sync analysis attempt journal")
        if any(directory.iterdir()):
            records = _pending_records(path)
            if records is None:
                raise ValueError("sync analysis attempt journal changed")
            return records
    ensure_guarded_directory(directory, mode=0o700)
    raw = _small_bytes({"schema_version": _ATTEMPT_SCHEMA, "cache_name": path.name}, 8192)
    if raw is None:
        raise ValueError("sync analysis attempt owner exceeds its byte limit")
    atomic_write_guarded_bytes(directory / _ATTEMPT_OWNER, raw, expected_existing=None)
    return {}


def _record_pending(path, records, logical_hash, size):
    if logical_hash in records:
        if records[logical_hash][0] != size:
            raise ValueError("sync analysis attempt shard size changed")
        return
    if len(records) >= MAX_NODES:
        raise ValueError("sync analysis attempt journal exceeds its entry limit")
    raw = _small_bytes({"hash": logical_hash, "bytes": size}, 512)
    assert raw is not None
    atomic_write_guarded_bytes(_pending(path) / (logical_hash[7:] + ".json"), raw, expected_existing=None)
    records[logical_hash] = (size, raw)


def _recover_pending(path, root_limit):
    records = _pending_records(path)
    if records is None:
        return
    root_bytes = _current_root(path, root_limit)
    references = _root_shards(root_bytes)
    directory = _pending(path)
    for logical_hash, (size, descriptor) in records.items():
        if _current_root(path, root_limit) != root_bytes:
            return
        target = _objects(path) / (logical_hash[7:] + ".json")
        if logical_hash not in references and (target.exists() or target.is_symlink()):
            raw = read_guarded(target, size).content
            if len(raw) != size or "sha256:" + hashlib.sha256(raw).hexdigest() != logical_hash:
                continue  # Replaced/unknown bytes retain their ownership evidence.
            if _current_root(path, root_limit) != root_bytes:
                return
            unlink_guarded_bytes(target, expected=raw)
        unlink_guarded_bytes(directory / (logical_hash[7:] + ".json"), expected=descriptor)
    if any(entry.name != _ATTEMPT_OWNER for entry in directory.iterdir()):
        return
    owner = directory / _ATTEMPT_OWNER
    raw = read_guarded(owner, 8192).content
    unlink_guarded_bytes(owner, expected=raw)
    if not any(directory.iterdir()):
        identity = fresh_no_follow_stat(directory)
        remove_guarded_tree(directory, expected_identity=(identity.st_dev, identity.st_ino), expected_manifest=())


def _previous_shards(path, root_limit):
    if not _objects(path).exists():
        return set()
    try:
        value = json.loads(read_guarded(path, root_limit).content)
        if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
            return set()
        pending = [value["tree"]]
        result = set()
        count = 0
        while pending:
            node = pending.pop()
            count += 1
            if count > MAX_NODES or not isinstance(node, dict):
                return set()
            if node.get("kind") == "value":
                digest = node.get("hash")
                if not isinstance(digest, str) or not _HASH.fullmatch(digest):
                    return set()
                result.add(digest)
            elif node.get("kind") in {"object", "array"}:
                items = node.get("items")
                if not isinstance(items, (dict, list)):
                    return set()
                pending.extend(items.values() if isinstance(items, dict) else items)
            else:
                return set()
        return result
    except (OSError, ValueError, KeyError, RecursionError):
        return set()


def _remove_superseded_shards(path, published, references, root_limit):
    # Only the previous catalog's exact content-addressed files are owned here.
    # Missing cache objects can cause a safe miss for a concurrent older reader.
    for digest in sorted(references):
        try:
            if read_guarded(path, root_limit).content != published:
                return
            target = _objects(path) / (digest[7:] + ".json")
            raw = read_guarded(target, MAX_SHARD_BYTES).content
            if "sha256:" + hashlib.sha256(raw).hexdigest() == digest:
                unlink_guarded_bytes(target, expected=raw)
        except (OSError, ValueError):
            continue  # Preserve unknown/replaced files; cleanup is advisory.


def _journal_superseded(path, references, owned=None):
    if not references:
        return
    owned = _prepare_pending(path) if owned is None else owned
    for logical_hash in sorted(references):
        target = _objects(path) / (logical_hash[7:] + ".json")
        try:
            raw = read_guarded(target, MAX_SHARD_BYTES).content
        except (OSError, ValueError):
            continue
        if "sha256:" + hashlib.sha256(raw).hexdigest() == logical_hash:
            _record_pending(path, owned, logical_hash, len(raw))


def save(path: Path, payload, *, root_limit: int, total_limit: int, writer=write_bytes_atomic):
    """Publish all immutable shards before atomically replacing their catalog."""
    from .knowledge_governance import governance_lock

    with governance_lock(path.parent, _lock_filename=_LOCK_FILENAME):
        try:
            _recover_pending(path, root_limit)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            # Unknown roots/journals never authorize deletion. A subsequent
            # valid publication may still make a recognized journal collectible.
            pass
        try:
            result = _save_locked(path, payload, root_limit=root_limit, total_limit=total_limit, writer=writer)
        except BaseException:
            try:
                _recover_pending(path, root_limit)
            except (OSError, ValueError, TypeError, KeyError, RecursionError):
                pass  # Preserve the primary failure and pending ownership evidence.
            raise
        try:
            _recover_pending(path, root_limit)
        except (OSError, ValueError, TypeError, KeyError, RecursionError):
            pass  # Advisory cleanup never invalidates a published capture.
        return result


def _save_locked(path: Path, payload, *, root_limit: int, total_limit: int, writer):
    measured = measure(payload, total_limit)
    if measured is None:
        raise ValueError("sync analysis exceeds its aggregate byte limit")
    size, logical_hash = measured
    previous = _previous_shards(path, root_limit)
    if size <= root_limit:
        raw = _small_bytes(payload, root_limit)
        assert raw is not None
        _journal_superseded(path, previous)
        writer(path, raw)
        _remove_superseded_shards(path, raw, previous, root_limit)
        return size
    directory = _objects(path)
    if first_unsafe_path_component(directory) is not None:
        raise OSError("redirected sync analysis object directory")
    directory.mkdir(parents=True, exist_ok=True)
    owned = _prepare_pending(path)
    nodes = 0
    shard_bytes = 0
    references = set()

    def partition(value, depth=0):
        nonlocal nodes, shard_bytes
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError("sync analysis catalog exceeds its structural limits")
        raw = _small_bytes(value, MAX_SHARD_BYTES)
        if raw is not None:
            shard_bytes += len(raw)
            if shard_bytes > total_limit:
                raise ValueError("sync analysis shards exceed the aggregate byte limit")
            digest = "sha256:" + hashlib.sha256(raw).hexdigest()
            references.add(digest)
            target = directory / (digest[7:] + ".json")
            if first_unsafe_path_component(target) is not None:
                raise OSError("redirected sync analysis shard")
            existing = read_guarded(target, MAX_SHARD_BYTES).content if target.exists() or target.is_symlink() else None
            if existing is not None and existing != raw:
                raise ValueError("existing sync analysis shard differs from its hash")
            if existing is None:
                _record_pending(path, owned, digest, len(raw))
                atomic_write_guarded_bytes(target, raw, expected_existing=None)
            return {"kind": "value", "hash": digest, "bytes": len(raw)}
        if isinstance(value, dict):
            return {"kind": "object", "items": {key: partition(child, depth + 1)
                                                   for key, child in sorted(value.items())}}
        if isinstance(value, (list, tuple)):
            return {"kind": "array", "items": [partition(child, depth + 1) for child in value]}
        raise ValueError("one sync analysis scalar exceeds the shard byte limit")

    catalog = {"schema_version": SCHEMA, "payload_hash": logical_hash,
               "payload_bytes": size, "tree": partition(payload)}
    raw = _small_bytes(catalog, root_limit)
    if raw is None:
        raise ValueError("sync analysis catalog exceeds its byte limit")
    _journal_superseded(path, previous - references, owned)
    writer(path, raw)
    _remove_superseded_shards(path, raw, previous - references, root_limit)
    return size


def load(path: Path, *, root_limit: int, total_limit: int) -> Any:
    """Read legacy captures or verify every bounded subtree before reuse."""
    value = json.loads(read_guarded(path, root_limit).content)
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        return value
    if (set(value) != {"schema_version", "payload_hash", "payload_bytes", "tree"}
            or not isinstance(value["payload_hash"], str) or not _HASH.fullmatch(value["payload_hash"])
            or type(value["payload_bytes"]) is not int
            or not 1 <= value["payload_bytes"] <= total_limit):
        raise ValueError("invalid sync analysis catalog")
    nodes = 0
    advertised = 0

    def validate(node, depth=0):
        nonlocal nodes, advertised
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH or not isinstance(node, dict):
            raise ValueError("sync analysis catalog exceeds its structural limits")
        kind = node.get("kind")
        if kind == "value":
            if (set(node) != {"kind", "hash", "bytes"}
                    or not isinstance(node["hash"], str) or not _HASH.fullmatch(node["hash"])
                    or type(node["bytes"]) is not int or not 1 <= node["bytes"] <= MAX_SHARD_BYTES):
                raise ValueError("invalid sync analysis shard reference")
            advertised += node["bytes"]
            if advertised > total_limit:
                raise ValueError("sync analysis shards exceed the aggregate byte limit")
        elif kind in {"object", "array"}:
            items = node.get("items")
            expected = dict if kind == "object" else list
            if set(node) != {"kind", "items"} or not isinstance(items, expected):
                raise ValueError("invalid sync analysis catalog container")
            for child in items.values() if isinstance(items, dict) else items:
                validate(child, depth + 1)
        else:
            raise ValueError("invalid sync analysis catalog node")

    # Enforce all advertised limits before opening the first shard.
    validate(value["tree"])
    directory = _objects(path)

    def materialize(node):
        if node["kind"] == "value":
            raw = read_guarded(directory / (node["hash"][7:] + ".json"), node["bytes"]).content
            if len(raw) != node["bytes"] or "sha256:" + hashlib.sha256(raw).hexdigest() != node["hash"]:
                raise ValueError("sync analysis shard commitment differs")
            return json.loads(raw)
        items = node["items"]
        if node["kind"] == "object":
            return {key: materialize(child) for key, child in items.items()}
        return [materialize(child) for child in items]

    payload = materialize(value["tree"])
    if measure(payload, total_limit) != (value["payload_bytes"], value["payload_hash"]):
        raise ValueError("sync analysis catalog does not reconstruct its payload")
    return payload
