"""Lossless portable encodings for versioned selected-storage receipts."""

from __future__ import annotations

from collections.abc import Mapping
import base64
import re
from typing import Any

from .knowledge_packs import PACK_NAME, INDEX_PAGE_NAME, pack_path, index_page_path
from .knowledge_storage import canonical_bytes

RECEIPT_SCHEMA = "llm-wiki-task-storage/v3"
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_FIXED = {1: ".llm-wiki-knowledge.json", 2: ".llm-wiki-manifest.json"}
_CONTENT_ADDRESSED = {
    3: ".llm-wiki-knowledge/pack-index", 4: ".llm-wiki-knowledge/objects",
    5: ".llm-wiki-manifest/objects",
}


def _hash(value: Any) -> str:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError("compact receipt requires a SHA-256 hexadecimal digest")
    return "sha256:" + value


def _encode_hash(commitment):
    if not isinstance(commitment, str) or not commitment.startswith("sha256:"):
        raise ValueError("invalid receipt digest")
    _hash(commitment[7:])
    return base64.urlsafe_b64encode(bytes.fromhex(commitment[7:])).rstrip(b"=").decode("ascii")


def _decode_hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
        raise ValueError("invalid compact SHA-256 encoding")
    raw = base64.b64decode(value + "=", altchars=b"-_", validate=True)
    result = "sha256:" + raw.hex()
    if _encode_hash(result) != value:
        raise ValueError("noncanonical compact SHA-256 encoding")
    return result


def _file_path(kind: int, commitment: str) -> str:
    if kind in _FIXED:
        return _FIXED[kind]
    if kind in _CONTENT_ADDRESSED:
        return f"{_CONTENT_ADDRESSED[kind]}/{commitment[:2]}/{commitment}.json"
    raise ValueError("unknown compact receipt path tag")


def compact_storage_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Encode each consumed path once; retain exact hashes, coordinates and work."""
    if receipt.get("schema_version") != RECEIPT_SCHEMA or receipt.get("layout") != "expanded-v1":
        raise ValueError("compaction requires an expanded version-3 receipt")
    result = {key: value for key, value in receipt.items() if key not in {"inputs", "ranges", "layout"}}
    result["layout"] = "compact-v1"
    files = []
    for item in receipt["inputs"]:
        identity = item["hash"][7:]
        _hash(identity)
        tag = next((tag for tag in (*_FIXED, *_CONTENT_ADDRESSED)
                    if _file_path(tag, identity) == item["path"]), 0)
        files.append([tag, *([item["path"]] if tag == 0 else []),
                      None if tag == 1 and item["hash"] == receipt["root_hash"] else _encode_hash(item["hash"]), item["bytes"]])
    result["files"] = files
    if "ranges" in receipt:
        packs = {}
        for row in receipt["ranges"]:
            match = PACK_NAME.fullmatch(row["path"])
            page = INDEX_PAGE_NAME.fullmatch(row["path"])
            if match is None and page is None:
                raise ValueError("compact receipt requires a canonical pack path")
            if match is not None:
                entry = [_encode_hash("sha256:" + match[2]), "" if match[3] == "root" else match[3], row["file_bytes"]]
            else:
                assert page is not None
                entry = [_encode_hash("sha256:" + page[2]), None, row["file_bytes"]]
            if packs.setdefault(row["path"], entry) != entry:
                raise ValueError("compact receipt pack sizes disagree")
        ordered = sorted(packs)
        table = {path: index for index, path in enumerate(ordered)}
        result["packs"] = [packs[path] for path in ordered]
        result["ranges"] = [[table[row["path"]], row["offset"], row["bytes"],
                             None if row["offset"] == 0 and row["bytes"] == row["file_bytes"]
                             and _encode_hash(row["hash"]) == packs[row["path"]][0] else _encode_hash(row["hash"])]
                            for row in receipt["ranges"]]
    return result


def expand_storage_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Expand compact proof data without evaluating its authority or freshness."""
    if not isinstance(receipt, Mapping):
        raise ValueError("storage receipt must be an object")
    if receipt.get("schema_version") != RECEIPT_SCHEMA or receipt.get("layout") != "compact-v1":
        raise ValueError("expansion requires a compact version-3 receipt")
    packed = receipt.get("storage_format") in {"packed-v3", "packed-v4"}
    required = {"schema_version", "status", "reason", "validation_scope", "whole_store_validated",
                "root_hash", "lookup_complete", "unverified_records", "read_bytes", "read_operations",
                "expanded_bytes", "collections", "layout", "storage_format", "files"}
    if packed:
        required.update({"packs", "ranges", "archive_validation_scope"})
    if set(receipt) != required:
        raise ValueError("invalid compact receipt fields")
    files = receipt["files"]
    if not isinstance(files, list) or len(files) > 100_000:
        raise ValueError("invalid compact receipt file table")
    result = {key: value for key, value in receipt.items() if key not in {"files", "packs", "ranges", "layout"}}
    result.update(layout="expanded-v1", inputs=[])
    for row in files:
        if (not isinstance(row, list) or len(row) not in {3, 4} or type(row[0]) is not int
                or (len(row) == 4) != (row[0] == 0) or type(row[-1]) is not int or row[-1] < 0):
            raise ValueError("invalid compact receipt file row")
        commitment = receipt["root_hash"] if row[0] == 1 and row[-2] is None else _decode_hash(row[-2])
        if not isinstance(commitment, str) or not commitment.startswith("sha256:"):
            raise ValueError("invalid compact root binding")
        _hash(commitment[7:])
        path = row[1] if row[0] == 0 else _file_path(row[0], commitment[7:])
        from .validation import is_portable_relative_path
        if not is_portable_relative_path(path):
            raise ValueError("invalid compact receipt path")
        result["inputs"].append({"path": path, "hash": commitment, "bytes": row[-1]})
    if packed:
        packs, ranges = receipt["packs"], receipt["ranges"]
        if (not isinstance(packs, list) or len(packs) > 100_000
                or not isinstance(ranges, list) or len(ranges) > 100_000):
            raise ValueError("invalid compact receipt pack tables")
        paths = []
        for row in packs:
            if (not isinstance(row, list) or len(row) != 3
                    or (row[1] is not None and (not isinstance(row[1], str) or not re.fullmatch(r"[01]{0,64}", row[1])))
                    or type(row[2]) is not int or not 22 <= row[2] <= 8_388_608):
                raise ValueError("invalid compact receipt pack row")
            paths.append(index_page_path(_decode_hash(row[0])) if row[1] is None else pack_path({"hash": _decode_hash(row[0]), "bucket": row[1]}))
        result["ranges"] = []
        for row in ranges:
            if (not isinstance(row, list) or len(row) != 4 or any(type(v) is not int for v in row[:3])
                    or not 0 <= row[0] < len(packs) or row[1] < 0 or row[2] <= 0
                    or row[1] + row[2] > packs[row[0]][2]):
                raise ValueError("invalid compact receipt range row")
            if row[3] is None and (row[1] != 0 or row[2] != packs[row[0]][2]):
                raise ValueError("compact whole-file hash used for a partial range")
            result["ranges"].append({"path": paths[row[0]], "offset": row[1], "bytes": row[2],
                                     "file_bytes": packs[row[0]][2],
                                     "hash": _decode_hash(packs[row[0]][0] if row[3] is None else row[3])})
    if canonical_bytes(compact_storage_receipt(result)) != canonical_bytes(receipt):
        raise ValueError("compact receipt tables are not canonical")
    return result
