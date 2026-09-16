"""Bounded, content-addressed storage for the unchanged logical knowledge model.

This module owns the storage wire format, not extraction or evidence semantics.
Full consumers still use the native model/artifact validators. A scoped receipt
only describes the committed records actually read, never a full-validity proof.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, NoReturn

from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY, TYPED_GRAPH_EXTENSION_KEY

STORE_SCHEMA = "llm-wiki-knowledge/v2"
OBJECT_SCHEMA = "llm-wiki-knowledge-object/v1"
SLICE_SCHEMA = "llm-wiki-knowledge-slice/v1"
LOGICAL_SCHEMA = "llm-wiki-knowledge/v1"
ROOT_FILENAME = ".llm-wiki-knowledge.json"
OBJECT_DIRECTORY = ".llm-wiki-knowledge/objects"
MAX_ROOT_BYTES = 262_144
TARGET_OBJECT_BYTES = 4_194_304
MAX_OBJECT_BYTES = 8_388_608
MAX_EXPANDED_BYTES = 1_073_741_824
MAX_READ_OBJECTS = 100_000
GIT_WARNING_BYTES = 50 * 1024 * 1024
GIT_FAILURE_BYTES = 95 * 1024 * 1024
MAX_VALUE_DEPTH = 96
COLLECTIONS = ("concepts", "relationships", "edges", "sections", "extensions", "values", "lookup")
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_PREFIX = re.compile(r"[0-9a-f]{0,128}\Z")
_RESERVED = frozenset({"$value", "$basis", "$object"})
_INTERN_FIELDS = frozenset({"source", "target", "basis"})
_HOT_OBJECT_TARGET = 65_536
_RECORD_OBJECT_TARGET = 262_144
_LOOKUP_GROUP_TARGET = 8_192


class KnowledgeStorageError(ValueError):
    """A storage contract, integrity or bounded-work failure."""

    def __init__(self, field: str, message: str, *, code: str = "storage-invalid"):
        self.field, self.message, self.code = field, message, code
        super().__init__(f"{field}: {message}")


def canonical_bytes(value: Any) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise KnowledgeStorageError("json", "must be finite UTF-8 JSON") from exc


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def logical_digest(value: Any) -> str:
    """Hash logical JSON without allocating a second monolithic serialization."""
    result = hashlib.sha256()
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False)
    for part in encoder.iterencode(value):
        result.update(part.encode("utf-8"))
    result.update(b"\n")
    return "sha256:" + result.hexdigest()


def _fail(field: str, message: str, code: str = "storage-invalid") -> NoReturn:
    raise KnowledgeStorageError(field, message, code=code)


def _fields(value: Any, names: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != names:
        _fail(field, "must contain exactly " + ", ".join(sorted(names)))
    return value


def _integer(value: Any, field: str, maximum: int, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        _fail(field, f"must be an integer between {minimum} and {maximum}")
    return value


def _text(value: Any, field: str, maximum: int = 16_384) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > maximum:
        _fail(field, "must be bounded nonempty UTF-8 text")
    return value


def _hash(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        _fail(field, "must be a SHA-256 commitment")
    return value


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", "duplicate object key")
        result[key] = value
    return result


def decode_bytes(raw: bytes, *, limit: int, field: str) -> dict[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > limit:
        _fail(field, "exceeds encoded byte limit", "storage-limit")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                           parse_constant=lambda _: _fail(field, "nonfinite number"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, KnowledgeStorageError):
            raise
        raise KnowledgeStorageError(field, "must contain finite UTF-8 JSON") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        _fail(field, "must use canonical compact JSON with one final newline")
    return value


def object_path(commitment: str) -> str:
    value = _hash(commitment, "object.hash")[7:]
    return f"{OBJECT_DIRECTORY}/{value[:2]}/{value}.json"


def _descriptor(value: Any, field: str) -> dict[str, Any]:
    item = _fields(value, {"hash", "bytes", "count"}, field)
    _hash(item["hash"], field + ".hash")
    _integer(item["bytes"], field + ".bytes", MAX_OBJECT_BYTES, 1)
    _integer(item["count"], field + ".count", 100_000_000)
    return item


def _route(owner: str, record_id: str) -> str:
    return hashlib.sha256(owner.encode("utf-8")).hexdigest() + hashlib.sha256(record_id.encode("utf-8")).hexdigest()


def _owner(concept: Mapping[str, Any]) -> str:
    basis = concept.get("facets", {}).get("structure", {}).get("basis") or {}
    return ("source:" + basis["source_path"] if basis.get("source_path")
            else "page:" + concept["document"]["canonical_path"])


def _node_aliases(node: Any) -> set[str]:
    if isinstance(node, str):
        return {"concept:" + node}
    if not isinstance(node, dict):
        return set()
    result = set()
    for field, prefix in (("locator", "concept:"), ("source_path", "source:"),
                          ("canonical_path", "page:")):
        if isinstance(node.get(field), str):
            result.add(prefix + node[field])
    result.add("node:" + digest(canonical_bytes(node)))
    return result


def _concept_aliases(concept: Mapping[str, Any]) -> set[str]:
    from .knowledge_governance import natural_key_for
    aliases = {"concept:" + concept["locator"], "page:" + concept["document"]["canonical_path"],
               "concept:" + natural_key_for(concept["concept_kind"], concept["document"]["canonical_path"]),
               _owner(concept), *("term:" + term for term in re.findall(r"\w+", concept["title"].casefold())[:64])}
    from .contracts import GOVERNANCE_EXTENSION_KEY
    governance = concept.get("extensions", {}).get(GOVERNANCE_EXTENSION_KEY)
    if isinstance(governance, dict):
        if isinstance(governance.get("uid"), str):
            aliases.add("concept:" + governance["uid"])
        for alias in governance.get("aliases", []):
            if isinstance(alias, dict) and isinstance(alias.get("value"), str):
                aliases.add("concept:" + alias["value"])
    return aliases


@dataclass(frozen=True)
class KnowledgeStorePlan:
    root_bytes: bytes
    objects: Mapping[str, bytes]
    statistics: Mapping[str, Any]


class _Encoder:
    def __init__(self, basis: dict[str, str]):
        self.basis = {value: key for key, value in sorted(basis.items(), reverse=True)}
        self.values: dict[str, Any] = {}

    def encode(self, value: Any, *, field: str = "", depth: int = 0) -> Any:
        if depth > MAX_VALUE_DEPTH:
            _fail(field, "exceeds storage value depth", "storage-limit")
        if isinstance(value, str) and value in self.basis:
            return {"$basis": self.basis[value]}
        if isinstance(value, list):
            return [self.encode(v, depth=depth + 1) for v in value]
        if not isinstance(value, dict):
            return value
        items = {k: self.encode(v, field=k, depth=depth + 1) for k, v in value.items()}
        encoded: Any = ({"$object": [[k, items[k]] for k in sorted(items)]}
                        if set(items) & _RESERVED else items)
        if field in _INTERN_FIELDS:
            raw = canonical_bytes(encoded)
            if len(raw) >= 128:
                key = digest(raw)
                self.values.setdefault(key, encoded)
                return {"$value": key}
        return encoded


class _TreeBuilder:
    def __init__(self, target: int):
        self.target = _integer(target, "target_bytes", MAX_OBJECT_BYTES, 512)
        self.objects: dict[str, bytes] = {}

    def emit(self, payload: dict[str, Any], count: int) -> dict[str, Any]:
        raw = canonical_bytes(payload)
        if len(raw) > MAX_OBJECT_BYTES:
            _fail(payload["collection"], "object exceeds 8 MiB", "storage-limit")
        key = digest(raw)
        path = object_path(key)
        if path in self.objects and self.objects[path] != raw:
            _fail(path, "content hash collision")
        self.objects[path] = raw
        return {"hash": key, "bytes": len(raw), "count": count}

    def tree(self, collection: str, records: list[dict[str, Any]], prefix: str = "") -> dict[str, Any]:
        owners = {row["owner"] for row in records}
        if collection == "lookup":
            owners.update(row["value"]["owner"] for row in records)
        owner_table = sorted(owners)
        owner_indexes = {owner: index for index, owner in enumerate(owner_table)}
        packed = []
        for row in records:
            value = row["value"]
            if collection == "lookup":
                value = {**value, "owner": owner_indexes[value["owner"]]}
            packed.append({"id": row["id"], "owner": owner_indexes[row["owner"]], "value": value})
        payload = {"schema_version": OBJECT_SCHEMA, "collection": collection,
                   "prefix": prefix, "kind": "records", "owners": owner_table, "records": packed}
        target = min(self.target, _HOT_OBJECT_TARGET if collection in {"values", "lookup"} else _RECORD_OBJECT_TARGET)
        if prefix and len(canonical_bytes(payload)) <= target:
            return self.emit(payload, len(records))
        if len(records) <= 1 and prefix:
            return self.emit(payload, len(records))
        if len(prefix) >= 128:
            _fail(collection, "indivisible colliding records exceed the object limit", "storage-limit")
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            buckets[_route(record["owner"], record["id"])[len(prefix)]].append(record)
        children = {}
        for key in sorted(buckets):
            group = buckets[key]
            routes = [_route(row["owner"], row["id"]) for row in group]
            first, last = min(routes), max(routes)
            shared = 0
            while shared < len(first) and first[shared] == last[shared]:
                shared += 1
            child_prefix = first[:max(len(prefix) + 1, shared)]
            children[key] = self.tree(collection, group, child_prefix)
        return self.emit({"schema_version": OBJECT_SCHEMA, "collection": collection,
                          "prefix": prefix, "kind": "catalog", "children": children}, len(records))


def build_knowledge_store(payload: Mapping[str, Any], *, target_bytes: int = TARGET_OBJECT_BYTES) -> KnowledgeStorePlan:
    """Encode a canonical logical v1 payload after its semantic validation.

    Arrays retain the logical model's canonical order; no global ordinal is
    stored in a shard, so inserting one record does not renumber unrelated data.
    """
    if payload.get("schema_version") != LOGICAL_SCHEMA:
        _fail("schema_version", "requires a logical knowledge v1 payload")
    extensions = dict(payload.get("extensions", {}))
    graph = extensions.pop(TYPED_GRAPH_EXTENSION_KEY, None)
    sections = extensions.pop(SECTION_OWNERSHIP_EXTENSION_KEY, None)
    basis: dict[str, str] = {}
    for key, value in payload["bundle"]["snapshot"].items():
        if isinstance(value, str) and _HASH.fullmatch(value):
            basis["snapshot." + key] = value
    if graph:
        for key, value in graph["input_hashes"].items():
            basis["graph." + key] = value
    encoder = _Encoder(basis)
    records: dict[str, list[dict[str, Any]]] = {name: [] for name in COLLECTIONS}
    concept_owners: dict[str, str] = {c["locator"]: _owner(c) for c in payload["concepts"]}
    page_owners: dict[str, str] = {c["document"]["canonical_path"]: _owner(c) for c in payload["concepts"]}
    lookup: dict[tuple[str, str, str], set[str]] = defaultdict(set)

    def add(kind: str, rid: str, owner: str, value: Any, aliases: Iterable[str]) -> None:
        _text(owner, kind + ".owner")
        _text(rid, kind + ".id")
        records[kind].append({"id": rid, "owner": owner, "value": encoder.encode(value)})
        for alias in set(aliases):
            lookup[(alias, kind, owner)].add(rid)

    for concept in payload["concepts"]:
        locator = concept["locator"]
        owner = concept_owners[locator]
        add("concepts", locator, owner, concept, _concept_aliases(concept))
    occurrences: Counter[str] = Counter()
    for relationship in payload["relationships"]:
        encoded = encoder.encode(relationship)
        key = digest(canonical_bytes(encoded))
        occurrences[key] += 1
        rid = f"{key}:{occurrences[key]}"
        source = _text(relationship["from"], "relationship.from")
        relationship_owner = _text(concept_owners.get(source, "concept:" + source), "relationship.owner")
        aliases = {relationship_owner, "out:concept:" + source}
        aliases.update("in:" + a for a in _node_aliases(relationship["target"]))
        add("relationships", rid, relationship_owner, relationship, aliases)
    if graph:
        for edge in graph["edges"]:
            from_node = edge["from"]
            aliases = _node_aliases(from_node)
            edge_owner = next(iter(sorted(a for a in aliases if a.startswith("source:"))), None)
            if edge_owner is None:
                locator = _text(from_node.get("locator") if isinstance(from_node, dict) else from_node, "edge.from")
                edge_owner = concept_owners.get(locator, next(iter(sorted(aliases)), "edge:" + edge["key"]))
            edge_owner = _text(edge_owner, "edge.owner")
            edge_aliases = {edge_owner, *("out:" + a for a in aliases),
                            *("in:" + a for a in _node_aliases(edge["target"]))}
            add("edges", edge["key"], edge_owner, edge, edge_aliases)
    if sections:
        for page in sections["pages"]:
            locator = page["page_locator"]
            owner = _text(concept_owners.get(locator, page_owners.get(locator, "page:" + locator)), "section.owner")
            add("sections", locator, owner, page, {owner, "concept:" + locator, "page:" + locator})
    for key, value in extensions.items():
        add("extensions", key, key, value, {"extension:" + key})
    def add_lookup(alias: str, kind: str, owner: str, ids: list[str], prefix: str = "") -> None:
        identity = {"collection": kind, "owner": owner, "prefix": prefix}
        row = {"owner": alias, "id": digest(canonical_bytes(identity)), "value": {**identity, "ids": ids}}
        if len(canonical_bytes(row)) <= _LOOKUP_GROUP_TARGET or len(ids) == 1:
            records["lookup"].append(row)
            return
        if len(prefix) >= 64:
            _fail("lookup", "colliding routing identifiers exceed the group limit", "storage-limit")
        buckets: dict[str, list[str]] = defaultdict(list)
        for rid in ids:
            buckets[hashlib.sha256(rid.encode("utf-8")).hexdigest()[len(prefix)]].append(rid)
        for nibble, group in sorted(buckets.items()):
            add_lookup(alias, kind, owner, group, prefix + nibble)

    for (alias, kind, owner), ids in sorted(lookup.items()):
        add_lookup(alias, kind, owner, sorted(ids))
    records["values"] = [{"id": key, "owner": "shared", "value": value}
                         for key, value in encoder.values.items()]
    builder = _TreeBuilder(target_bytes)
    collections = {}
    for kind, rows in records.items():
        rows.sort(key=lambda r: (r["owner"], r["id"]))
        identities = [(row["owner"], row["id"]) for row in rows]
        if len(identities) != len(set(identities)):
            _fail(kind, "duplicate record identity")
        collections[kind] = builder.tree(kind, rows)
    metadata = {"has_extensions": "extensions" in payload,
                "graph": None if graph is None else {k: v for k, v in graph.items() if k != "edges"},
                "sections": None if sections is None else {k: v for k, v in sections.items() if k != "pages"}}
    root = {"schema_version": STORE_SCHEMA, "logical_schema": LOGICAL_SCHEMA,
            "bundle": payload["bundle"], "basis": basis, "metadata": metadata,
            "collections": collections, "logical_hash": logical_digest(payload)}
    root_bytes = canonical_bytes(root)
    if len(root_bytes) > MAX_ROOT_BYTES:
        _fail("root", "metadata exceeds the 256 KiB root ceiling", "storage-limit")
    parse_store_root(root_bytes)
    stats = {"root_bytes": len(root_bytes), "object_bytes": sum(map(len, builder.objects.values())),
             "object_count": len(builder.objects), "records": {k: len(v) for k, v in records.items()},
             "largest_object_bytes": max(map(len, builder.objects.values()), default=0)}
    return KnowledgeStorePlan(root_bytes, builder.objects, stats)


def parse_store_root(raw: bytes) -> dict[str, Any]:
    root = decode_bytes(raw, limit=MAX_ROOT_BYTES, field="knowledge.root")
    _fields(root, {"schema_version", "logical_schema", "bundle", "basis", "metadata", "collections", "logical_hash"}, "knowledge.root")
    if root["schema_version"] != STORE_SCHEMA or root["logical_schema"] != LOGICAL_SCHEMA:
        _fail("knowledge.root.schema_version", "unsupported storage version", "unsupported-schema-version")
    _hash(root["logical_hash"], "knowledge.root.logical_hash")
    if not isinstance(root["bundle"], dict) or not isinstance(root["basis"], dict):
        _fail("knowledge.root", "bundle and basis must be objects")
    for key, value in root["basis"].items():
        _text(key, "basis.key", 256)
        _hash(value, "basis.value")
    _fields(root["collections"], set(COLLECTIONS), "collections")
    for name, value in root["collections"].items():
        _descriptor(value, "collections." + name)
    meta = _fields(root["metadata"], {"graph", "sections", "has_extensions"}, "metadata")
    if type(meta["has_extensions"]) is not bool:
        _fail("metadata.has_extensions", "must be boolean")
    for name in ("graph", "sections"):
        if meta[name] is not None and not isinstance(meta[name], dict):
            _fail("metadata." + name, "must be an object or null")
    from .knowledge_model import _parse_bundle
    try:
        _parse_bundle(root["bundle"], "bundle")
    except ValueError as exc:
        raise KnowledgeStorageError("bundle", str(exc)) from exc
    expected_basis = {"snapshot." + k: v for k, v in root["bundle"]["snapshot"].items()
                      if isinstance(v, str) and _HASH.fullmatch(v)}
    if meta["graph"] is not None:
        graph = _fields(meta["graph"], {"schema_version", "input_hashes", "coverage"}, "metadata.graph")
        if graph["schema_version"] != "llm-wiki-typed-graph/v1" or not isinstance(graph["input_hashes"], dict):
            _fail("metadata.graph", "unsupported graph metadata")
        expected_basis.update({"graph." + k: v for k, v in graph["input_hashes"].items()})
        from .knowledge_graph import validate_typed_graph_slice
        from .knowledge_envelope import INVENTORY_HASH_EXTENSION
        try:
            normalized_graph = validate_typed_graph_slice({**graph, "edges": []})
        except ValueError as exc:
            raise KnowledgeStorageError("metadata.graph", str(exc)) from exc
        if {k: v for k, v in normalized_graph.items() if k != "edges"} != graph:
            _fail("metadata.graph", "must contain canonical complete analyzer metadata")
        if graph["input_hashes"]["inventory"] != root["bundle"]["snapshot"].get("extensions", {}).get(INVENTORY_HASH_EXTENSION):
            _fail("metadata.graph", "inventory basis differs from the bundle")
    if meta["sections"] is not None:
        _fields(meta["sections"], {"schema_version"}, "metadata.sections")
        if meta["sections"]["schema_version"] != "llm-wiki-section-ownership/v1":
            _fail("metadata.sections", "unsupported ownership metadata")
    if expected_basis != root["basis"]:
        _fail("basis", "does not match the committed snapshot and graph bases")
    return root


def _validate_selected_record(collection: str, row: dict[str, Any], value: Any) -> None:
    """Reuse semantic record owners without issuing a whole-bundle verdict."""
    from .knowledge_model import _parse_concept, _parse_relationship, _parse_extensions
    from .knowledge_graph import _normalise_edge
    from .section_ownership import validate_section_ownership
    try:
        if collection == "concepts":
            _parse_concept(value, "concept")
            if value["locator"] != row["id"] or _owner(value) != row["owner"]:
                _fail(collection, "concept identity or owner mismatch")
        elif collection == "relationships":
            _parse_relationship(value, "relationship")
        elif collection == "edges":
            _normalise_edge(value, "edge", None)
            if value["key"] != row["id"]:
                _fail(collection, "edge identity mismatch")
        elif collection == "sections":
            validate_section_ownership({"schema_version": "llm-wiki-section-ownership/v1", "pages": [value]})
            if value["page_locator"] != row["id"]:
                _fail(collection, "page identity mismatch")
        elif collection == "extensions":
            _parse_extensions({row["id"]: value}, "extensions")
    except (ValueError, TypeError, KeyError) as exc:
        if isinstance(exc, KnowledgeStorageError):
            raise
        raise KnowledgeStorageError(collection, f"invalid selected native record: {exc}") from exc


@dataclass(frozen=True)
class KnowledgeSlice:
    """Detached scoped data; deliberately not ValidatedKnowledgeArtifacts."""

    _bytes: bytes

    def to_payload(self) -> dict[str, Any]:
        return json.loads(self._bytes)


class KnowledgeStoreReader:
    """Read committed objects through a caller-owned bounded I/O boundary."""

    def __init__(self, root_bytes: bytes, read_object: Callable[[str, int], bytes], *,
                 max_bytes: int = MAX_EXPANDED_BYTES, max_objects: int = MAX_READ_OBJECTS,
                 max_expanded_bytes: int = MAX_EXPANDED_BYTES):
        self.root = parse_store_root(root_bytes)
        self.root_bytes = root_bytes
        self.read_object = read_object
        self.max_bytes = _integer(max_bytes, "max_bytes", MAX_EXPANDED_BYTES, 1)
        self.max_objects = _integer(max_objects, "max_objects", MAX_READ_OBJECTS, 1)
        self.max_expanded_bytes = _integer(max_expanded_bytes, "max_expanded_bytes", MAX_EXPANDED_BYTES, 1)
        self.bytes_read = len(root_bytes)
        self.expanded_bytes = 0
        self.objects: dict[str, bytes] = {}
        self._nodes: dict[str, dict[str, Any]] = {}
        self._validated_nodes: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._values: dict[str, Any] = {}
        self._concept_owners: dict[str, str] = {}
        self.consumed_concepts: dict[str, dict[str, Any]] = {}
        self._validated_records: dict[str, set[tuple[str, str]]] = {k: set() for k in COLLECTIONS[:5]}
        self._check_budget()

    def _check_budget(self) -> None:
        if self.bytes_read > self.max_bytes or len(self.objects) > self.max_objects:
            _fail("read", "storage inspection budget exhausted", "storage-budget-exhausted")

    def _node(self, desc: dict[str, Any], collection: str, prefix: str) -> dict[str, Any]:
        _descriptor(desc, "object")
        path = object_path(desc["hash"])
        raw = self.objects.get(path)
        if raw is None:
            if self.bytes_read + desc["bytes"] > self.max_bytes or len(self.objects) >= self.max_objects:
                _fail("read", "storage inspection budget exhausted", "storage-budget-exhausted")
            raw = self.read_object(path, desc["bytes"])
            self.bytes_read += len(raw)
            if len(raw) != desc["bytes"] or digest(raw) != desc["hash"]:
                _fail(path, "object bytes do not match their commitment")
            self.objects[path] = raw
            self._nodes[path] = decode_bytes(raw, limit=MAX_OBJECT_BYTES, field=path)
            self._check_budget()
        elif len(raw) != desc["bytes"]:
            _fail(path, "inconsistent object size descriptor")
        cache_key = (path, collection, prefix)
        cached = self._validated_nodes.get(cache_key)
        if cached is not None:
            count = (len(cached["records"]) if cached["kind"] == "records"
                     else sum(child["count"] for child in cached["children"].values()))
            if count != desc["count"]:
                _fail(path, "inconsistent object count descriptor")
            return cached
        node = self._nodes[path]
        kind = node.get("kind")
        _fields(node, {"schema_version", "collection", "prefix", "kind"}
                | ({"children"} if kind == "catalog" else {"records", "owners"}), path)
        actual_prefix = node["prefix"]
        if (node["schema_version"] != OBJECT_SCHEMA or node["collection"] != collection
                or not isinstance(actual_prefix, str) or not _PREFIX.fullmatch(actual_prefix)
                or (not prefix and actual_prefix) or not actual_prefix.startswith(prefix)):
            _fail(path, "object kind, collection or routing prefix mismatch")
        prefix = actual_prefix
        if kind == "catalog":
            children = node["children"]
            if not isinstance(children, dict) or len(children) > 16 or len(prefix) >= 128:
                _fail(path, "invalid radix catalog")
            for key, child in children.items():
                if key not in "0123456789abcdef" or len(key) != 1:
                    _fail(path, "invalid radix child")
                _descriptor(child, path)
            if sum(child["count"] for child in children.values()) != desc["count"]:
                _fail(path, "catalog count mismatch")
        elif kind == "records":
            rows = node["records"]
            owners = node["owners"]
            if not isinstance(rows, list) or len(rows) != desc["count"]:
                _fail(path, "record count mismatch")
            if not isinstance(owners, list) or any(not isinstance(owner, str) for owner in owners) or owners != sorted(set(owners)):
                _fail(path, "owner table must contain unique sorted names")
            for owner in owners:
                _text(owner, path)
            identities = []
            unpacked = []
            for row in rows:
                _fields(row, {"owner", "id", "value"}, path)
                owner = owners[_integer(row["owner"], path, len(owners) - 1)]
                rid = _text(row["id"], path)
                if not _route(owner, rid).startswith(prefix):
                    _fail(path, "record does not belong to its routing prefix")
                identities.append((owner, rid))
                value = row["value"]
                if collection == "lookup":
                    _fields(value, {"collection", "owner", "prefix", "ids"}, path)
                    value = {**value, "owner": owners[_integer(value["owner"], path, len(owners) - 1)]}
                unpacked.append({"owner": owner, "id": rid, "value": value})
            if identities != sorted(set(identities)):
                _fail(path, "records must have unique sorted identities")
            node = {**node, "records": unpacked}
        else:
            _fail(path, "unknown object kind")
        self._validated_nodes[cache_key] = node
        return node

    def records(self, collection: str, *, owner: str | None = None,
                record_id: str | None = None) -> Iterable[dict[str, Any]]:
        if collection not in COLLECTIONS:
            _fail("collection", "unknown collection")
        wanted = "" if owner is None else _route(owner, record_id or "")[:64 if record_id is None else 128]

        def walk(desc: dict[str, Any], prefix: str) -> Iterable[dict[str, Any]]:
            node = self._node(desc, collection, prefix)
            prefix = node["prefix"]
            if wanted and not (wanted.startswith(prefix) or prefix.startswith(wanted)):
                return
            if node["kind"] == "records":
                for row in node["records"]:
                    if (owner is None or row["owner"] == owner) and (record_id is None or row["id"] == record_id):
                        yield row
                return
            for key, child in sorted(node["children"].items()):
                route = prefix + key
                if not wanted or wanted.startswith(route) or route.startswith(wanted):
                    yield from walk(child, route)

        return walk(self.root["collections"][collection], "")

    def record(self, collection: str, owner: str, record_id: str) -> dict[str, Any]:
        rows = list(self.records(collection, owner=owner, record_id=record_id))
        if len(rows) != 1:
            _fail(collection, "missing or ambiguous referenced record")
        return rows[0]

    def _charge_expanded(self, amount: int) -> None:
        self.expanded_bytes += amount
        if self.expanded_bytes > self.max_expanded_bytes:
            _fail("value", "expanded data budget exhausted", "storage-budget-exhausted")

    def _expand(self, value: Any, *, stack: tuple[str, ...] = (), depth: int = 0) -> Any:
        if depth > MAX_VALUE_DEPTH:
            _fail("value", "reference/value depth exceeded", "storage-limit")
        if isinstance(value, list):
            self._charge_expanded(2 + max(0, len(value) - 1))
            return [self._expand(v, stack=stack, depth=depth + 1) for v in value]
        if not isinstance(value, dict):
            self._charge_expanded(len(canonical_bytes(value)) - 1)
            return value
        if set(value) == {"$basis"}:
            key = value["$basis"]
            if not isinstance(key, str) or key not in self.root["basis"]:
                _fail("basis", "missing basis reference")
            result = self.root["basis"][key]
            self._charge_expanded(len(canonical_bytes(result)) - 1)
            return result
        if set(value) == {"$value"}:
            key = _hash(value["$value"], "value.ref")
            if key in stack:
                _fail("value", "cyclic reference")
            if key not in self._values:
                encoded = self.record("values", "shared", key)["value"]
                if digest(canonical_bytes(encoded)) != key:
                    _fail("value", "descriptor identity mismatch")
                self._values[key] = encoded
            return self._expand(self._values[key], stack=(*stack, key), depth=depth + 1)
        if set(value) == {"$object"}:
            pairs = value["$object"]
            if not isinstance(pairs, list):
                _fail("value", "escaped object must contain pairs")
            result = {}
            self._charge_expanded(2 + max(0, len(pairs) - 1))
            previous = None
            for pair in pairs:
                if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str):
                    _fail("value", "invalid escaped pair")
                if previous is not None and pair[0] <= previous:
                    _fail("value", "escaped keys must be unique and sorted")
                previous = pair[0]
                self._charge_expanded(len(canonical_bytes(pair[0])))
                result[pair[0]] = self._expand(pair[1], stack=stack, depth=depth + 1)
            return result
        if set(value) & _RESERVED:
            _fail("value", "unescaped reserved storage key")
        self._charge_expanded(2 + max(0, len(value) - 1)
                              + sum(len(canonical_bytes(k)) for k in value))
        return {k: self._expand(v, stack=stack, depth=depth + 1) for k, v in value.items()}

    def expand_record(self, row: dict[str, Any]) -> Any:
        value = self._expand(row["value"])
        self._charge_expanded(1)
        return value

    def materialize(self, *, audit_routes: bool = True) -> dict[str, Any]:
        data = {name: [self.expand_record(row) for row in self.records(name)]
                for name in ("concepts", "relationships", "edges", "sections")}
        extensions = {row["id"]: self.expand_record(row) for row in self.records("extensions")}
        if self.root["metadata"]["graph"] is not None:
            extensions[TYPED_GRAPH_EXTENSION_KEY] = {**self.root["metadata"]["graph"],
                "edges": sorted(data["edges"], key=lambda e: e["key"])}
        elif data["edges"]:
            _fail("edges", "graph metadata missing")
        if self.root["metadata"]["sections"] is not None:
            extensions[SECTION_OWNERSHIP_EXTENSION_KEY] = {**self.root["metadata"]["sections"],
                "pages": sorted(data["sections"], key=lambda p: (p["page_locator"].casefold(), p["page_locator"]))}
        elif data["sections"]:
            _fail("sections", "ownership metadata missing")
        payload = {"schema_version": LOGICAL_SCHEMA, "bundle": self.root["bundle"],
                   "concepts": sorted(data["concepts"], key=lambda c: c["locator"]),
                   "relationships": sorted(data["relationships"], key=canonical_bytes)}
        if self.root["metadata"]["has_extensions"]:
            payload["extensions"] = extensions
        elif extensions:
            _fail("extensions", "extension metadata mismatch")
        if logical_digest(payload) != self.root["logical_hash"]:
            _fail("knowledge", "logical content commitment mismatch")
        # Full audit also inspects unused descriptor objects and the secondary
        # index, which a selected read deliberately cannot establish globally.
        for row in self.records("values"):
            if row["owner"] != "shared" or digest(canonical_bytes(row["value"])) != row["id"]:
                _fail("values", "descriptor identity mismatch")
            self.expand_record(row)
        if audit_routes:
            self._audit_lookup(payload)
        return payload

    def _audit_lookup(self, payload: dict[str, Any]) -> None:
        # Rebuild expected index from logical facts, independently of supplied
        # catalog membership. A missing record with recomputed object hashes is
        # therefore still an invalid full store.
        expected = build_knowledge_store(payload)
        reader = KnowledgeStoreReader(expected.root_bytes, lambda path, _: expected.objects[path])
        for collection in COLLECTIONS:
            wanted = {(r["owner"], r["id"]): r["value"] for r in reader.records(collection)}
            actual = {(r["owner"], r["id"]): r["value"] for r in self.records(collection)}
            if actual != wanted:
                _fail(collection, "does not exactly index the logical knowledge")

    def _lookup_references(self, selector: str) -> Iterable[dict[str, str]]:
        for row in self.records("lookup", owner=selector):
            value = _fields(row["value"], {"collection", "owner", "prefix", "ids"}, "lookup.value")
            if value["collection"] not in COLLECTIONS[:5]:
                _fail("lookup", "invalid target collection")
            owner = _text(value["owner"], "lookup.owner")
            prefix, ids = value["prefix"], value["ids"]
            if not isinstance(prefix, str) or not re.fullmatch(r"[0-9a-f]{0,64}", prefix) or not isinstance(ids, list):
                _fail("lookup", "invalid reference group")
            identity = {"collection": value["collection"], "owner": owner, "prefix": prefix}
            if digest(canonical_bytes(identity)) != row["id"]:
                _fail("lookup", "reference group identity mismatch")
            previous = None
            for rid in ids:
                _text(rid, "lookup.id")
                if previous is not None and rid <= previous:
                    _fail("lookup", "reference IDs must be sorted and unique")
                previous = rid
                if not hashlib.sha256(rid.encode("utf-8")).hexdigest().startswith(prefix):
                    _fail("lookup", "reference outside its group prefix")
                yield {"collection": value["collection"], "owner": owner, "id": rid}

    def _concept_owner(self, locator: str) -> str:
        if locator not in self._concept_owners:
            matched = []
            for ref in self._lookup_references("concept:" + locator):
                if ref["collection"] == "concepts" and ref["id"] == locator:
                    matched.append(ref)
            if len(matched) != 1:
                _fail("lookup", "source concept ownership is missing or ambiguous")
            ref = matched[0]
            row = self.record("concepts", _text(ref["owner"], "owner"), locator)
            value = self.expand_record(row)
            _validate_selected_record("concepts", row, value)
            self._validated_records["concepts"].add((row["owner"], row["id"]))
            self._concept_owners[locator] = _owner(value)
            self.consumed_concepts[locator] = value
        return self._concept_owners[locator]

    def _record_aliases(self, collection: str, row: dict[str, Any], value: Any) -> set[str]:
        if collection == "concepts":
            self._concept_owners[value["locator"]] = _owner(value)
            self.consumed_concepts[value["locator"]] = value
            return _concept_aliases(value)
        if collection == "relationships":
            owner = self._concept_owner(value["from"])
            parts = row["id"].rsplit(":", 1)
            if len(parts) != 2 or parts[0] != digest(canonical_bytes(row["value"])) or not re.fullmatch(r"[1-9][0-9]*", parts[1]):
                _fail(collection, "relationship identity mismatch")
            aliases = {owner, "out:concept:" + value["from"]}
            aliases.update("in:" + a for a in _node_aliases(value["target"]))
        elif collection == "edges":
            source = value["from"]
            locator = source["locator"] if isinstance(source, dict) else source
            owner = self._concept_owner(locator)
            aliases = {owner, *("out:" + a for a in _node_aliases(source)),
                       *("in:" + a for a in _node_aliases(value["target"]))}
        elif collection == "sections":
            owner = self._concept_owner(value["page_locator"])
            aliases = {owner, "concept:" + value["page_locator"], "page:" + value["page_locator"]}
        else:
            owner = row["id"]
            aliases = {"extension:" + row["id"]}
        if owner != row["owner"]:
            _fail(collection, "record owner does not match its source concept")
        return aliases

    def select(self, selectors: Iterable[str], *, max_records: int = 1000) -> KnowledgeSlice:
        selectors = sorted(set(selectors))
        if len(selectors) > 100:
            _fail("selectors", "at most 100 selectors are supported", "storage-limit")
        _integer(max_records, "max_records", 100_000, 1)
        refs: dict[tuple[str, str, str], dict[str, Any]] = {}
        requested_aliases: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        complete = True
        for selector in selectors:
            _text(selector, "selector")
            for ref in self._lookup_references(selector):
                key = (ref["collection"], _text(ref["owner"], "lookup.owner"), _text(ref["id"], "lookup.id"))
                if key not in refs and len(refs) >= max_records:
                    complete = False
                    break
                refs[key] = ref
                requested_aliases[key].add(selector)
            if not complete:
                break
        records: dict[str, list[Any]] = {key: [] for key in COLLECTIONS[:5]}
        for collection, owner, rid in sorted(refs):
            row = self.record(collection, owner, rid)
            value = self.expand_record(row)
            _validate_selected_record(collection, row, value)
            if not requested_aliases[(collection, owner, rid)] <= self._record_aliases(collection, row, value):
                _fail("lookup", "selected record does not match the requested selector")
            self._validated_records[collection].add((owner, rid))
            records[collection].append({"id": rid, "owner": owner, "value": value})
        if records["edges"]:
            from .knowledge_graph import validate_typed_graph_slice
            metadata = self.root["metadata"]["graph"]
            if metadata is None:
                _fail("edges", "graph metadata missing")
            try:
                validate_typed_graph_slice({**metadata, "edges": [row["value"] for row in records["edges"]]})
            except ValueError as exc:
                raise KnowledgeStorageError("edges", str(exc)) from exc
        result = {"schema_version": SLICE_SCHEMA, "root_hash": digest(self.root_bytes),
                  "logical_hash": self.root["logical_hash"], "selectors": selectors,
                  "validation_scope": "selected-committed-records", "whole_store_validated": False,
                  "lookup_complete": complete, "live_evaluated": False,
                  "bundle": self.root["bundle"], "metadata": self.root["metadata"], "records": records,
                  "inspected_objects": sorted(self.objects),
                  "work": {"root_bytes": len(self.root_bytes), "object_bytes": self.bytes_read - len(self.root_bytes),
                           "objects": len(self.objects), "expanded_bytes": self.expanded_bytes},
                  "unverified_records": {name: self.root["collections"][name]["count"] - len(self._validated_records[name])
                                     for name in COLLECTIONS[:5]}}
        return KnowledgeSlice(canonical_bytes(result))
