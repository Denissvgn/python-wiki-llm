"""Format checks for ``llm-wiki-context/v1`` and ``/v2`` protocol responses.

A response is either a successful budgeted context or an error envelope.
These checks read no repository, wiki or knowledge state. The success body
is the one a qualified context packet carries as ``response``, so the deeper
native knowledge rules are the packet format's own checks.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import context_packet, context_request_format
from .context_knowledge_contract import KNOWLEDGE_MODE_VALUES
from .contracts import CONTEXT_KNOWLEDGE_PROTOCOL_VERSION, CONTEXT_PROTOCOL_VERSION

#: Protocols whose responses these checks cover, oldest first.
CONTEXT_RESPONSE_PROTOCOLS = (CONTEXT_PROTOCOL_VERSION, CONTEXT_KNOWLEDGE_PROTOCOL_VERSION)

_DETAIL_LEVELS = frozenset({"deep", "slim", "summary"})
_PRIORITIES = frozenset({"high", "medium", "low"})
_SUCCESS_REQUIRED = frozenset({
    "protocol", "ok", "budget_tokens", "used_tokens", "format", "focus", "filters",
    "truncated", "omitted_files", "downgraded_files", "bounds",
})
_SUCCESS_OPTIONAL = frozenset({
    "warnings", "graphs", "surface", "knowledge", "typed_graph", "files", "content",
    "prefer_fresh", "ranking_policy", "source_priorities",
})
_INVALID_REQUEST = "invalid_request"
_KNOWLEDGE_REQUIRED_UNAVAILABLE = "knowledge-required-unavailable"
_KNOWLEDGE_ERROR_FIELDS = frozenset({
    "code", "field", "mode", "availability", "reason", "fallback_evidence",
    "recovery_command", "mutation_permitted",
})
_AVAILABILITY = frozenset({"ready", "absent", "degraded", "unsupported"})


class ContextResponseError(ValueError):
    """A context protocol response does not follow its format."""


def validate_context_response(document: object) -> None:
    """Raise ``ContextResponseError`` unless *document* is a valid v1 or v2 response."""
    try:
        _validate(document)
    except ContextResponseError:
        raise
    except context_packet.ContextPacketError as exc:
        raise ContextResponseError(str(exc)) from exc


def _validate(document: object) -> None:
    data = _object(document, "response")
    protocol = data.get("protocol")
    if protocol not in CONTEXT_RESPONSE_PROTOCOLS:
        raise ContextResponseError(f"response.protocol: unsupported protocol {protocol!r}")
    ok = data.get("ok")
    if ok is False:
        _validate_error(data, protocol)
    elif ok is True:
        _validate_success(data, protocol)
    else:
        raise ContextResponseError("response.ok: must be a boolean")


def _validate_error(data: Mapping[str, Any], protocol: str) -> None:
    _exact(data, {"protocol", "ok", "error"}, set(), "response")
    error = _object(data["error"], "response.error")
    code = error.get("code")
    if code == _INVALID_REQUEST:
        _exact(error, {"code", "message"}, {"field"}, "response.error")
        _text(error["message"], "response.error.message")
        if "field" in error:
            _text(error["field"], "response.error.field")
        return
    if code != _KNOWLEDGE_REQUIRED_UNAVAILABLE or protocol != CONTEXT_KNOWLEDGE_PROTOCOL_VERSION:
        raise ContextResponseError(f"response.error.code: unsupported error code {code!r}")
    _exact(error, _KNOWLEDGE_ERROR_FIELDS, set(), "response.error")
    if error["field"] != "knowledge_mode" or error["mode"] != "required":
        raise ContextResponseError("response.error: only required knowledge can be unavailable")
    if error["availability"] not in _AVAILABILITY:
        raise ContextResponseError("response.error.availability: unsupported availability")
    context_packet._stable_code(error["reason"], "response.error.reason")
    context_packet._string_list(error["fallback_evidence"], "response.error.fallback_evidence")
    _text(error["recovery_command"], "response.error.recovery_command")
    if error["mutation_permitted"] is not False:
        raise ContextResponseError("response.error.mutation_permitted: must be false")


def _validate_success(data: Mapping[str, Any], protocol: str) -> None:
    knowledge_protocol = protocol == CONTEXT_KNOWLEDGE_PROTOCOL_VERSION
    required = set(_SUCCESS_REQUIRED) | ({"knowledge"} if knowledge_protocol else set())
    _exact(data, required, set(_SUCCESS_OPTIONAL) - required, "response")
    request = _request(data, protocol)
    for name in ("budget_tokens", "format", "focus", "filters"):
        if data[name] != request[name]:
            raise ContextResponseError(f"response.{name}: is not in normalized request form")
    used = context_packet._nonnegative_integer(data["used_tokens"], "response.used_tokens")
    if used > request["budget_tokens"]:
        raise ContextResponseError("response.used_tokens: exceeds budget_tokens")
    if not isinstance(data["truncated"], bool):
        raise ContextResponseError("response.truncated: must be a boolean")
    if request["format"] == "json":
        if "content" in data:
            raise ContextResponseError("response: JSON context requires files and no content")
        files = _object(data.get("files"), "response.files")
        for path, entry in files.items():
            entry = _object(entry, f"response.files.{path}")
            if knowledge_protocol and entry.get("priority") not in _PRIORITIES:
                raise ContextResponseError(f"response.files.{path}.priority: unsupported priority")
    elif not isinstance(data.get("content"), str) or "files" in data:
        raise ContextResponseError("response: Markdown context requires content and no files")
    context_packet._string_list(data["omitted_files"], "response.omitted_files")
    downgraded = _object(data["downgraded_files"], "response.downgraded_files")
    if any(level not in _DETAIL_LEVELS for level in downgraded.values()):
        raise ContextResponseError("response.downgraded_files: unsupported detail level")
    if "warnings" in data:
        context_packet._string_list(data["warnings"], "response.warnings")
    if "source_priorities" in data:
        priorities = _object(data["source_priorities"], "response.source_priorities")
        if any(priority not in _PRIORITIES for priority in priorities.values()):
            raise ContextResponseError("response.source_priorities: unsupported priority")
    if request["prefer_fresh"]:
        if not isinstance(data.get("ranking_policy"), Mapping):
            raise ContextResponseError("response: freshness preference requires its ranking policy")
    elif "prefer_fresh" in data or "ranking_policy" in data:
        raise ContextResponseError("response: freshness ranking was not requested")
    if not knowledge_protocol:
        return
    context_packet._validate_explicit_source_bounds(data)
    context_packet._validate_explicit_knowledge_response(
        data["knowledge"],
        request,
        source_priorities=(
            context_packet._explicit_response_source_priorities(data)
            if "source_priorities" in data
            else None
        ),
    )
    if request["prefer_fresh"]:
        context_packet._validate_explicit_ranking_policy(
            data["ranking_policy"], data["knowledge"], response_truncated=data["truncated"]
        )


def _request(data: Mapping[str, Any], protocol: str) -> dict[str, Any]:
    """Return the normalized request the response's own fields describe."""
    if "prefer_fresh" in data and data["prefer_fresh"] is not True:
        raise ContextResponseError("response.prefer_fresh: is present only when true")
    request: dict[str, Any] = {
        "protocol": protocol,
        "budget_tokens": data["budget_tokens"],
        "focus": data["focus"],
        "format": data["format"],
        "filters": data["filters"],
        "prefer_fresh": "prefer_fresh" in data,
    }
    if protocol == CONTEXT_KNOWLEDGE_PROTOCOL_VERSION:
        knowledge = _object(data["knowledge"], "response.knowledge")
        if knowledge.get("mode") not in KNOWLEDGE_MODE_VALUES:
            raise ContextResponseError("response.knowledge.mode: unsupported knowledge mode")
        request["knowledge_mode"] = knowledge["mode"]
    try:
        return context_request_format._validate_protocol_request(request)
    except context_request_format.ProtocolRequestError as exc:
        raise ContextResponseError(f"response.{exc.field or 'request'}: {exc}") from exc


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ContextResponseError(f"{field}: must be a JSON object")
    return value


def _exact(
    value: Mapping[str, Any], required: set[str] | frozenset[str],
    optional: set[str] | frozenset[str], field: str,
) -> None:
    missing = sorted(set(required) - set(value))
    if missing:
        raise ContextResponseError(f"{field}.{missing[0]}: is required")
    unknown = sorted(set(value) - set(required) - set(optional))
    if unknown:
        raise ContextResponseError(f"{field}.{unknown[0]}: is not supported")


def _text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise ContextResponseError(f"{field}: must be a non-empty string")
