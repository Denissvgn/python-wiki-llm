"""Format checks for context requests: the context, budget and change shapes.

These checks decide whether a request is well formed; they read no
repository, wiki or knowledge state. Building the context a request asks
for lives in ``context_service`` and ``context_budget``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from llm_wiki_engine import wiki_surface
from llm_wiki_engine.context_knowledge_contract import KNOWLEDGE_MODE_VALUES
from llm_wiki_engine.contracts import (
    CONTEXT_BUDGET_PROTOCOL_VERSION,
    CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    CONTEXT_PROTOCOL_VERSION,
)
from llm_wiki_engine.knowledge_graph import CORE_RELATIONSHIP_KINDS, GRAPH_ORIGINS, GRAPH_RESOLUTIONS
from .knowledge_model import ComputedFreshness, EvidenceState

CONTEXT_COVERAGE_LIMITATION_LIMIT = 16

CONTEXT_COVERAGE_LIMITATION_CODE_MAX_LENGTH = 128


PROTOCOL_VERSION = CONTEXT_PROTOCOL_VERSION


KNOWLEDGE_PROTOCOL_VERSION = CONTEXT_KNOWLEDGE_PROTOCOL_VERSION


CONTEXT_KNOWLEDGE_CONCEPT_LIMIT = 20


CONTEXT_KNOWLEDGE_PAGE_LIMIT = 20


CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT = 40


_V1_REQUEST_KEYS = {
    "protocol",
    "budget_tokens",
    "focus",
    "format",
    "filters",
    "prefer_fresh",
}


_V2_REQUEST_KEYS = {*_V1_REQUEST_KEYS, "knowledge_mode"}


# The budgeted protocol owns its validator; legacy versions share field rules.
# This registry also owns supported-version diagnostics and error identities.
_PROTOCOL_REQUEST_KEYS = {
    PROTOCOL_VERSION: _V1_REQUEST_KEYS,
    KNOWLEDGE_PROTOCOL_VERSION: _V2_REQUEST_KEYS,
    CONTEXT_BUDGET_PROTOCOL_VERSION: None,
}


_FILTER_KEYS = {
    "language",
    "module",
    "symbol",
    "entrypoint",
    "surface",
    "freshness",
    "evidence",
    "relationship_kind",
    "relationship_origin",
    "relationship_resolution",
    "relationship_direction",
}


_FOCUS_VALUES = {"changed", "neighbors", "all"}


_FORMATS = {"json", "markdown"}


_CONTEXT_QUERY_LIMIT = 20


_CONCEPT_FILTER_KEYS = {"surface", "symbol"}


_KNOWLEDGE_REFINEMENT_KEYS = {"freshness", "evidence"}


_RELATIONSHIP_REFINEMENT_KEYS = {
    "relationship_kind",
    "relationship_origin",
    "relationship_resolution",
    "relationship_direction",
}


_RELATIONSHIP_DIRECTIONS = ("incoming", "outgoing", "both")


_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)


_FRESHNESS_FILTER_VALUES = {item.value for item in ComputedFreshness}


_EVIDENCE_FILTER_VALUES = {item.value for item in EvidenceState}


class ProtocolRequestError(ValueError):
    """Validation error for Wiki-as-Context protocol requests."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        *,
        protocol: str = PROTOCOL_VERSION,
    ):
        super().__init__(message)
        self.field = field
        self.protocol = protocol


def _validate_protocol_request(data: object) -> dict:
    """Return a normalised protocol request or raise ``ProtocolRequestError``."""

    protocol = data.get("protocol") if isinstance(data, dict) else PROTOCOL_VERSION
    try:
        return _validate_protocol_request_impl(data)
    except ProtocolRequestError as exc:
        if isinstance(protocol, str) and protocol in _PROTOCOL_REQUEST_KEYS:
            exc.protocol = protocol
        raise


def _validate_protocol_request_impl(data: object) -> dict:
    if not isinstance(data, dict):
        raise ProtocolRequestError("Request must be a JSON object.", "request")
    if any(not isinstance(key, str) for key in data):
        raise ProtocolRequestError(
            "Request field names must be strings.",
            "request",
        )

    protocol = data.get("protocol")
    if not isinstance(protocol, str) or protocol not in _PROTOCOL_REQUEST_KEYS:
        choices = ", ".join(repr(version) for version in _PROTOCOL_REQUEST_KEYS)
        raise ProtocolRequestError(
            f"Unsupported protocol: {protocol!r}. Expected one of {choices}.",
            "protocol",
        )
    if protocol == CONTEXT_BUDGET_PROTOCOL_VERSION:
        return validate_budget_request(data)
    request_keys = _PROTOCOL_REQUEST_KEYS[protocol]
    assert request_keys is not None

    unknown = sorted(set(data) - request_keys)
    if unknown:
        raise ProtocolRequestError(
            f"Unknown request field: {unknown[0]}",
            unknown[0],
            protocol=protocol,
        )

    if "budget_tokens" not in data:
        raise ProtocolRequestError(
            "Missing required field: budget_tokens", "budget_tokens"
        )
    budget = data["budget_tokens"]
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        raise ProtocolRequestError(
            "budget_tokens must be a positive integer.", "budget_tokens"
        )

    fmt = data.get("format", "json")
    if not isinstance(fmt, str) or fmt not in _FORMATS:
        raise ProtocolRequestError("format must be 'json' or 'markdown'.", "format")

    focus = _normalise_protocol_focus(data.get("focus", ["changed", "neighbors"]))
    filters = _normalise_protocol_filters(data.get("filters", {}))
    prefer_fresh = data.get("prefer_fresh", False)
    if not isinstance(prefer_fresh, bool):
        raise ProtocolRequestError(
            "prefer_fresh must be a boolean.",
            "prefer_fresh",
        )

    normalized = {
        "protocol": protocol,
        "budget_tokens": budget,
        "focus": focus,
        "format": fmt,
        "filters": filters,
        "prefer_fresh": prefer_fresh,
    }
    if protocol == KNOWLEDGE_PROTOCOL_VERSION:
        if "knowledge_mode" not in data:
            raise ProtocolRequestError(
                "Missing required field: knowledge_mode",
                "knowledge_mode",
                protocol=protocol,
            )
        knowledge_mode = data["knowledge_mode"]
        if not isinstance(knowledge_mode, str) or knowledge_mode not in (
            KNOWLEDGE_MODE_VALUES
        ):
            choices = ", ".join(repr(value) for value in KNOWLEDGE_MODE_VALUES)
            raise ProtocolRequestError(
                f"knowledge_mode must be one of {choices}.",
                "knowledge_mode",
                protocol=protocol,
            )
        normalized["knowledge_mode"] = knowledge_mode
    return normalized


def _normalise_protocol_focus(raw_focus: object) -> list[str]:
    if not isinstance(raw_focus, list) or not raw_focus:
        raise ProtocolRequestError("focus must be a non-empty list.", "focus")

    if any(not isinstance(item, str) for item in raw_focus):
        raise ProtocolRequestError("focus values must be strings.", "focus")

    unknown = sorted(set(raw_focus) - _FOCUS_VALUES)
    if unknown:
        raise ProtocolRequestError(f"Unknown focus value: {unknown[0]}", "focus")

    if len(set(raw_focus)) != len(raw_focus):
        raise ProtocolRequestError("focus values must not be duplicated.", "focus")

    focus_set = set(raw_focus)
    if "all" in focus_set and len(focus_set) > 1:
        raise ProtocolRequestError(
            "focus 'all' cannot be combined with other values.", "focus"
        )

    if "neighbors" in focus_set and "changed" not in focus_set:
        raise ProtocolRequestError("focus 'neighbors' requires 'changed'.", "focus")

    if "all" in focus_set:
        return ["all"]

    ordered = ["changed"] if "changed" in focus_set else []
    if "neighbors" in focus_set:
        ordered.append("neighbors")
    return ordered


def _normalise_protocol_filters(raw_filters: object) -> dict:
    if raw_filters is None:
        return {}
    if not isinstance(raw_filters, dict):
        raise ProtocolRequestError("filters must be a JSON object.", "filters")
    if any(not isinstance(key, str) for key in raw_filters):
        raise ProtocolRequestError(
            "filter field names must be strings.",
            "filters",
        )

    unknown = sorted(set(raw_filters) - _FILTER_KEYS)
    if unknown:
        raise ProtocolRequestError(
            f"Unknown filter field: {unknown[0]}", f"filters.{unknown[0]}"
        )

    filters: dict[str, str] = {}
    for key in (
        "language",
        "module",
        "symbol",
        "entrypoint",
        "surface",
        "freshness",
        "evidence",
        "relationship_kind",
        "relationship_origin",
        "relationship_resolution",
        "relationship_direction",
    ):
        if key not in raw_filters:
            continue
        value = raw_filters[key]
        if not isinstance(value, str) or not value:
            raise ProtocolRequestError(
                f"filters.{key} must be a non-empty string.", f"filters.{key}"
            )
        if key == "surface":
            _validate_surface_filter(value)
        elif key == "freshness":
            _validate_enum_filter(
                key,
                value,
                _FRESHNESS_FILTER_VALUES,
            )
        elif key == "evidence":
            _validate_enum_filter(
                key,
                value,
                _EVIDENCE_FILTER_VALUES,
            )
        elif key == "relationship_kind":
            _validate_relationship_kind_filter(value)
        elif key == "relationship_origin":
            _validate_enum_filter(key, value, set(GRAPH_ORIGINS))
        elif key == "relationship_resolution":
            _validate_enum_filter(key, value, set(GRAPH_RESOLUTIONS))
        elif key == "relationship_direction":
            _validate_enum_filter(
                key,
                value,
                set(_RELATIONSHIP_DIRECTIONS),
            )
        filters[key] = value

    filter_keys = set(filters)
    refinements = _KNOWLEDGE_REFINEMENT_KEYS & filter_keys
    if refinements and not (_CONCEPT_FILTER_KEYS & filter_keys):
        field = next(key for key in ("freshness", "evidence") if key in refinements)
        raise ProtocolRequestError(
            f"filters.{field} requires filters.surface or filters.symbol.",
            f"filters.{field}",
        )
    relationship_refinements = _RELATIONSHIP_REFINEMENT_KEYS & filter_keys
    if relationship_refinements and not (_CONCEPT_FILTER_KEYS & filter_keys):
        field = next(
            key
            for key in (
                "relationship_kind",
                "relationship_origin",
                "relationship_resolution",
                "relationship_direction",
            )
            if key in relationship_refinements
        )
        raise ProtocolRequestError(
            f"filters.{field} requires filters.surface or filters.symbol.",
            f"filters.{field}",
        )
    return filters


def _validate_surface_filter(value: str) -> None:
    known = {entry.kind.value for entry in wiki_surface.iter_page_kinds()}
    if value not in known:
        raise ProtocolRequestError(
            f"filters.surface must be one of: {', '.join(sorted(known))}.",
            "filters.surface",
        )


def _validate_enum_filter(key: str, value: str, known: set[str]) -> None:
    if value not in known:
        raise ProtocolRequestError(
            f"filters.{key} must be one of: {', '.join(sorted(known))}.",
            f"filters.{key}",
        )


def _validate_relationship_kind_filter(value: str) -> None:
    if (
        value not in CORE_RELATIONSHIP_KINDS
        and _QUALIFIED_RELATIONSHIP_KIND_RE.fullmatch(value) is None
    ):
        raise ProtocolRequestError(
            "filters.relationship_kind must be a core relationship kind or "
            "a qualified plugin kind such as 'vendor.plugin/relationship'.",
            "filters.relationship_kind",
        )


def validate_budget_request(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping) or any(not isinstance(key, str) for key in data):
        raise ProtocolRequestError("Request must be an object with string keys", "request")
    if data.get("protocol", CONTEXT_BUDGET_PROTOCOL_VERSION) != CONTEXT_BUDGET_PROTOCOL_VERSION:
        raise ProtocolRequestError("Unsupported context budget protocol", "protocol")
    allowed = _V2_REQUEST_KEYS | {"budget_mode", "counter_id", "changes"}
    unknown = set(data) - allowed
    if unknown:
        raise ProtocolRequestError(
            f"Unknown request field: {sorted(unknown)[0]}", sorted(unknown)[0]
        )
    legacy = dict(data)
    legacy["protocol"] = KNOWLEDGE_PROTOCOL_VERSION
    legacy["knowledge_mode"] = data.get("knowledge_mode", "off")
    legacy["format"] = (
        "json" if data.get("format") == "packet" else data.get("format", "json")
    )
    legacy.pop("budget_mode", None)
    legacy.pop("counter_id", None)
    legacy.pop("changes", None)
    normalized = _validate_protocol_request(legacy)
    mode = data.get("budget_mode", "exact")
    if not isinstance(mode, str) or mode not in {"exact", "estimated"}:
        raise ProtocolRequestError(
            "budget_mode must be exact or estimated", "budget_mode"
        )
    identity = data.get("counter_id")
    if identity is not None and (not isinstance(identity, str) or not identity):
        raise ProtocolRequestError(
            "counter_id must be a nonempty string", "counter_id"
        )
    changes = None
    if "changes" in data:
        try:
            changes = validate_changes(data["changes"])
        except ValueError as exc:
            raise ProtocolRequestError(str(exc), "changes") from exc
    return {
        **normalized,
        **({"changes": changes} if changes is not None else {}),
        "protocol": CONTEXT_BUDGET_PROTOCOL_VERSION,
        "format": data.get("format", "json"),
        "budget_mode": mode,
        "counter_id": identity,
    }


def portable_path(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Changed paths must be strings")
    value = value.replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    if (
        not value
        or value.startswith("/")
        or re.match(r"^[A-Za-z]:", value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError("Changed paths must be normalized source-relative paths")
    return value


def validate_changes(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("changes must be an object")
    mode = value.get("mode")
    fields = {
        "paths": {"mode", "paths"},
        "range": {"mode", "base", "head"},
        "staged": {"mode"},
    }
    if not isinstance(mode, str) or mode not in fields or set(value) != fields[mode]:
        raise ValueError("changes must specify paths, staged, or a base/head range")
    if mode == "paths":
        if not isinstance(value["paths"], list):
            raise ValueError("changes.paths must be an array")
        return {
            "mode": mode,
            "paths": sorted({portable_path(p) for p in value["paths"]}),
        }
    if mode == "range":
        for field in ("base", "head"):
            ref = value[field]
            if (
                not isinstance(ref, str)
                or not ref
                or ref.startswith("-")
                or any(ord(c) < 32 for c in ref)
            ):
                raise ValueError(f"changes.{field} must be a Git revision")
    return dict(value)
