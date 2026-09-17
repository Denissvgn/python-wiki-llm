"""Private bounded spill buffers; never an on-disk source of authority.

The owner must keep the context open until its consumers finish. Reads verify
their captured hash; closing or cancelling the context removes all staged data.
"""

from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass
import hashlib
import json
import pickle
from collections import OrderedDict
import tempfile
from typing import Any

from .knowledge_storage import MAX_OBJECT_BYTES, KnowledgeStorageError


class ByteSpool(MutableMapping[str, bytes]):
    """One private file, bounded index and byte quota, with synchronous backpressure."""

    def __init__(self, *, max_bytes: int = 2_147_483_648, max_index_bytes: int = 16_777_216):
        if type(max_bytes) is not int or not 0 < max_bytes <= 8_589_934_592:
            raise ValueError("invalid spool byte limit")
        if type(max_index_bytes) is not int or not 0 < max_index_bytes <= 67_108_864:
            raise ValueError("invalid spool index limit")
        self._file = tempfile.TemporaryFile(prefix="llm-wiki-spool-")
        self._index: dict[str, tuple[int, int, bytes]] = {}
        self.maximum, self.index_maximum = max_bytes, max_index_bytes
        self.bytes_written = self.index_bytes = 0

    def __getitem__(self, key: str) -> bytes:
        offset, size, commitment = self._index[key]
        self._file.seek(offset)
        raw = self._file.read(size)
        if len(raw) != size or hashlib.sha256(raw).digest() != commitment:
            raise KnowledgeStorageError("spool", "private staged data changed")
        return raw

    def __setitem__(self, key: str, value: bytes) -> None:
        if not isinstance(key, str) or not isinstance(value, bytes):
            raise TypeError("spool entries require string keys and bytes")
        if len(value) > MAX_OBJECT_BYTES:
            raise KnowledgeStorageError("spool", "entry exceeds 8 MiB", code="storage-limit")
        extra = 0 if key in self._index else len(key.encode("utf-8")) + 128
        if self.bytes_written + len(value) > self.maximum or self.index_bytes + extra > self.index_maximum:
            raise KnowledgeStorageError("spool", "private spill quota exhausted", code="storage-limit")
        offset = self._file.seek(0, 2)
        self._file.write(value)
        self._index[key] = offset, len(value), hashlib.sha256(value).digest()
        self.bytes_written += len(value)
        self.index_bytes += extra

    def __delitem__(self, key: str) -> None:
        del self._index[key]
        self.index_bytes -= len(key.encode("utf-8")) + 128

    def __iter__(self) -> Iterator[str]:
        return iter(self._index)

    def __len__(self) -> int:
        return len(self._index)

    def __contains__(self, key) -> bool:
        return key in self._index

    def close(self) -> None:
        self._file.close()
        self._index.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


@dataclass(frozen=True)
class SpooledArtifactWrite:
    """Byte-compatible planned write whose buffers live in a request-owned spool."""

    path: Any
    relative_path: str
    state: Any
    content_hash: str
    needs_write: bool
    _spool: ByteSpool
    _new_key: str
    _old_key: str | None

    @property
    def content(self) -> bytes:
        return self._spool[self._new_key]

    @property
    def previous_content(self) -> bytes | None:
        return None if self._old_key is None else self._spool[self._old_key]


def spool_write(write, spool: ByteSpool) -> SpooledArtifactWrite:
    key = "new:" + write.relative_path
    spool[key] = write.content
    previous = write.previous_content
    old_key = None
    if previous is not None:
        if previous == write.content:
            old_key = key
        else:
            old_key = "old:" + write.relative_path
            spool[old_key] = previous
    return SpooledArtifactWrite(write.path, write.relative_path, write.state, write.content_hash,
                                write.needs_write, spool, key, old_key)


class JsonSpool(MutableMapping):
    """JSON values backed by one explicitly owned byte spool."""

    def __init__(self, spool: ByteSpool):
        self.spool = spool

    def __getitem__(self, key):
        return json.loads(self.spool[key])

    def __setitem__(self, key, value):
        from .knowledge_storage import canonical_bytes
        self.spool[key] = canonical_bytes(value)

    def __delitem__(self, key):
        del self.spool[key]

    def __iter__(self):
        return iter(self.spool)

    def __len__(self):
        return len(self.spool)


class DecodeCache(MutableMapping):
    """Bound encoded cache weight; never reuse this cache across captures."""

    def __init__(self, maximum=2_097_152):
        self.entries = OrderedDict()
        self.maximum, self.size = maximum, 0

    def __getitem__(self, key):
        value, _ = self.entries[key]
        self.entries.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self.entries:
            del self[key]
        weight = len(pickle.dumps(value, protocol=4))
        if weight > self.maximum:
            return
        while self.size + weight > self.maximum:
            del self[next(iter(self.entries))]
        self.entries[key] = value, weight
        self.size += weight

    def __delitem__(self, key):
        _, weight = self.entries.pop(key)
        self.size -= weight

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)
