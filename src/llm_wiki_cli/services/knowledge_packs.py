"""Immutable indexed ZIP containers for unchanged logical knowledge objects.

Selected readers authenticate bounded member ranges, not an entire archive.
Full readers additionally validate ZIP structure and exact locator membership.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
import hashlib
import io
import json
import re
import struct
from typing import Any, NoReturn
import zipfile
import zlib

from .knowledge_storage import (
    COLLECTIONS, MAX_EXPANDED_BYTES, MAX_OBJECT_BYTES, MAX_READ_OBJECTS, MAX_ROOT_BYTES,
    OBJECT_SCHEMA, KnowledgeSlice, KnowledgeStorageError, KnowledgeStorePlan,
    KnowledgeStoreReader, build_knowledge_store, canonical_bytes, decode_bytes, digest,
    parse_store_root, _fields, _hash, _integer,
)

PACKED_SCHEMA = "llm-wiki-knowledge/v3"
PACK_INDEX_SCHEMA = "llm-wiki-knowledge-pack-index/v1"
PACK_DIRECTORY = ".llm-wiki-knowledge/packs"
PACK_INDEX_DIRECTORY = ".llm-wiki-knowledge/pack-index"
PACK_TARGET_BYTES = 4_194_304
MAX_PACK_BYTES = 8_388_608
MAX_INDEX_BYTES = 65_536
MAX_PACK_MEMBERS = 512
MAX_DIRECTORY_BYTES = 262_144
PACKED_FORMATS = frozenset({"packed-v3", "packed-v3-deflate"})
INDEX_NAME = re.compile(r"\.llm-wiki-knowledge/pack-index/([0-9a-f]{2})/\1[0-9a-f]{62}\.json\Z")
PACK_NAME = re.compile(r"\.llm-wiki-knowledge/packs/([0-9a-f]{2})/(\1[0-9a-f]{62})-knowledge-pack-(root|[01]{1,64})\.zip\Z")
_BITS = re.compile(r"[01]{0,64}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MEMBER = re.compile(r"(" + "|".join(COLLECTIONS) + r")/(root|[0-9a-f]{1,128})\.json\Z")
_LOCAL_HEADER = struct.Struct("<4s5H3I2H")
_END = struct.Struct("<4s4H2IH")
RangeReader = Callable[[str, int, int, int], bytes]


def _fail(field: str, message: str, code: str = "storage-invalid") -> NoReturn:
    raise KnowledgeStorageError(field, message, code=code)


def _bits(hexadecimal: str) -> str:
    return format(int(hexadecimal, 16), "0256b")


def _bucket(member: str) -> str:
    return _bits(hashlib.sha256(member.encode("ascii")).hexdigest())


def _member_name(raw: bytes) -> str:
    node = decode_bytes(raw, limit=MAX_OBJECT_BYTES, field="member")
    prefix = node.get("prefix")
    if (node.get("schema_version") != OBJECT_SCHEMA or node.get("collection") not in COLLECTIONS
            or not isinstance(prefix, str) or re.fullmatch(r"[0-9a-f]{0,128}", prefix) is None
            or node.get("kind") not in {"catalog", "records"}):
        _fail("member", "not a logical knowledge object")
    return f"{node['collection']}/{prefix or 'root'}.json"


def pack_path(descriptor: Mapping[str, Any]) -> str:
    identity = descriptor["hash"][7:]
    return f"{PACK_DIRECTORY}/{identity[:2]}/{identity}-knowledge-pack-{descriptor['bucket'] or 'root'}.zip"


def index_path(commitment: str) -> str:
    value = _hash(commitment, "index.hash")[7:]
    return f"{PACK_INDEX_DIRECTORY}/{value[:2]}/{value}.json"


def _index_descriptor(value: Any) -> dict[str, Any]:
    item = _fields(value, {"hash", "bytes", "count"}, "index")
    _hash(item["hash"], "index.hash")
    _integer(item["bytes"], "index.bytes", MAX_INDEX_BYTES, 1)
    _integer(item["count"], "index.count", MAX_READ_OBJECTS, 1)
    return item


def _pack_descriptor(value: Any) -> dict[str, Any]:
    item = _fields(value, {"hash", "bytes", "bucket", "members", "expanded_bytes"}, "pack")
    _hash(item["hash"], "pack.hash")
    _integer(item["bytes"], "pack.bytes", MAX_PACK_BYTES, 22)
    _integer(item["members"], "pack.members", MAX_PACK_MEMBERS, 1)
    _integer(item["expanded_bytes"], "pack.expanded_bytes", MAX_PACK_BYTES, 1)
    if not isinstance(item["bucket"], str) or not _BITS.fullmatch(item["bucket"]):
        _fail("pack.bucket", "invalid stable hash prefix")
    return item


def parse_packed_root(raw: bytes) -> dict[str, Any]:
    root = decode_bytes(raw, limit=MAX_ROOT_BYTES, field="root")
    _fields(root, {"schema_version", "store", "packing"}, "root")
    if root["schema_version"] != PACKED_SCHEMA:
        _fail("schema_version", "unsupported packed storage version", "unsupported-schema-version")
    parse_store_root(canonical_bytes(root["store"]))
    packing = _fields(root["packing"], {"compression", "catalog", "pack_catalog", "objects", "packs"}, "packing")
    if not isinstance(packing["compression"], str) or packing["compression"] not in {"stored", "deflate"}:
        _fail("packing.compression", "unsupported compression method")
    _index_descriptor(packing["catalog"])
    _index_descriptor(packing["pack_catalog"])
    for key in ("objects", "packs"):
        _integer(packing[key], "packing." + key, MAX_READ_OBJECTS, 1)
    if (packing["objects"] != packing["catalog"]["count"] or packing["packs"] > packing["objects"]
            or packing["packs"] != packing["pack_catalog"]["count"]):
        _fail("packing", "invalid declared membership counts")
    return root


def _zip_bytes(members: Mapping[str, bytes], compression: str) -> tuple[bytes, dict[str, list[Any]]]:
    output = io.BytesIO()
    method = zipfile.ZIP_STORED if compression == "stored" else zipfile.ZIP_DEFLATED
    coordinates = {}
    with zipfile.ZipFile(output, "w", compression=method, compresslevel=6, allowZip64=False) as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw, compress_type=method, compresslevel=6)
            coordinates[digest(raw)[7:]] = [name, info.header_offset, info.compress_size, len(raw), info.CRC]
    return output.getvalue(), coordinates


def build_packed_store(payload: Mapping[str, Any], *, compression: str = "stored") -> KnowledgeStorePlan:
    if not isinstance(compression, str) or compression not in {"stored", "deflate"}:
        _fail("compression", "must be stored or deflate")
    logical = build_knowledge_store(payload)
    members = {_member_name(raw): raw for raw in logical.objects.values()}
    if len(members) != len(logical.objects):
        _fail("members", "logical identities collide")
    files: dict[str, bytes] = {}
    locations: dict[str, tuple[dict[str, Any], list[Any]]] = {}
    pack_directory: dict[str, dict[str, Any]] = {}

    def pack(group: dict[str, bytes], prefix: str):
        # Size on uncompressed data bounds both stored and expanded packs.
        upper_size = 22 + sum(len(raw) + 76 + 2 * len(name) for name, raw in group.items())
        if (upper_size > PACK_TARGET_BYTES or len(group) > MAX_PACK_MEMBERS) and len(group) > 1:
            if len(prefix) >= 64:
                _fail("pack", "colliding logical members exceed pack limits", "storage-limit")
            groups: dict[str, dict[str, bytes]] = defaultdict(dict)
            for name, raw in group.items():
                groups[_bucket(name)[len(prefix)]][name] = raw
            for bit, child in sorted(groups.items()):
                pack(child, prefix + bit)
            return
        if upper_size > MAX_PACK_BYTES:
            _fail(next(iter(group)), "member and ZIP headers exceed the 8 MiB pack ceiling", "storage-limit")
        raw, coordinates = _zip_bytes(group, compression)
        if len(raw) > MAX_PACK_BYTES:
            _fail("pack", "encoded pack exceeds the 8 MiB ceiling", "storage-limit")
        descriptor = {"hash": digest(raw), "bytes": len(raw), "bucket": prefix,
                      "members": len(group), "expanded_bytes": sum(map(len, group.values()))}
        files[pack_path(descriptor)] = raw
        pack_directory[prefix] = descriptor
        for key, position in coordinates.items():
            locations[key] = (descriptor, position)

    pack(members, "")

    def index(group: dict[str, Any], prefix: str, kind: str):
        node = {"schema_version": PACK_INDEX_SCHEMA, "kind": kind, "prefix": prefix, kind: group}
        raw = canonical_bytes(node)
        if len(raw) > MAX_INDEX_BYTES:
            if len(prefix) >= 64 or len(group) <= 1:
                _fail("index", "unsplittable routing node", "storage-limit")
            groups: dict[str, dict[str, Any]] = defaultdict(dict)
            for key, entry in group.items():
                route = key if kind == "members" else hashlib.sha256(key.encode("ascii")).hexdigest()
                groups[_bits(route)[len(prefix)]][key] = entry
            node = {"schema_version": PACK_INDEX_SCHEMA, "kind": "catalog", "prefix": prefix,
                    "children": {bit: index(child, prefix + bit, kind) for bit, child in sorted(groups.items())}}
            raw = canonical_bytes(node)
        files[index_path(digest(raw))] = raw
        return {"hash": digest(raw), "bytes": len(raw), "count": len(group)}

    catalog = index({key: [descriptor["bucket"], *position] for key, (descriptor, position) in locations.items()}, "", "members")
    pack_catalog = index(pack_directory, "", "packs")
    pack_count = len(pack_directory)
    root = canonical_bytes({"schema_version": PACKED_SCHEMA, "store": json.loads(logical.root_bytes),
                            "packing": {"compression": compression, "catalog": catalog, "pack_catalog": pack_catalog,
                                        "objects": len(locations), "packs": pack_count}})
    parse_packed_root(root)
    if len(files) > MAX_READ_OBJECTS or sum(map(len, files.values())) > MAX_EXPANDED_BYTES:
        _fail("packing", "physical store exceeds its object/byte bound", "storage-limit")
    return KnowledgeStorePlan(root, files, {"packs": pack_count, "indexes": len(files) - pack_count,
        "objects": len(locations), "physical_bytes": sum(map(len, files.values())),
        "logical_object_bytes": sum(map(len, logical.objects.values()))})


def _coordinates(value: Any) -> tuple[str, list[Any]]:
    if not isinstance(value, list) or len(value) != 6:
        _fail("member", "invalid member coordinates")
    bucket, name, offset, compressed, expanded, crc = value
    if not isinstance(bucket, str) or not _BITS.fullmatch(bucket):
        _fail("member", "invalid stable pack bucket")
    if not isinstance(name, str) or not _MEMBER.fullmatch(name) or not _bucket(name).startswith(bucket):
        _fail("member", "member name or stable bucket differs")
    _integer(offset, "member.offset", MAX_PACK_BYTES)
    _integer(compressed, "member.compressed", MAX_PACK_BYTES, 1)
    _integer(expanded, "member.bytes", MAX_OBJECT_BYTES, 1)
    _integer(crc, "member.crc", 0xffffffff)
    if offset + 30 + len(name) + compressed > MAX_PACK_BYTES - 22:
        _fail("member", "member range lies outside its pack")
    return bucket, value[1:]


def _position(value: Any, descriptor: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
    bucket, position = _coordinates(value)
    name, offset, compressed, expanded, _ = position
    if (descriptor["bucket"] != bucket or offset + 30 + len(name) + compressed > descriptor["bytes"] - 22
            or expanded > descriptor["expanded_bytes"]):
        _fail("member", "member range differs from its pack descriptor")
    return descriptor, value[1:]


def decode_member(raw: bytes, position: list[Any], compression: str, commitment: str) -> bytes:
    name, _, compressed, expanded, crc = position
    method = 0 if compression == "stored" else 8
    wanted = (b"PK\x03\x04", 20, 0, method, 0, 33, crc, compressed, expanded, len(name), 0)
    if len(raw) != 30 + len(name) + compressed or _LOCAL_HEADER.unpack(raw[:30]) != wanted:
        _fail("member", "ZIP header differs from authenticated coordinates")
    if raw[30:30 + len(name)] != name.encode("ascii"):
        _fail("member", "ZIP member name differs from its locator")
    body = raw[30 + len(name):]
    if method == 8:
        try:
            decoder = zlib.decompressobj(-15)
            content = decoder.decompress(body, expanded + 1)
        except zlib.error as exc:
            raise KnowledgeStorageError("member", "invalid DEFLATE member") from exc
        if len(content) != expanded or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
            _fail("member", "DEFLATE stream exceeds or differs from its declared expansion", "storage-limit")
    else:
        content = body
    if len(content) != expanded or zlib.crc32(content) != crc or digest(content) != commitment:
        _fail("member", "member checksum, size or logical commitment differs")
    if _member_name(content) != name:
        _fail("member", "logical object identity differs from its member name")
    return content


def validate_pack(raw: bytes, descriptor: dict[str, Any], compression: str) -> dict[str, list[Any]]:
    """Validate a complete bounded archive, including all otherwise unread metadata."""
    _pack_descriptor(descriptor)
    if len(raw) != descriptor["bytes"] or digest(raw) != descriptor["hash"]:
        _fail("pack", "pack checksum or size differs")
    footer = _END.unpack(raw[-22:])
    sig, disk, start_disk, count_here, count, directory_bytes, start, comment = footer
    if (sig != b"PK\x05\x06" or disk or start_disk or comment or count_here != count
            or count != descriptor["members"] or directory_bytes > MAX_DIRECTORY_BYTES
            or start + directory_bytes != len(raw) - 22):
        _fail("pack", "unsupported or unbounded ZIP directory")
    positions = {}
    previous_name = ""
    offset = expanded_total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if len(infos) != count:
                _fail("pack", "directory membership differs")
            for info in infos:
                name = info.filename
                if (not _MEMBER.fullmatch(name) or info.orig_filename != name or name <= previous_name or info.header_offset != offset
                        or info.flag_bits or info.extra or info.comment or info.volume or info.reserved
                        or info.create_system != 3 or info.create_version != 20 or info.extract_version != 20
                        or info.external_attr != 0o100644 << 16 or info.internal_attr
                        or info.date_time != (1980, 1, 1, 0, 0, 0)
                        or info.compress_type != (0 if compression == "stored" else 8)):
                    _fail("pack", "noncanonical ZIP metadata, order or membership")
                value = [descriptor["bucket"], name, offset, info.compress_size, info.file_size, info.CRC]
                _, position = _position(value, descriptor)
                end = offset + 30 + len(name) + info.compress_size
                # The full index audit below binds this independently computed identity.
                chunk = raw[offset:end]
                if compression == "stored":
                    content = chunk[30 + len(name):]
                else:
                    decoder = zlib.decompressobj(-15)
                    content = decoder.decompress(chunk[30 + len(name):], info.file_size + 1)
                commitment = digest(content)
                decode_member(chunk, position, compression, commitment)
                if commitment[7:] in positions:
                    _fail("pack", "duplicate logical object")
                positions[commitment[7:]] = position
                previous_name, offset = name, end
                expanded_total += info.file_size
                if expanded_total > MAX_PACK_BYTES:
                    _fail("pack", "expanded pack exceeds its ceiling", "storage-limit")
    except (zipfile.BadZipFile, zlib.error, struct.error, UnicodeError) as exc:
        raise KnowledgeStorageError("pack", "invalid ZIP archive") from exc
    if offset != start or expanded_total != descriptor["expanded_bytes"]:
        _fail("pack", "directory offset or expanded total differs")
    return positions


def inspect_pack(raw: bytes, relative: str) -> dict[str, Any]:
    """Recognize a complete generated archive for diagnostics and orphan cleanup."""
    match = PACK_NAME.fullmatch(relative)
    if match is None or not 22 <= len(raw) <= MAX_PACK_BYTES or digest(raw)[7:] != match[2]:
        _fail("pack", "unrecognized archive identity")
    footer = _END.unpack(raw[-22:])
    if (footer[0] != b"PK\x05\x06" or footer[1] or footer[2] or footer[3] != footer[4]
            or not 0 < footer[4] <= MAX_PACK_MEMBERS or footer[5] > MAX_DIRECTORY_BYTES
            or footer[6] + footer[5] != len(raw) - 22 or footer[7]):
        _fail("pack", "unbounded ZIP directory", "storage-limit")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_PACK_MEMBERS or infos[0].compress_type not in {0, 8}:
                _fail("pack", "unsupported archive membership or compression")
            compression = "stored" if infos[0].compress_type == 0 else "deflate"
            descriptor = {"hash": digest(raw), "bytes": len(raw), "bucket": "" if match[3] == "root" else match[3],
                          "members": len(infos), "expanded_bytes": sum(i.file_size for i in infos)}
    except (zipfile.BadZipFile, UnicodeError) as exc:
        raise KnowledgeStorageError("pack", "invalid ZIP archive") from exc
    positions = validate_pack(raw, descriptor, compression)
    return {"descriptor": descriptor, "compression": compression, "objects": len(positions)}


class PackedKnowledgeStoreReader(KnowledgeStoreReader):
    def __init__(self, root_bytes: bytes, read_file: Callable[[str, int], bytes], *,
                 read_range: RangeReader | None = None, **limits):
        packed = parse_packed_root(root_bytes)
        self.packing = packed["packing"]
        self.read_file = read_file
        self.read_range = read_range
        self.physical_objects: dict[str, bytes] = {}
        self._indexes: dict[str, dict[str, Any]] = {}
        self._pack_descriptors: dict[str, dict[str, Any]] = {}
        self._selected_locations: dict[str, tuple[dict[str, Any], list[Any]]] = {}
        self._verified_pack_hashes: set[str] = set()
        self._physical_bytes = len(root_bytes)
        super().__init__(canonical_bytes(packed["store"]), self._read_member, **limits)
        self.bytes_read += len(root_bytes) - len(self.root_bytes)
        self.root_bytes = root_bytes
        self._check_budget()

    def _physical(self, path: str, size: int) -> bytes:
        if path not in self.physical_objects:
            if self._physical_bytes + size > self.max_bytes or len(self.physical_objects) >= self.max_objects:
                _fail("read", "physical storage budget exhausted", "storage-budget-exhausted")
            raw = self.read_file(path, size)
            if not isinstance(raw, bytes):
                _fail(path, "physical reads must return immutable bytes")
            self._physical_bytes += len(raw)
            if len(raw) != size:
                _fail(path, "physical file size differs")
            self.physical_objects[path] = raw
        if len(self.physical_objects[path]) != size:
            _fail(path, "inconsistent physical file size")
        return self.physical_objects[path]

    def _index(self, descriptor: dict[str, Any], prefix: str, leaf_kind: str = "members") -> dict[str, Any]:
        _index_descriptor(descriptor)
        path = index_path(descriptor["hash"])
        raw = self._physical(path, descriptor["bytes"])
        node = self._indexes.get(path)
        if node is None:
            if digest(raw) != descriptor["hash"]:
                _fail(path, "routing index checksum differs")
            node = decode_bytes(raw, limit=MAX_INDEX_BYTES, field=path)
            _fields(node, {"schema_version", "prefix", "kind"} |
                    ({"children"} if node.get("kind") == "catalog" else {leaf_kind}), path)
            if node["schema_version"] != PACK_INDEX_SCHEMA or node["prefix"] != prefix or not _BITS.fullmatch(prefix):
                _fail(path, "routing schema or prefix differs")
            if node["kind"] == "catalog":
                children = node["children"]
                if not isinstance(children, dict) or not children or not set(children) <= {"0", "1"} or len(prefix) >= 64:
                    _fail(path, "invalid routing children")
                for child in children.values():
                    _index_descriptor(child)
            elif node["kind"] == leaf_kind:
                members = node[leaf_kind]
                if not isinstance(members, dict) or not members:
                    _fail(path, "invalid member table")
                for key, value in members.items():
                    if leaf_kind == "members":
                        if not _HEX.fullmatch(key):
                            _fail(path, "invalid logical object key")
                        route = key
                        _coordinates(value)
                    else:
                        _pack_descriptor(value)
                        if key != value["bucket"]:
                            _fail(path, "pack key differs from its stable bucket")
                        route = hashlib.sha256(key.encode("ascii")).hexdigest()
                        previous = self._pack_descriptors.setdefault(value["hash"], value)
                        if previous != value:
                            _fail(path, "inconsistent pack descriptor")
                    if not _bits(route).startswith(prefix):
                        _fail(path, "member key lies outside its routing prefix")
            else:
                _fail(path, "unsupported routing kind")
            self._indexes[path] = node
        if node["prefix"] != prefix or node["kind"] not in {"catalog", leaf_kind}:
            _fail(path, "routing node reused at a different prefix")
        count = len(node[leaf_kind]) if node["kind"] == leaf_kind else sum(d["count"] for d in node["children"].values())
        if count != descriptor["count"]:
            _fail(path, "routing member count differs")
        return node

    def _find_entry(self, key: str, leaf_kind: str) -> Any:
        prefix = ""
        descriptor = self.packing["catalog" if leaf_kind == "members" else "pack_catalog"]
        route = key if leaf_kind == "members" else hashlib.sha256(key.encode("ascii")).hexdigest()
        while True:
            node = self._index(descriptor, prefix, leaf_kind)
            if node["kind"] == leaf_kind:
                if key not in node[leaf_kind]:
                    _fail("index", "required logical object has no member")
                return node[leaf_kind][key]
            bit = _bits(route)[len(prefix)]
            if bit not in node["children"]:
                _fail("index", "required logical object has no routing branch")
            prefix, descriptor = prefix + bit, node["children"][bit]

    def _find(self, key: str) -> tuple[dict[str, Any], list[Any]]:
        value = self._find_entry(key, "members")
        return _position(value, self._find_entry(value[0], "packs"))

    def _pack(self, descriptor: dict[str, Any]) -> bytes:
        raw = self._physical(pack_path(descriptor), descriptor["bytes"])
        if descriptor["hash"] not in self._verified_pack_hashes:
            if digest(raw) != descriptor["hash"]:
                _fail("pack", "pack checksum differs")
            self._verified_pack_hashes.add(descriptor["hash"])
        return raw

    def _read_member(self, logical_path: str, maximum: int) -> bytes:
        key = logical_path.rsplit("/", 1)[-1][:-5]
        descriptor, position = self._find(key)
        name, offset, compressed, expanded, _ = position
        if expanded > maximum:
            _fail("member", "expanded object differs from its logical descriptor", "storage-limit")
        length = 30 + len(name) + compressed
        if self.read_range is None:
            raw = self._pack(descriptor)[offset:offset + length]
        else:
            if self._physical_bytes + length > self.max_bytes:
                _fail("read", "member read budget exhausted", "storage-budget-exhausted")
            raw = self.read_range(pack_path(descriptor), offset, length, descriptor["bytes"])
            self._physical_bytes += len(raw)
        content = decode_member(raw, position, self.packing["compression"], "sha256:" + key)
        self._selected_locations[key] = descriptor, position
        return content

    def materialize(self, *, audit_routes: bool = True) -> dict[str, Any]:
        payload = super().materialize(audit_routes=audit_routes)
        locations = {}
        pack_locations = {}
        def walk(descriptor, prefix, kind, output):
            node = self._index(descriptor, prefix, kind)
            if node["kind"] == kind:
                for key, value in node[kind].items():
                    if key in output:
                        _fail("index", "duplicate routed object")
                    output[key] = value
            else:
                for bit, child in node["children"].items():
                    walk(child, prefix + bit, kind, output)
        walk(self.packing["catalog"], "", "members", locations)
        walk(self.packing["pack_catalog"], "", "packs", pack_locations)
        if any(value[0] not in pack_locations for value in locations.values()):
            _fail("index", "member references an absent pack bucket")
        locations = {key: _position(value, pack_locations[value[0]]) for key, value in locations.items()}
        expected = {path.rsplit("/", 1)[-1][:-5] for path in self.objects}
        if set(locations) != expected or len(locations) != self.packing["objects"]:
            _fail("index", "locator membership differs from the complete logical store")
        if len(self._pack_descriptors) != self.packing["packs"]:
            _fail("packing", "pack count differs")
        actual = {}
        buckets = []
        for descriptor in self._pack_descriptors.values():
            buckets.append(descriptor["bucket"])
            for key, position in validate_pack(self._pack(descriptor), descriptor, self.packing["compression"]).items():
                if key in actual:
                    _fail("packing", "logical object duplicated across packs")
                actual[key] = descriptor, position
        ordered = sorted(buckets)
        if any(b.startswith(a) for a, b in zip(ordered, ordered[1:])):
            _fail("packing", "pack bucket boundaries overlap")
        if actual != locations:
            _fail("index", "locator coordinates differ from complete archive membership")
        return payload

    def select(self, selectors, *, max_records: int = 1000) -> KnowledgeSlice:
        payload = super().select(selectors, max_records=max_records).to_payload()
        payload.update(schema_version="llm-wiki-knowledge-slice/v2", storage_format="packed-v3",
                       archive_validation_scope="selected-members")
        payload["work"]["physical_bytes"] = self._physical_bytes
        return KnowledgeSlice(canonical_bytes(payload))


def open_knowledge_store(root_bytes: bytes, read_file: Callable[[str, int], bytes], *,
                         read_range: RangeReader | None = None, **limits) -> KnowledgeStoreReader:
    version = json.loads(root_bytes).get("schema_version")
    if version == PACKED_SCHEMA:
        return PackedKnowledgeStoreReader(root_bytes, read_file, read_range=read_range, **limits)
    return KnowledgeStoreReader(root_bytes, read_file, **limits)


def physical_objects(reader: KnowledgeStoreReader) -> Mapping[str, bytes]:
    return reader.physical_objects if isinstance(reader, PackedKnowledgeStoreReader) else reader.objects


def build_storage(payload: Mapping[str, Any], storage_format: str) -> KnowledgeStorePlan:
    if storage_format in PACKED_FORMATS:
        return build_packed_store(payload, compression="deflate" if storage_format.endswith("-deflate") else "stored")
    if storage_format == "sharded-v2":
        return build_knowledge_store(payload)
    _fail("format", "unsupported object storage format")
