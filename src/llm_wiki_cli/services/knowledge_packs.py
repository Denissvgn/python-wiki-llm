"""Immutable indexed ZIP containers for unchanged logical knowledge objects.

Selected readers authenticate bounded member ranges, not an entire archive.
Full readers additionally validate ZIP structure and exact locator membership.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, MutableMapping
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
LOCAL_PACKED_SCHEMA = "llm-wiki-knowledge/v4"
PACKED_SCHEMAS = (PACKED_SCHEMA, LOCAL_PACKED_SCHEMA)
LOCAL_PACK_PROFILE = "local-v1"
LOCAL_PACK_TARGET_BYTES = 1_048_576
LOCAL_INDEX_ROWS = 24
PACK_INDEX_SCHEMA = "llm-wiki-knowledge-pack-index/v1"
PAGE_INDEX_SCHEMA = "llm-wiki-knowledge-pack-index/v2"
INDEX_PAGE_DIRECTORY = ".llm-wiki-knowledge/index-pages"
INDEX_PAGE_BYTES = 1_048_576
INDEX_PAGE_NAME = re.compile(r"\.llm-wiki-knowledge/index-pages/([0-9a-f]{2})/(\1[0-9a-f]{62})\.bin\Z")
PACK_DIRECTORY = ".llm-wiki-knowledge/packs"
PACK_INDEX_DIRECTORY = ".llm-wiki-knowledge/pack-index"
PACK_TARGET_BYTES = 4_194_304
MAX_PACK_BYTES = 8_388_608
MAX_INDEX_BYTES = 65_536
MAX_PACK_MEMBERS = 512
MAX_DIRECTORY_BYTES = 262_144
PACKED_FORMATS = frozenset({"packed-v3", "packed-v3-deflate", "packed-v4", "packed-v4-deflate"})
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


def index_page_path(commitment):
    value = _hash(commitment, "index-page.hash")[7:]
    return f"{INDEX_PAGE_DIRECTORY}/{value[:2]}/{value}.bin"


def _index_descriptor(value: Any, *, paged: bool = False) -> dict[str, Any]:
    item = _fields(value, {"hash", "bytes", "count"} | ({"extent"} if paged else set()), "index")
    _hash(item["hash"], "index.hash")
    _integer(item["bytes"], "index.bytes", MAX_INDEX_BYTES, 1)
    _integer(item["count"], "index.count", MAX_READ_OBJECTS, 1)
    if paged:
        extent = _fields(item["extent"], {"container", "offset", "file_bytes"}, "index.extent")
        _hash(extent["container"], "index.extent.container")
        _integer(extent["offset"], "index.extent.offset", INDEX_PAGE_BYTES)
        _integer(extent["file_bytes"], "index.extent.file_bytes", INDEX_PAGE_BYTES, 1)
        if extent["offset"] + item["bytes"] > extent["file_bytes"]:
            _fail("index.extent", "page range exceeds its container")
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
    if root["schema_version"] not in PACKED_SCHEMAS:
        _fail("schema_version", "unsupported packed storage version", "unsupported-schema-version")
    parse_store_root(canonical_bytes(root["store"]))
    local = root["schema_version"] == LOCAL_PACKED_SCHEMA
    packing = _fields(root["packing"], {"compression", "catalog", "pack_catalog", "objects", "packs"}
                      | ({"profile"} if local else set()), "packing")
    if local and packing["profile"] != LOCAL_PACK_PROFILE:
        _fail("packing.profile", "unsupported locality profile", "unsupported-schema-version")
    if not isinstance(packing["compression"], str) or packing["compression"] not in {"stored", "deflate"}:
        _fail("packing.compression", "unsupported compression method")
    _index_descriptor(packing["catalog"], paged=local)
    _index_descriptor(packing["pack_catalog"], paged=local)
    for key in ("objects", "packs"):
        _integer(packing[key], "packing." + key, MAX_READ_OBJECTS, 1)
    if (packing["objects"] != packing["catalog"]["count"] or packing["packs"] > packing["objects"]
            or packing["packs"] != packing["pack_catalog"]["count"]):
        _fail("packing", "invalid declared membership counts")
    return root


def packed_format(root: Mapping[str, Any]) -> str:
    """Return the explicitly adopted physical format of a validated packed root."""
    version = "packed-v4" if root["schema_version"] == LOCAL_PACKED_SCHEMA else "packed-v3"
    return version + ("-deflate" if root["packing"]["compression"] == "deflate" else "")


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


def _zip_reusing(members: Mapping[str, bytes], compression: str,
                reusable: Mapping[str, tuple[bytes, int]]) -> tuple[bytes, dict[str, list[Any]]]:
    """Write the pinned ZIP profile, copying verified compressed payloads verbatim."""
    output = io.BytesIO()
    central = io.BytesIO()
    coordinates = {}
    method = 0 if compression == "stored" else 8
    for name, raw in sorted(members.items()):
        retained = reusable.get(name)
        if retained is not None:
            body, crc = retained
        else:
            crc = zlib.crc32(raw)
            if method == 8:
                encoder = zlib.compressobj(6, zlib.DEFLATED, -15)
                body = encoder.compress(raw) + encoder.flush()
            else:
                body = raw
        position = [name, output.tell(), len(body), len(raw), crc]
        coordinates[digest(raw)[7:]] = position
        output.write(_member_header(position, compression))
        output.write(body)
        central.write(struct.pack("<4s6H3I5H2I", b"PK\x01\x02", 788, 20, 0, method, 0, 33,
                                  crc, len(body), len(raw), len(name), 0, 0, 0, 0,
                                  0o100644 << 16, position[1]))
        central.write(name.encode("ascii"))
    offset = output.tell()
    directory = central.getvalue()
    output.write(directory)
    output.write(_END.pack(b"PK\x05\x06", 0, 0, len(members), len(members), len(directory), offset, 0))
    return output.getvalue(), coordinates


def build_packed_store(payload: Mapping[str, Any], *, compression: str = "stored", prior=None, objects=None,
                       profile: str = "standard") -> KnowledgeStorePlan:
    if not isinstance(compression, str) or compression not in {"stored", "deflate"}:
        _fail("compression", "must be stored or deflate")
    if not isinstance(profile, str) or profile not in {"standard", LOCAL_PACK_PROFILE}:
        _fail("profile", "unsupported packing profile")
    from contextlib import nullcontext
    from .storage_spool import ByteSpool
    with ByteSpool() if objects is not None else nullcontext(None) as staging:
        logical = build_knowledge_store(payload, objects=staging)
        return _pack_logical(logical, compression, prior, objects, profile)


def _pack_logical(logical, compression, prior, objects, profile="standard"):
    local = profile == LOCAL_PACK_PROFILE
    target_bytes = LOCAL_PACK_TARGET_BYTES if local else PACK_TARGET_BYTES
    members = {name: path for path, name in logical.member_names.items()}
    sizes = {name: len(logical.objects[path]) for name, path in members.items()}
    if len(members) != len(logical.objects):
        _fail("members", "logical identities collide")
    files = {} if objects is None else objects
    locations: dict[str, tuple[dict[str, Any], list[Any]]] = {}
    pack_directory: dict[str, dict[str, Any]] = {}
    prior_reader = None
    reused_packs = reused_members = 0
    if prior is not None:
        from .knowledge_artifacts import require_validated_artifacts, validated_artifact_bytes
        require_validated_artifacts(prior)
        _, previous_root = validated_artifact_bytes(prior)
        if json.loads(previous_root).get("schema_version") in PACKED_SCHEMAS:
            previous = parse_packed_root(previous_root)
            if (previous["packing"]["compression"] == compression
                    and previous["packing"].get("profile", "standard") == profile):
                prior_reader = PackedKnowledgeStoreReader(previous_root, lambda path, _: prior.storage_objects[path])

    def previous_member(name, content):
        if prior_reader is None:
            return None
        key = digest(content)[7:]
        try:
            descriptor, position = prior_reader._find(key)
        except KnowledgeStorageError as exc:
            if "has no member" in exc.message or "has no routing branch" in exc.message:
                return None
            raise
        if position[0] != name or position[3] != len(content):
            _fail("reuse", "prior logical identity differs")
        return descriptor, position

    def pack(group: dict[str, str], prefix: str):
        nonlocal reused_packs, reused_members
        # Size on uncompressed data bounds both stored and expanded packs.
        upper_size = 22 + sum(sizes[name] + 76 + 2 * len(name) for name in group)
        if (upper_size > target_bytes or len(group) > MAX_PACK_MEMBERS) and len(group) > 1:
            if len(prefix) >= 64:
                _fail("pack", "colliding logical members exceed pack limits", "storage-limit")
            groups: dict[str, dict[str, str]] = defaultdict(dict)
            for name, raw in group.items():
                groups[_bucket(name)[len(prefix)]][name] = raw
            for bit, child in sorted(groups.items()):
                pack(child, prefix + bit)
            return
        if upper_size > MAX_PACK_BYTES:
            _fail(next(iter(group)), "member and ZIP headers exceed the 8 MiB pack ceiling", "storage-limit")
        encoded = {name: logical.objects[path] for name, path in group.items()}
        previous = {name: location for name, content in encoded.items()
                    if (location := previous_member(name, content)) is not None}
        descriptors = {location[0]["hash"] for location in previous.values()}
        descriptor = next(iter(previous.values()))[0] if previous else None
        if (len(previous) == len(group) and len(descriptors) == 1 and descriptor is not None
                and descriptor["bucket"] == prefix and descriptor["members"] == len(group)):
            assert prior_reader is not None
            raw = prior_reader._pack(descriptor)
            coordinates = {digest(encoded[name])[7:]: position for name, (_, position) in previous.items()}
            reused_packs += 1
        elif previous:
            assert prior_reader is not None
            reusable = {}
            for name, (old_descriptor, position) in previous.items():
                _, offset, size, _, crc = position
                start = offset + 30 + len(name)
                reusable[name] = (prior_reader._pack(old_descriptor)[start:start + size], crc)
            raw, coordinates = _zip_reusing(encoded, compression, reusable)
        else:
            raw, coordinates = _zip_bytes(encoded, compression)
        reused_members += len(previous)
        if len(raw) > MAX_PACK_BYTES:
            _fail("pack", "encoded pack exceeds the 8 MiB ceiling", "storage-limit")
        descriptor = {"hash": digest(raw), "bytes": len(raw), "bucket": prefix,
                      "members": len(group), "expanded_bytes": sum(sizes[name] for name in group)}
        files[pack_path(descriptor)] = raw
        pack_directory[prefix] = descriptor
        for key, position in coordinates.items():
            locations[key] = (descriptor, position)

    pack(members, "")

    def index(group: dict[str, Any], prefix: str, kind: str):
        node = {"schema_version": PACK_INDEX_SCHEMA, "kind": kind, "prefix": prefix, kind: group}
        raw = canonical_bytes(node)
        if len(raw) > MAX_INDEX_BYTES or (local and len(group) > LOCAL_INDEX_ROWS):
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

    member_directory = {key: [descriptor["bucket"], *position] for key, (descriptor, position) in locations.items()}
    if local:
        catalog, pack_catalog = _paged_indexes(member_directory, pack_directory, files)
    else:
        catalog = index(member_directory, "", "members")
        pack_catalog = index(pack_directory, "", "packs")
    pack_count = len(pack_directory)
    root = canonical_bytes({"schema_version": LOCAL_PACKED_SCHEMA if local else PACKED_SCHEMA, "store": json.loads(logical.root_bytes),
                            "packing": {"compression": compression, "catalog": catalog, "pack_catalog": pack_catalog,
                                        "objects": len(locations), "packs": pack_count,
                                        **({"profile": profile} if local else {})}})
    parse_packed_root(root)
    if len(files) > MAX_READ_OBJECTS or sum(map(len, files.values())) > MAX_EXPANDED_BYTES:
        _fail("packing", "physical store exceeds its object/byte bound", "storage-limit")
    return KnowledgeStorePlan(root, files, {"packs": pack_count, "indexes": len(files) - pack_count,
        "objects": len(locations), "physical_bytes": sum(map(len, files.values())),
        "logical_object_bytes": sum(sizes.values()),
        "reused_packs": reused_packs, "reused_members": reused_members,
        "encoded_members": len(locations) - reused_members})


def _paged_indexes(members, packs, files):
    """Pack locator pages bottom-up, so every extent has an acyclic commitment."""
    levels = defaultdict(list)

    def tree(group, prefix, kind):
        node = {"schema_version": PAGE_INDEX_SCHEMA, "kind": kind, "prefix": prefix, kind: group}
        children = {}
        height = 0
        if len(group) > LOCAL_INDEX_ROWS or len(canonical_bytes(node)) > MAX_INDEX_BYTES:
            if len(prefix) >= 64 or len(group) <= 1:
                _fail("index", "unsplittable routing page", "storage-limit")
            groups = defaultdict(dict)
            for key, value in group.items():
                route = key if kind == "members" else hashlib.sha256(key.encode("ascii")).hexdigest()
                groups[_bits(route)[len(prefix)]][key] = value
            children = {bit: tree(child, prefix + bit, kind) for bit, child in sorted(groups.items())}
            height = 1 + max(child["height"] for child in children.values())
        item = {"node": node, "children": children, "height": height, "count": len(group), "descriptor": None}
        levels[height].append(item)
        return item

    roots = tree(members, "", "members"), tree(packs, "", "packs")
    for height in sorted(levels):
        encoded = []
        for item in sorted(levels[height], key=lambda i: (i["node"]["kind"], i["node"]["prefix"])):
            node = item["node"]
            if item["children"]:
                node = {"schema_version": PAGE_INDEX_SCHEMA, "kind": "catalog", "prefix": node["prefix"],
                        "children": {bit: child["descriptor"] for bit, child in item["children"].items()}}
            raw = canonical_bytes(node)
            if len(raw) > MAX_INDEX_BYTES:
                _fail("index", "routing page exceeds the byte bound", "storage-limit")
            encoded.append((item, raw))
        group, size = [], 0

        def emit(batch):
            raw = b"".join(content for _, content in batch)
            commitment = digest(raw)
            files[index_page_path(commitment)] = raw
            offset = 0
            for item, content in batch:
                item["descriptor"] = {"hash": digest(content), "bytes": len(content), "count": item["count"],
                    "extent": {"container": commitment, "offset": offset, "file_bytes": len(raw)}}
                offset += len(content)
        for item, raw in encoded:
            if group and size + len(raw) > INDEX_PAGE_BYTES:
                emit(group)
                group, size = [], 0
            group.append((item, raw))
            size += len(raw)
        if group:
            emit(group)
    return tuple(root["descriptor"] for root in roots)


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


def inspect_index_pages(raw: bytes, relative: str) -> dict[str, Any]:
    """Validate intrinsic page-container syntax without claiming reachability."""
    match = INDEX_PAGE_NAME.fullmatch(relative)
    if match is None or not 0 < len(raw) <= INDEX_PAGE_BYTES or digest(raw)[7:] != match[2]:
        _fail("index-pages", "invalid content-addressed page container")
    count = 0
    for line in raw.splitlines(keepends=True):
        node = decode_bytes(line, limit=MAX_INDEX_BYTES, field=relative)
        kind, prefix = node.get("kind"), node.get("prefix")
        if kind not in {"catalog", "members", "packs"} or not isinstance(prefix, str) or not _BITS.fullmatch(prefix):
            _fail(relative, "invalid routing page")
        field = "children" if kind == "catalog" else kind
        _fields(node, {"schema_version", "kind", "prefix", field}, relative)
        if node["schema_version"] != PAGE_INDEX_SCHEMA or canonical_bytes(node) != line:
            _fail(relative, "routing pages must be canonical v2 objects")
        entries = node[field]
        if not isinstance(entries, dict) or not entries:
            _fail(relative, "routing page requires entries")
        if kind == "catalog":
            if not set(entries) <= {"0", "1"} or len(prefix) >= 64:
                _fail(relative, "invalid page branches")
            for descriptor in entries.values():
                _index_descriptor(descriptor, paged=True)
        else:
            if len(entries) > LOCAL_INDEX_ROWS:
                _fail(relative, "routing page exceeds its row bound")
            for key, value in entries.items():
                if kind == "members":
                    if not _HEX.fullmatch(key):
                        _fail(relative, "invalid logical object key")
                    _coordinates(value)
                    route = key
                else:
                    _pack_descriptor(value)
                    if key != value["bucket"]:
                        _fail(relative, "pack bucket differs")
                    route = hashlib.sha256(key.encode("ascii")).hexdigest()
                if not _bits(route).startswith(prefix):
                    _fail(relative, "routing key exceeds its prefix")
        count += 1
    return {"pages": count, "bytes": len(raw)}


def _position(value: Any, descriptor: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]:
    bucket, position = _coordinates(value)
    name, offset, compressed, expanded, _ = position
    if (descriptor["bucket"] != bucket or offset + 30 + len(name) + compressed > descriptor["bytes"] - 22
            or expanded > descriptor["expanded_bytes"]):
        _fail("member", "member range differs from its pack descriptor")
    return descriptor, value[1:]


def _member_header(position: list[Any], compression: str) -> bytes:
    name, _, compressed, expanded, crc = position
    return _LOCAL_HEADER.pack(b"PK\x03\x04", 20, 0, 0 if compression == "stored" else 8,
                              0, 33, crc, compressed, expanded, len(name), 0) + name.encode("ascii")


def decode_member(raw: bytes, position: list[Any], compression: str, commitment: str | None,
                  *, verify_name: bool = True) -> bytes:
    name, _, compressed, expanded, crc = position
    method = 0 if compression == "stored" else 8
    if len(raw) != 30 + len(name) + compressed or not raw.startswith(_member_header(position, compression)):
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
    if (len(content) != expanded or zlib.crc32(content) != crc
            or (commitment is not None and digest(content) != commitment)):
        _fail("member", "member checksum, size or logical commitment differs")
    if verify_name and _member_name(content) != name:
        _fail("member", "logical object identity differs from its member name")
    return content


def _pack_structure(raw: bytes, descriptor: dict[str, Any], compression: str) -> dict[str, list[Any]]:
    """Check all container/header bytes; member content validation is separate."""
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
                if raw[offset:offset + 30 + len(name)] != _member_header(position, compression):
                    _fail("pack", "local header differs from its complete directory")
                positions[name] = position
                previous_name, offset = name, end
                expanded_total += info.file_size
                if expanded_total > MAX_PACK_BYTES:
                    _fail("pack", "expanded pack exceeds its ceiling", "storage-limit")
    except (zipfile.BadZipFile, zlib.error, struct.error, UnicodeError) as exc:
        raise KnowledgeStorageError("pack", "invalid ZIP archive") from exc
    if offset != start or expanded_total != descriptor["expanded_bytes"]:
        _fail("pack", "directory offset or expanded total differs")
    return positions


def validate_pack(raw: bytes, descriptor: dict[str, Any], compression: str) -> dict[str, list[Any]]:
    """Validate a whole archive and each logical member, inflating each once."""
    result = {}
    for position in _pack_structure(raw, descriptor, compression).values():
        name, offset, compressed, _, _ = position
        content = decode_member(raw[offset:offset + 30 + len(name) + compressed], position, compression, None)
        key = digest(content)[7:]
        if key in result:
            _fail("pack", "duplicate logical object")
        result[key] = position
    return result


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
        self.storage_format = packed_format(packed).removesuffix("-deflate")
        self.packing = packed["packing"]
        self.read_file = read_file
        self.read_range = read_range
        self.physical_objects: MutableMapping[str, bytes] = {}
        self._indexes: MutableMapping[str, dict[str, Any]] = {}
        self._index_extents: dict[str, dict[str, Any]] = {}
        self._verified_index_containers: set[str] = set()
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
        paged = self.packing.get("profile") == LOCAL_PACK_PROFILE
        _index_descriptor(descriptor, paged=paged)
        path = index_path(descriptor["hash"])
        if paged:
            previous = self._index_extents.setdefault(path, descriptor)
            if previous != descriptor:
                _fail(path, "inconsistent page extent")
            extent = descriptor["extent"]
            container = index_page_path(extent["container"])
            if path in self._indexes:
                raw = None
            elif self.read_range is None:
                content = self._physical(container, extent["file_bytes"])
                if extent["container"] not in self._verified_index_containers:
                    if digest(content) != extent["container"]:
                        _fail(container, "index container checksum differs")
                    self._verified_index_containers.add(extent["container"])
                raw = content[extent["offset"]:extent["offset"] + descriptor["bytes"]]
            else:
                if self._physical_bytes + descriptor["bytes"] > self.max_bytes:
                    _fail("read", "index page budget exhausted", "storage-budget-exhausted")
                raw = self.read_range(container, extent["offset"], descriptor["bytes"], extent["file_bytes"])
                self._physical_bytes += len(raw)
        else:
            raw = self._physical(path, descriptor["bytes"])
        node = self._indexes.get(path)
        if node is None:
            if raw is None or len(raw) != descriptor["bytes"]:
                _fail(path, "index page size differs")
            if digest(raw) != descriptor["hash"]:
                _fail(path, "routing index checksum differs")
            node = decode_bytes(raw, limit=MAX_INDEX_BYTES, field=path)
            if paged and canonical_bytes(node) != raw:
                _fail(path, "index pages must use canonical JSON")
            _fields(node, {"schema_version", "prefix", "kind"} |
                    ({"children"} if node.get("kind") == "catalog" else {leaf_kind}), path)
            if node["schema_version"] != (PAGE_INDEX_SCHEMA if paged else PACK_INDEX_SCHEMA) or node["prefix"] != prefix or not _BITS.fullmatch(prefix):
                _fail(path, "routing schema or prefix differs")
            if node["kind"] == "catalog":
                children = node["children"]
                if not isinstance(children, dict) or not children or not set(children) <= {"0", "1"} or len(prefix) >= 64:
                    _fail(path, "invalid routing children")
                for child in children.values():
                    _index_descriptor(child, paged=paged)
            elif node["kind"] == leaf_kind:
                members = node[leaf_kind]
                if not isinstance(members, dict) or not members:
                    _fail(path, "invalid member table")
                if self.packing.get("profile") == LOCAL_PACK_PROFILE and len(members) > LOCAL_INDEX_ROWS:
                    _fail(path, "locality index exceeds its row bound", "storage-limit")
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
        content = decode_member(raw, position, self.packing["compression"], "sha256:" + key, verify_name=False)
        self._selected_locations[key] = descriptor, position
        return content

    def _node(self, desc, collection, prefix):
        node = super()._node(desc, collection, prefix)
        expected_name = f"{collection}/{node['prefix'] or 'root'}.json"
        if self._selected_locations[desc["hash"][7:]][1][0] != expected_name:
            _fail("member", "logical object identity differs from its member name")
        return node

    def materialize(self, *, audit_routes: bool = True) -> dict[str, Any]:
        payload = super().materialize(audit_routes=audit_routes)
        self.audit_containers()
        return payload

    def audit_containers(self) -> None:
        """Reconcile all captured logical members with complete archive routing."""
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
        verified = {}
        for key, (descriptor, position) in self._selected_locations.items():
            slot = descriptor["hash"], position[0]
            if slot in verified:
                _fail("packing", "duplicate logical member name")
            verified[slot] = key, position
        for descriptor in self._pack_descriptors.values():
            buckets.append(descriptor["bucket"])
            for name, position in _pack_structure(self._pack(descriptor), descriptor, self.packing["compression"]).items():
                observed = verified.get((descriptor["hash"], name))
                if observed is None or observed[1] != position:
                    _fail("index", "archive member was not validated at its committed coordinates")
                key = observed[0]
                if key in actual:
                    _fail("packing", "logical object duplicated across packs")
                actual[key] = descriptor, position
        ordered = sorted(buckets)
        if any(b.startswith(a) for a, b in zip(ordered, ordered[1:])):
            _fail("packing", "pack bucket boundaries overlap")
        if actual != locations:
            _fail("index", "locator coordinates differ from complete archive membership")
        containers = defaultdict(list)
        for descriptor in self._index_extents.values():
            extent = descriptor["extent"]
            containers[extent["container"]].append((extent["offset"], descriptor["bytes"], extent["file_bytes"]))
        for commitment, extents in containers.items():
            position = 0
            content = self._physical(index_page_path(commitment), extents[0][2])
            if digest(content) != commitment:
                _fail("index", "index container checksum differs")
            for offset, size, file_bytes in sorted(extents):
                if offset != position or file_bytes != len(content):
                    _fail("index", "index container has gaps, overlaps or inconsistent extents")
                position += size
            if position != len(content):
                _fail("index", "index container has uncommitted trailing data")

    def select(self, selectors, *, max_records: int = 1000, collections=None) -> KnowledgeSlice:
        payload = super().select(selectors, max_records=max_records, collections=collections).to_payload()
        payload.update(schema_version="llm-wiki-knowledge-slice/v2" if collections is None else "llm-wiki-knowledge-slice/v3",
                       storage_format=self.storage_format,
                       archive_validation_scope="selected-members")
        payload["work"]["physical_bytes"] = self._physical_bytes
        return KnowledgeSlice(canonical_bytes(payload))

    def statistics(self) -> dict[str, Any]:
        return {**super().statistics(), "physical_packs": self.packing["packs"],
                "physical_indexes": sum(bool(INDEX_NAME.fullmatch(p) or INDEX_PAGE_NAME.fullmatch(p)) for p in self.physical_objects)}

    def release_capture(self) -> None:
        super().release_capture()
        self.physical_objects.clear()
        self._indexes.clear()
        self._index_extents.clear()
        self._verified_index_containers.clear()
        self._pack_descriptors.clear()
        self._selected_locations.clear()
        self._verified_pack_hashes.clear()


def open_knowledge_store(root_bytes: bytes, read_file: Callable[[str, int], bytes], *,
                         read_range: RangeReader | None = None, **limits) -> KnowledgeStoreReader:
    version = json.loads(root_bytes).get("schema_version")
    if version in PACKED_SCHEMAS:
        return PackedKnowledgeStoreReader(root_bytes, read_file, read_range=read_range, **limits)
    return KnowledgeStoreReader(root_bytes, read_file, **limits)


def physical_objects(reader: KnowledgeStoreReader) -> Mapping[str, bytes]:
    return reader.physical_objects if isinstance(reader, PackedKnowledgeStoreReader) else reader.objects


def build_storage(payload: Mapping[str, Any], storage_format: str, *, prior=None, objects=None) -> KnowledgeStorePlan:
    if storage_format in PACKED_FORMATS:
        return build_packed_store(payload, compression="deflate" if storage_format.endswith("-deflate") else "stored", prior=prior, objects=objects,
                                  profile=LOCAL_PACK_PROFILE if storage_format.startswith("packed-v4") else "standard")
    if storage_format == "sharded-v2":
        return build_knowledge_store(payload, objects=objects)
    _fail("format", "unsupported object storage format")
