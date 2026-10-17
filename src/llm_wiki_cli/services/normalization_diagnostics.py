"""Bounded fresh-normalization diagnostics, separate from evidence/hash contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import json
import math


from .contracts import NORMALIZATION_DIAGNOSTIC_SCHEMA_VERSION

DIAGNOSTIC_SCHEMA = NORMALIZATION_DIAGNOSTIC_SCHEMA_VERSION
DIAGNOSTIC_PREFIX = "Fresh normalization diagnostic: "
MAX_DIAGNOSTIC_BYTES = 4096
MISSING_VALUE = object()


def _actual(value: object) -> tuple[str, str]:
    # Never stringify an arbitrary value, key, source fragment or Python repr.
    if value is MISSING_VALUE:
        return "missing", "field absent"
    if value is None:
        return "null", "null"
    if isinstance(value, bool):
        return "boolean", "true" if value else "false"
    if isinstance(value, str):
        return "string", "empty string" if not value else f"{len(value)} characters; value redacted"
    if isinstance(value, Mapping):
        return "object", f"{len(value)} entries; contents redacted"
    if isinstance(value, list):
        return "array", f"{len(value)} items; contents redacted"
    if isinstance(value, int):
        return "integer", "zero" if value == 0 else "value redacted"
    if isinstance(value, float):
        return "number", "non-finite" if not math.isfinite(value) else "zero" if value == 0 else "value redacted"
    return "unsupported", "value redacted"


@dataclass(frozen=True)
class NormalizationDiagnostic:
    """One fresh rejection; never a historical evidence promise."""

    reason: str
    pointer: str | None
    rule: str
    expected: str
    actual_type: str
    actual_summary: str
    pointer_exact: bool = True
    source_path: str | None = None
    scope: str | None = None
    extractor_ref: str | None = None
    entity_name: str | None = None
    occurrence: int | None = None

    @classmethod
    def rejection(cls, reason, pointer, rule, expected, value, *, exact=True):
        actual_type, summary = _actual(value)
        return cls(reason, pointer, rule, expected, actual_type, summary, exact)

    def at_source(self, source_path, scope, extractor_ref, entity_name=None, occurrence=None):
        return replace(self, source_path=source_path, scope=scope, extractor_ref=extractor_ref,
                       entity_name=entity_name, occurrence=occurrence)

    def to_payload(self) -> dict:
        truncated = []

        def bounded(key, value, limit=64):
            if value is None:
                return None
            if len(value) > limit:
                truncated.append(key)
            return value[:limit]

        pointer = bounded("pointer", self.pointer, 256)
        result = {
            "schema_version": DIAGNOSTIC_SCHEMA, "basis": "fresh-normalization",
            "reason": bounded("reason", self.reason),
            "source_path": bounded("source_path", self.source_path), "scope": bounded("scope", self.scope),
            "extractor_ref": bounded("extractor_ref", self.extractor_ref),
            "entity_name": bounded("entity_name", self.entity_name),
            "occurrence": self.occurrence if self.occurrence is None or self.occurrence.bit_length() <= 31 else None,
            "pointer": pointer,
            "pointer_exact": self.pointer_exact and pointer is not None and "pointer" not in truncated,
            "rule": bounded("rule", self.rule), "expected": bounded("expected", self.expected),
            "actual": {"type": self.actual_type, "summary": self.actual_summary},
            "truncated_fields": truncated,
        }
        # Escaped Unicode can expand sixfold; retain the hard wire-byte bound.
        if self.occurrence is not None and self.occurrence.bit_length() > 31:
            truncated.append("occurrence")
        if len(json.dumps(result, ensure_ascii=True).encode()) + len(DIAGNOSTIC_PREFIX) > MAX_DIAGNOSTIC_BYTES:
            result["pointer"] = None
            result["pointer_exact"] = False
            if "pointer" not in truncated:
                truncated.append("pointer")
        return result

    def render(self) -> str:
        return DIAGNOSTIC_PREFIX + json.dumps(self.to_payload(), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
