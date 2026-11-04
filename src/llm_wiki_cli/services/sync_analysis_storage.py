"""Bounded content-addressed persistence for advisory sync analysis captures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .canonical_json import canonical_chunks
from .filesystem_guard import unlink_guarded_bytes
from .io import first_unsafe_path_component, write_bytes_atomic
from .knowledge_storage_io import read_guarded

SCHEMA = "llm-wiki-sync-analysis-storage/v1"
MAX_SHARD_BYTES = 4 * 1024 * 1024
MAX_NODES = 100_000
MAX_DEPTH = 32
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


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


def save(path: Path, payload, *, root_limit: int, total_limit: int, writer=write_bytes_atomic):
    """Publish all immutable shards before atomically replacing their catalog."""
    measured = measure(payload, total_limit)
    if measured is None:
        raise ValueError("sync analysis exceeds its aggregate byte limit")
    size, logical_hash = measured
    previous = _previous_shards(path, root_limit)
    if size <= root_limit:
        raw = _small_bytes(payload, root_limit)
        assert raw is not None
        writer(path, raw)
        _remove_superseded_shards(path, raw, previous, root_limit)
        return size
    directory = _objects(path)
    if first_unsafe_path_component(directory) is not None:
        raise OSError("redirected sync analysis object directory")
    directory.mkdir(parents=True, exist_ok=True)
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
            existing = read_guarded(target, MAX_SHARD_BYTES).content if target.exists() else None
            if existing != raw:
                writer(target, raw)
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
