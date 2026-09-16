"""Bounded, strict JSON input for explicit read requests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

MAX_REQUEST_BYTES = 1_048_576


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("Nonfinite JSON numbers are not permitted")


def parse_request(raw: bytes | str) -> dict[str, Any]:
    if len(raw if isinstance(raw, bytes) else raw.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ValueError("Request exceeds 1 MiB")
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError("Request must be a UTF-8 JSON object") from exc
    if not isinstance(value, dict):
        raise ValueError("Request must be a JSON object")
    return value


def load_request(path: str) -> dict[str, Any]:
    if path == "-":
        stream = getattr(sys.stdin, "buffer", sys.stdin)
        return parse_request(stream.read(MAX_REQUEST_BYTES + 1))
    with Path(path).open("rb") as stream:
        return parse_request(stream.read(MAX_REQUEST_BYTES + 1))
