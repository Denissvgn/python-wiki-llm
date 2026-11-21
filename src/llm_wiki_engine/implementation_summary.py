"""The implementation summary a context packet may carry.

A summary states whether captured executable syntax changed for one owner,
within fixed limitations. This module checks the summary's closed format; the
evidence it summarizes is produced and compared by the analyzing application.
"""

from __future__ import annotations

from collections.abc import Mapping
import json

from .canonical_json import compact_line_bytes

SCOPES = frozenset({"module", "class", "callable"})
ANALYSIS_SCOPES = frozenset({"snapshot", "selected-source", "full-inventory"})
UNAVAILABLE_REASONS = frozenset(
    {
        "missing-source",
        "unsupported-language",
        "unsupported-syntax",
        "unsupported-producer",
        "ambiguous-owner",
        "legacy-evidence-absent",
        "observation-limit",
        "object-limit",
    }
)
REASONS = UNAVAILABLE_REASONS | frozenset(
    {
        "matching-executable-syntax",
        "executable-syntax-changed",
        "live-evaluation-not-performed",
        "source-not-captured",
        "owner-not-observed",
        "producer-incompatible",
        "scope-incompatible",
        "implementation-unavailable",
        "identical-source-observation-mismatch",
        "invalid-captured-evidence",
    }
)
LIMITATIONS = (
    "captured-executable-syntax-only",
    "dependencies-and-runtime-behavior-not-evaluated",
    "authored-prose-correctness-not-evaluated",
)
SUMMARY_FIELDS = frozenset(
    {
        "state",
        "reason",
        "scope",
        "analysis_scope",
        "live_comparison_performed",
        "source_changed",
        "documentation_changed",
        "truncated",
        "limitations",
    }
)


def _object(value, fields, label):
    if not isinstance(value, Mapping) or set(value) != set(fields):
        raise ValueError(f"{label}: fields must match the closed contract")
    return dict(value)


def _bool(value, label):
    if type(value) is not bool:
        raise ValueError(f"{label}: must be boolean")
    return value


def _copy(value):
    # This also refuses NaN, non-JSON values and invalid UTF-8 scalars.
    return json.loads(compact_line_bytes(value))


def validate_implementation_summary(value: object) -> dict:
    row = _object(value, SUMMARY_FIELDS, "implementation summary")
    if (
        row["state"] not in {"changed", "unchanged", "unavailable"}
        or row["reason"] not in REASONS
        or row["scope"] not in SCOPES | {None}
        or row["analysis_scope"] not in ANALYSIS_SCOPES
    ):
        raise ValueError("implementation summary: unsupported state, reason or scope")
    for key in ("live_comparison_performed", "truncated"):
        _bool(row[key], key)
    for key in ("source_changed", "documentation_changed"):
        if row[key] is not None:
            _bool(row[key], key)
    if (
        not isinstance(row["limitations"], (list, tuple))
        or tuple(row["limitations"]) != LIMITATIONS
    ):
        raise ValueError("implementation summary: fixed limitations required")
    if row["state"] != "unavailable":
        expected = (
            "matching-executable-syntax"
            if row["state"] == "unchanged"
            else "executable-syntax-changed"
        )
        if (
            row["reason"] != expected
            or row["analysis_scope"] == "snapshot"
            or not row["live_comparison_performed"]
            or row["scope"] is None
            or row["source_changed"] is None
            or row["documentation_changed"] is None
        ):
            raise ValueError(
                "implementation summary: verdict requires qualified live comparison"
            )
        if (row["state"] == "changed" or row["documentation_changed"]) and row[
            "source_changed"
        ] is not True:
            raise ValueError(
                "implementation summary: changed syntax/docstrings require changed source bytes"
            )
    elif (
        row["reason"] in {"matching-executable-syntax", "executable-syntax-changed"}
        or row["live_comparison_performed"]
        or row["documentation_changed"] is not None
    ):
        raise ValueError(
            "implementation summary: unavailable cannot assert executable comparison"
        )
    if row["analysis_scope"] == "snapshot" and (
        row["reason"] != "live-evaluation-not-performed"
        or row["source_changed"] is not None
        or row["documentation_changed"] is not None
    ):
        raise ValueError("implementation summary: snapshot has no live verdict")
    row["limitations"] = list(row["limitations"])
    return _copy(row)


__all__ = [
    "ANALYSIS_SCOPES",
    "LIMITATIONS",
    "REASONS",
    "SCOPES",
    "SUMMARY_FIELDS",
    "UNAVAILABLE_REASONS",
    "validate_implementation_summary",
]
