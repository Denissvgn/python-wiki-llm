"""Bounded legacy and maintenance roots with immutable field catalogs.

Each catalog is a bounded tree of canonical JSON byte segments. Splitting by
bytes also bounds unusually large individual source records and policy values.
The full API reconstructs logical v5/v7; the selected header never validates
an unread maintenance ledger.
"""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from .canonical_json import canonical_chunks
from .immutable import freeze
from .knowledge_storage import (
    MAX_EXPANDED_BYTES, KnowledgeStorageError, canonical_bytes, decode_bytes,
    digest, logical_digest, _hash,
)
from .sync_manifest import ManifestArtifactHashes

VERSION = 6
MAINTENANCE_VERSION = 8
SUPPORTED_PAIRS = {(6, 5), (8, 7)}
MAINTENANCE_FIELDS = ("maintenance_state",)
MAINTENANCE_HEADER_FIELDS = {"adoption_id", "maintenance_state_hash"}
ROOT_LIMIT = 65_536
OBJECT_LIMIT = 65_536
INLINE_LIMIT = 8_192
DIRECTORY = ".llm-wiki-manifest/objects"
OBJECT_NAME = re.compile(r"\.llm-wiki-manifest/objects/([0-9a-f]{2})/\1[0-9a-f]{62}\.json\Z")
CATALOG_SCHEMA = "llm-wiki-manifest-catalog/v1"
FIELDS = ("sources", "surfaces", "generation_inputs", "page_source_mappings", "evidence_baselines", "tombstones")
Reader = Callable[[str, int], bytes]


def object_path(commitment: str) -> str:
    _hash(commitment, "manifest.catalog.hash")
    return f"{DIRECTORY}/{commitment[7:9]}/{commitment[7:]}.json"


def _descriptor(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"hash", "bytes", "expanded_bytes"}:
        raise KnowledgeStorageError("manifest.catalog", "invalid descriptor")
    _hash(value["hash"], "manifest.catalog.hash")
    if (type(value["bytes"]) is not int or not 0 < value["bytes"] <= OBJECT_LIMIT
            or type(value["expanded_bytes"]) is not int or not 0 < value["expanded_bytes"] <= MAX_EXPANDED_BYTES):
        raise KnowledgeStorageError("manifest.catalog", "invalid size", code="storage-limit")
    return value


def validate_catalog(raw: bytes) -> dict[str, Any]:
    node = decode_bytes(raw, limit=OBJECT_LIMIT, field="manifest.catalog")
    if canonical_bytes(node) != raw or node.get("schema_version") != CATALOG_SCHEMA:
        raise KnowledgeStorageError("manifest.catalog", "invalid canonical catalog")
    if node.get("kind") == "data":
        if set(node) != {"schema_version", "kind", "data"} or not isinstance(node["data"], str):
            raise KnowledgeStorageError("manifest.catalog", "invalid data segment")
        try:
            value = base64.b64decode(node["data"], validate=True)
        except ValueError as exc:
            raise KnowledgeStorageError("manifest.catalog", "invalid base64 segment") from exc
        if not value or len(value) > 32_768 or base64.b64encode(value).decode("ascii") != node["data"]:
            raise KnowledgeStorageError("manifest.catalog", "invalid segment size or encoding")
    elif node.get("kind") == "branch":
        if (set(node) != {"schema_version", "kind", "children"}
                or not isinstance(node["children"], list) or not 2 <= len(node["children"]) <= 128):
            raise KnowledgeStorageError("manifest.catalog", "invalid branch")
        for child in node["children"]:
            _descriptor(child)
    else:
        raise KnowledgeStorageError("manifest.catalog", "unknown node kind")
    return node


@dataclass(frozen=True)
class ManifestStore:
    root_bytes: bytes
    objects: Mapping[str, bytes]


def build_manifest_store(payload: Mapping[str, Any]) -> ManifestStore:
    logical_version = payload.get("version")
    if type(logical_version) is not int or logical_version not in {5, 7}:
        raise KnowledgeStorageError("manifest", "requires a complete v5 or v7 logical value")
    if logical_version == 7:
        from .sync_manifest import SyncManifest
        SyncManifest.from_payload(dict(payload))
    fields = (*FIELDS, *MAINTENANCE_FIELDS) if logical_version == 7 else FIELDS
    objects: dict[str, bytes] = {}
    encoded_size = 0

    def put(node: dict[str, Any], size: int) -> dict[str, Any]:
        nonlocal encoded_size
        raw = canonical_bytes({"schema_version": CATALOG_SCHEMA, **node})
        if len(raw) > OBJECT_LIMIT or size > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("manifest.catalog", "catalog exceeds its limit", code="storage-limit")
        commitment = digest(raw)
        name = object_path(commitment)
        if name not in objects:
            encoded_size += len(raw)
            if encoded_size > MAX_EXPANDED_BYTES or len(objects) >= 100_000:
                raise KnowledgeStorageError("manifest.catalog", "aggregate catalog limit exceeded", code="storage-limit")
            objects[name] = raw
        return {"hash": commitment, "bytes": len(raw), "expanded_bytes": size}

    def catalog(value: object) -> dict[str, Any]:
        leaves = [put({"kind": "data", "data": base64.b64encode(part).decode("ascii")}, len(part))
                  for part in canonical_chunks(value, chunk_bytes=32_768)]
        if sum(d["expanded_bytes"] for d in leaves) > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("manifest.catalog", "expanded field exceeds limit", code="storage-limit")
        while len(leaves) > 1:
            following = []
            for i in range(0, len(leaves), 128):
                group = leaves[i:i + 128]
                following.append(group[0] if len(group) == 1 else
                                 put({"kind": "branch", "children": group}, sum(d["expanded_bytes"] for d in group)))
            leaves = following
        return leaves[0]

    header: dict[str, Any] = ({name: payload[name] for name in MAINTENANCE_HEADER_FIELDS} if logical_version == 7 else {})
    catalogs = {}
    expanded_size = 0
    for name in fields:
        value = payload[name]
        # Policy and surface configuration are usually small. Large policy is
        # committed separately and charged to the selected request's budget.
        if name in {"generation_inputs", "surfaces"}:
            parts = iter(canonical_chunks(value, chunk_bytes=INLINE_LIMIT))
            first = next(parts)
            if next(parts, None) is None and len(first) <= INLINE_LIMIT:
                header[name] = value
                continue
        catalogs[name] = catalog(value)
        expanded_size += catalogs[name]["expanded_bytes"]
        if expanded_size > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("manifest", "expanded catalogs exceed aggregate limit", code="storage-limit")
    root = {"version": MAINTENANCE_VERSION if logical_version == 7 else VERSION, "logical_version": logical_version, "logical_hash": logical_digest(payload),
            "header": header, "catalogs": catalogs}
    if "artifact_hashes" in payload:
        root["artifact_hashes"] = payload["artifact_hashes"]
    raw = canonical_bytes(root)
    if len(raw) > ROOT_LIMIT:
        raise KnowledgeStorageError("manifest", "commit root exceeds its limit", code="storage-limit")
    return ManifestStore(raw, freeze(objects))


class ManifestStoreReader:
    def __init__(self, root: Mapping[str, Any], read: Reader):
        required = {"version", "logical_version", "logical_hash", "header", "catalogs"}
        if (not required <= set(root) <= required | {"artifact_hashes"}
                or type(root.get("version")) is not int or type(root.get("logical_version")) is not int
                or (root.get("version"), root.get("logical_version")) not in SUPPORTED_PAIRS
                or len(canonical_bytes(root)) > ROOT_LIMIT):
            raise KnowledgeStorageError("manifest", "invalid indexed commit root")
        _hash(root["logical_hash"], "manifest.logical_hash")
        header, catalogs = root["header"], root["catalogs"]
        fields = set(FIELDS) | (set(MAINTENANCE_FIELDS) if root["logical_version"] == 7 else set())
        metadata = MAINTENANCE_HEADER_FIELDS if root["logical_version"] == 7 else set()
        if root["logical_version"] == 7:
            from .maintenance_state import validate_maintenance_adoption
            if not isinstance(header, dict) or not metadata <= set(header):
                raise KnowledgeStorageError("manifest.header", "adopted header commitments are missing")
            validate_maintenance_adoption({
                "schema_version": "llm-wiki-maintenance-adoption/v1",
                "adoption_id": header["adoption_id"],
                "min_manifest_version": 7,
                "features": {"implementation_evidence": 1, "maintenance_state": 1, "ordinary_acknowledgment": 1},
            })
            _hash(header["maintenance_state_hash"], "manifest.header.maintenance_state_hash")
        if (not isinstance(header, dict) or not isinstance(catalogs, dict)
                or set(header) - ({"generation_inputs", "surfaces"} | metadata)
                or set(header) & set(catalogs) or (set(header) - metadata) | set(catalogs) != fields):
            raise KnowledgeStorageError("manifest", "invalid header or field catalog")
        for name, value in header.items():
            if name in metadata:
                continue
            if not isinstance(value, dict) or len(canonical_bytes(value)) > INLINE_LIMIT:
                raise KnowledgeStorageError("manifest.header", "invalid inline field")
        for value in catalogs.values():
            _descriptor(value)
        if root["logical_version"] == 7:
            from .maintenance_state import LIMITS
            if catalogs["maintenance_state"]["expanded_bytes"] > LIMITS["state_bytes"]:
                raise KnowledgeStorageError("manifest.maintenance_state", "declared state expansion exceeds 64 MiB", code="storage-limit")
        if sum(d["expanded_bytes"] for d in catalogs.values()) > MAX_EXPANDED_BYTES:
            raise KnowledgeStorageError("manifest", "expanded catalogs exceed aggregate limit", code="storage-limit")
        self.root, self.read = root, read
        self.objects: dict[str, bytes] = {}
        self.nodes = 0

    def _chunks(self, desc: dict[str, Any], depth: int = 0):
        self.nodes += 1
        if depth > 8 or self.nodes > 100_000:
            raise KnowledgeStorageError("manifest.catalog", "tree exceeds limits", code="storage-limit")
        path = object_path(desc["hash"])
        raw = self.objects.get(path)
        if raw is None:
            raw = self.read(path, desc["bytes"])
            if len(raw) != desc["bytes"] or digest(raw) != desc["hash"]:
                raise KnowledgeStorageError(path, "catalog commitment mismatch")
            self.objects[path] = raw
        if len(raw) != desc["bytes"]:
            raise KnowledgeStorageError(path, "inconsistent catalog size commitment")
        node = validate_catalog(raw)
        if node["kind"] == "data":
            value = base64.b64decode(node["data"], validate=True)
            if len(value) != desc["expanded_bytes"]:
                raise KnowledgeStorageError(path, "segment size mismatch")
            yield value
        else:
            if sum(d["expanded_bytes"] for d in node["children"]) != desc["expanded_bytes"]:
                raise KnowledgeStorageError(path, "branch expansion mismatch")
            for child in node["children"]:
                yield from self._chunks(child, depth + 1)

    def field(self, name: str) -> dict[str, Any]:
        if name in self.root["header"]:
            return self.root["header"][name]
        raw = b"".join(self._chunks(self.root["catalogs"][name]))
        value = decode_bytes(raw, limit=MAX_EXPANDED_BYTES, field=f"manifest.{name}")
        if logical_digest(value) != digest(raw):
            raise KnowledgeStorageError(name, "noncanonical logical catalog")
        return value

    def materialize(self) -> dict[str, Any]:
        logical_version = self.root["logical_version"]
        fields = (*FIELDS, *MAINTENANCE_FIELDS) if logical_version == 7 else FIELDS
        payload = {"version": logical_version, **{name: self.field(name) for name in fields}}
        if logical_version == 7:
            payload.update({name: self.root["header"][name] for name in MAINTENANCE_HEADER_FIELDS})
            from .maintenance_state import maintenance_state_hash
            if maintenance_state_hash(payload["maintenance_state"]) != payload["maintenance_state_hash"]:
                raise KnowledgeStorageError("manifest.maintenance_state", "header state commitment mismatch")
        if "artifact_hashes" in self.root:
            payload["artifact_hashes"] = self.root["artifact_hashes"]
        if logical_digest(payload) != self.root["logical_hash"]:
            raise KnowledgeStorageError("manifest", "logical commitment mismatch")
        return payload


@dataclass(frozen=True)
class ValidatedManifestHeader:
    """Policy and artifact commitments only; never a complete sync manifest."""

    generation_inputs: Mapping[str, Any]
    artifact_hashes: ManifestArtifactHashes | None
    storage_version: int
    adoption_id: str | None = None
    maintenance_state_hash: str | None = None
    whole_maintenance_state_validated: bool = False


def read_manifest_header(raw: bytes, read: Reader) -> ValidatedManifestHeader:
    from .knowledge_artifacts import _decode_json_object
    from .sync_manifest import SyncManifest, validate_manifest_policy
    root = _decode_json_object(raw, "manifest")
    if root.get("version") not in {VERSION, MAINTENANCE_VERSION}:
        if root.get("version") == 7 and len(raw) > ROOT_LIMIT:
            raise KnowledgeStorageError("manifest", "selected flat v7 read exceeds 64 KiB; use full validation or explicit indexed v8 adoption", code="storage-limit")
        manifest = SyncManifest.from_payload(root)
        return ValidatedManifestHeader(freeze(manifest.generation_inputs), manifest.artifact_hashes,
            7 if manifest.maintenance_state is not None else 5,
            None if manifest.maintenance_state is None else manifest.maintenance_state["adoption_id"],
            None if manifest.maintenance_state is None else root["maintenance_state_hash"],
            manifest.maintenance_state is not None)
    if len(raw) > ROOT_LIMIT or canonical_bytes(root) != raw:
        raise KnowledgeStorageError("manifest", "invalid v6 root encoding")
    store = ManifestStoreReader(root, read)
    policy = store.field("generation_inputs")
    validate_manifest_policy(policy)
    marker = ManifestArtifactHashes.from_payload(root["artifact_hashes"]) if "artifact_hashes" in root else None
    if root["version"] == 8 and (marker is None or marker.maintenance_adoption_hash is None):
        raise KnowledgeStorageError("manifest", "adopted selected root lacks immutable marker commitment")
    return ValidatedManifestHeader(freeze(policy), marker, root["version"],
        root["header"].get("adoption_id"), root["header"].get("maintenance_state_hash"), False)


def current_manifest_format(wiki_dir: str | Path) -> str:
    from .knowledge_storage_io import read_guarded
    from .sync_manifest import MANIFEST_FILENAME
    path = Path(wiki_dir) / MANIFEST_FILENAME
    adoption = path.parent / ".llm-wiki-maintenance-adoption.json"
    adopted = adoption.exists() or adoption.is_symlink()
    if not path.exists() and not path.is_symlink():
        if adopted:
            raise KnowledgeStorageError("manifest", "adopted maintenance owner is missing; restore a complete snapshot", code="maintenance-adoption-incomplete")
        if (path.parent / ".llm-wiki-manifest").exists():
            raise KnowledgeStorageError("manifest", "indexed manifest root is missing; recover it first")
        return "v5"
    try:
        value = json.loads(read_guarded(path, MAX_EXPANDED_BYTES).content)
        if not isinstance(value, dict):
            raise ValueError("manifest must be an object")
    except (ValueError, UnicodeError):
        if adopted:
            raise KnowledgeStorageError("manifest", "adopted maintenance owner is invalid; restore a complete snapshot", code="maintenance-adoption-incomplete")
        if (path.parent / ".llm-wiki-manifest").exists():
            raise KnowledgeStorageError("manifest", "indexed manifest root is invalid; recover it first")
        return "v5"
    version = value.get("version")
    if adopted and version not in {7, MAINTENANCE_VERSION}:
        raise KnowledgeStorageError("manifest", "immutable marker cannot accompany a legacy owner; restore a complete snapshot", code="maintenance-adoption-incomplete")
    if type(version) is int and 1 <= version <= 5:
        return "v5"
    if version == VERSION:
        return "indexed-v6"
    if version == 7:
        return "v7"
    if version == MAINTENANCE_VERSION:
        return "indexed-v8"
    raise KnowledgeStorageError("manifest", "cannot overwrite an unsupported manifest version", code="unsupported-version")
