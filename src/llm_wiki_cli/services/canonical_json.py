"""Bounded canonical JSON chunks and exact scalar sizes.

Only immutable JSON syntax is handled here. There is no filesystem or validity
cache, and emitted bytes retain the existing compact UTF-8 encoding.
"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from collections.abc import Iterator, Mapping
from typing import Any

_ESCAPED = re.compile(r'["\\\x00-\x1f]')
_SHORT = frozenset('"\\\b\f\n\r\t')
CHUNK_BYTES = 65_536


class CanonicalArray:
    """Explicit repeatable array stream for internal spill-backed operations."""

    def __init__(self, values):
        self.values = values

    def __iter__(self):
        return iter(self.values)


def _string_size(value: str) -> int:
    size = len(value.encode("utf-8")) + 2
    if _ESCAPED.search(value) is None:
        return size
    return size + sum(1 if m[0] in _SHORT else 5 for m in _ESCAPED.finditer(value))


_short_string_size = lru_cache(maxsize=8192)(_string_size)


def scalar_size(value: Any) -> int:
    """Exact encoded bytes, excluding a trailing newline, without JSON buffers."""
    if isinstance(value, str):
        return _short_string_size(value) if len(value) <= 512 else _string_size(value)
    if value is None:
        return 4
    if value is True:
        return 4
    if value is False:
        return 5
    if isinstance(value, int):
        return len(int.__repr__(value))
    if isinstance(value, float) and math.isfinite(value):
        return len(float.__repr__(value))
    raise ValueError("requires a finite JSON scalar")


def _fits(value: Any, budget: int) -> bool:
    # A bounded conservative estimate chooses the C encoder for record-sized
    # subtrees. Large values use the streaming path, without a whole-model dump.
    pending = [value]
    nodes = 0
    while pending:
        item = pending.pop()
        nodes += 1
        if nodes > 512:
            return False
        if isinstance(item, str):
            budget -= 2 + 6 * len(item)
        elif isinstance(item, dict):
            if len(item) > 512 or any(not isinstance(k, str) for k in item):
                return False
            budget -= 2 + 2 * len(item)
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            if len(item) > 512:
                return False
            budget -= 2 + len(item)
            pending.extend(item)
        elif isinstance(item, int):
            budget -= max(5, item.bit_length() // 3 + 2)
        elif item is None or isinstance(item, float):
            budget -= 32
        else:
            return False
        if budget < 0:
            return False
    return True


def canonical_chunks(value: Any, *, chunk_bytes: int = CHUNK_BYTES) -> Iterator[bytes]:
    """Emit exactly json.dumps(sort_keys=True, ensure_ascii=False, compact)+LF."""
    if type(chunk_bytes) is not int or chunk_bytes < 64:
        raise ValueError("chunk_bytes must be at least 64")
    encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    active: set[int] = set()

    def emit(item, depth=0):
        if depth > 256:
            raise ValueError("JSON nesting exceeds the streaming bound")
        if _fits(item, chunk_bytes):
            raw = encoder.encode(item).encode("utf-8")
            for offset in range(0, len(raw), chunk_bytes):
                yield raw[offset:offset + chunk_bytes]
            return
        if isinstance(item, str):
            yield b'"'
            # Six escaped bytes per code point is the largest JSON expansion.
            width = max(1, (chunk_bytes - 2) // 6)
            for offset in range(0, len(item), width):
                yield encoder.encode(item[offset:offset + width])[1:-1].encode("utf-8")
            yield b'"'
            return
        if not isinstance(item, (Mapping, list, tuple, CanonicalArray)):
            raw = encoder.encode(item).encode("utf-8")
            for offset in range(0, len(raw), chunk_bytes):
                yield raw[offset:offset + chunk_bytes]
            return
        identity = id(item)
        if identity in active:
            raise ValueError("circular JSON value")
        active.add(identity)
        try:
            if isinstance(item, Mapping):
                if any(not isinstance(key, str) for key in item):
                    raise TypeError("JSON object keys must be strings")
                yield b"{"
                for index, key in enumerate(sorted(item)):
                    if index:
                        yield b","
                    yield from emit(key, depth + 1)
                    yield b":"
                    yield from emit(item[key], depth + 1)
                yield b"}"
            else:
                yield b"["
                for index, child in enumerate(item):
                    if index:
                        yield b","
                    yield from emit(child, depth + 1)
                yield b"]"
        finally:
            active.remove(identity)

    buffer = bytearray()
    for part in emit(value):
        offset = 0
        while offset < len(part):
            take = min(chunk_bytes - len(buffer), len(part) - offset)
            buffer.extend(part[offset:offset + take])
            offset += take
            if len(buffer) == chunk_bytes:
                yield bytes(buffer)
                buffer.clear()
    buffer.extend(b"\n")
    yield bytes(buffer)
