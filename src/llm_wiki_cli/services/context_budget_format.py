"""Format checks for ``llm-wiki-context/v3`` budgeted context responses.

A response is a budgeted context envelope, an invalid-request envelope or a
cannot-fit refusal. These checks read no repository, wiki, knowledge state or
token counter. The embedded body is a v2 context response or a v2 qualified
packet, so its deeper rules are those formats' own checks. Binding
``request_id`` to a request and recounting the emitted text need the request
and the named counter; ``context_budget.validate_budgeted_context`` does both.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from . import context_packet, context_request_format, context_response_format
from .contracts import CONTEXT_BUDGET_PROTOCOL_VERSION, CONTEXT_KNOWLEDGE_PROTOCOL_VERSION

#: Protocol of the responses these checks cover.
CONTEXT_BUDGET_RESPONSE_PROTOCOL = CONTEXT_BUDGET_PROTOCOL_VERSION
#: Version of the diagnostics a cannot-fit refusal carries.
CONTEXT_BUDGET_REFUSAL_SCHEMA_VERSION = "llm-wiki-context-budget-refusal/v1"

_PACKET_SCHEMA_VERSION = "llm-wiki-qualified-context-packet/v2"
_COMMON_FIELDS = frozenset({"protocol", "ok", "format", "request_id", "changes", "accounting"})
_FORMAT_FIELDS = {
    "json": frozenset({"context"}),
    "packet": frozenset({"packet"}),
    "markdown": frozenset({"metadata", "warnings"}),
}
_ACCOUNTING_FIELDS = frozenset({
    "budget_tokens", "used_tokens", "counter_id", "mode", "exact_compliance",
    "usage_kind", "scope",
})
_USAGE_KIND = "upper-bound-including-accounting"
_SCOPE = "emitted-text-without-host-chat-framing"
_BUDGET_MODES = frozenset({"exact", "estimated"})
_METADATA_REQUIRED = frozenset({
    "bounds", "budget", "downgraded_files", "knowledge", "omitted_files",
    "source_priorities", "truncated", "used",
})
_METADATA_OPTIONAL = frozenset({"graphs", "ranking_policy", "surface", "typed_graph"})
_LEGACY_CHANGES = {"request": {"mode": "legacy-last-commit"}}
_CHANGE_FIELDS = frozenset({
    "request", "paths", "path_basis", "selection_boundary_changed", "paths_id",
    "affected_pages",
})
_CHANGE_REQUEST_FIELDS = {
    "paths": frozenset({"mode", "paths"}),
    "range": frozenset({"mode", "base", "head", "commits"}),
    "staged": frozenset({"mode", "index_id"}),
}
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")
_REFUSAL_FIELDS = frozenset({
    "schema_version", "request_id", "selection_policy", "reason", "accounting_meaning",
    "counter_id", "budget_mode", "emitted_context_bytes", "source", "native",
    "component_bytes", "recovery",
})
_SELECTION_POLICIES = frozenset({"joint-native-source/v1", "source-tail-reduction/v1"})
_REFUSAL_CONSTANTS = {
    "reason": "permitted-selection-reductions-exhausted",
    "accounting_meaning": "rejected-candidate-not-emitted-context-or-global-minimum",
}
_NATIVE_MODES = frozenset({"off", "auto", "required"})
_NATIVE_STATUSES = frozenset({"disabled", "selected", "fallback"})
_NATIVE_AVAILABILITY = frozenset({"not-evaluated", "ready", "absent", "degraded", "unsupported"})
_NATIVE_COLLECTIONS = frozenset({"concepts", "pages", "relationships"})
_COMPONENT_FIELDS = frozenset({
    "measurement", "source_entries", "native_knowledge", "omitted_files", "source_priorities",
})
_COMPONENT_MEASUREMENT = "canonical-json-fragments-not-additive-token-costs"
_RECOVERY_ROUTES = ("scoped-evidence", "explicit-larger-budget")


class BudgetedContextResponseError(ValueError):
    """A budgeted context response does not follow ``llm-wiki-context/v3``."""


def validate_budgeted_context_response(document: object) -> None:
    """Raise ``BudgetedContextResponseError`` unless *document* is a valid v3 response."""
    try:
        _validate(document)
    except BudgetedContextResponseError:
        raise
    except (context_packet.ContextPacketError, context_response_format.ContextResponseError) as exc:
        raise BudgetedContextResponseError(str(exc)) from exc


def _validate(document: object) -> None:
    data = _object(document, "response")
    if data.get("protocol") != CONTEXT_BUDGET_PROTOCOL_VERSION:
        raise BudgetedContextResponseError(
            f"response.protocol: unsupported protocol {data.get('protocol')!r}"
        )
    ok = data.get("ok")
    if ok is True:
        _validate_success(data)
    elif ok is False:
        if isinstance(data.get("error"), Mapping):
            _validate_invalid_request(data)
        else:
            _validate_refusal(data)
    else:
        raise BudgetedContextResponseError("response.ok: must be a boolean")


def _validate_success(data: Mapping[str, Any]) -> None:
    fmt = data.get("format")
    if fmt not in _FORMAT_FIELDS:
        raise BudgetedContextResponseError(f"response.format: unsupported format {fmt!r}")
    _exact(data, _COMMON_FIELDS | _FORMAT_FIELDS[fmt], frozenset(), "response")
    _sha256(data["request_id"], "response.request_id")
    accounting = _accounting(data["accounting"], "response.accounting")
    if accounting["used_tokens"] > accounting["budget_tokens"]:
        raise BudgetedContextResponseError("response.accounting.used_tokens: exceeds budget_tokens")
    if accounting["exact_compliance"] is not (accounting["mode"] == "exact"):
        raise BudgetedContextResponseError(
            "response.accounting.exact_compliance: exact mode output is counted exactly"
        )
    _validate_changes(data["changes"])
    if fmt == "json":
        _validate_context(data["context"])
    elif fmt == "packet":
        _validate_packet(data["packet"])
    else:
        context_packet._string_list(data["warnings"], "response.warnings")
        _validate_metadata(data["metadata"])


def _accounting(value: object, field: str) -> Mapping[str, Any]:
    accounting = _object(value, field)
    _exact(accounting, _ACCOUNTING_FIELDS, frozenset(), field)
    for name in ("budget_tokens", "used_tokens"):
        context_packet._nonnegative_integer(accounting[name], f"{field}.{name}")
    _text(accounting["counter_id"], f"{field}.counter_id")
    if accounting["mode"] not in _BUDGET_MODES:
        raise BudgetedContextResponseError(f"{field}.mode: must be exact or estimated")
    if not isinstance(accounting["exact_compliance"], bool):
        raise BudgetedContextResponseError(f"{field}.exact_compliance: must be a boolean")
    if accounting["exact_compliance"] and accounting["mode"] != "exact":
        raise BudgetedContextResponseError(
            f"{field}.exact_compliance: only exact mode can claim exact compliance"
        )
    if accounting["usage_kind"] != _USAGE_KIND:
        raise BudgetedContextResponseError(f"{field}.usage_kind: must be {_USAGE_KIND}")
    if accounting["scope"] != _SCOPE:
        raise BudgetedContextResponseError(f"{field}.scope: must be {_SCOPE}")
    return accounting


def _validate_changes(value: object) -> None:
    changes = _object(value, "response.changes")
    if changes == _LEGACY_CHANGES:
        return
    _exact(changes, _CHANGE_FIELDS, frozenset(), "response.changes")
    request = _object(changes["request"], "response.changes.request")
    mode = request.get("mode")
    if mode not in _CHANGE_REQUEST_FIELDS:
        raise BudgetedContextResponseError(
            f"response.changes.request.mode: unsupported change mode {mode!r}"
        )
    _exact(request, _CHANGE_REQUEST_FIELDS[mode], frozenset(), "response.changes.request")
    if mode == "staged":
        _sha256(request["index_id"], "response.changes.request.index_id")
        requested = {"mode": mode}
    elif mode == "range":
        commits = _object(request["commits"], "response.changes.request.commits")
        _exact(commits, {"base", "head"}, frozenset(), "response.changes.request.commits")
        for side in ("base", "head"):
            if not isinstance(commits[side], str) or _COMMIT.fullmatch(commits[side]) is None:
                raise BudgetedContextResponseError(
                    f"response.changes.request.commits.{side}: must be a full commit id"
                )
        requested = {"mode": mode, "base": request["base"], "head": request["head"]}
    else:
        requested = {"mode": mode, "paths": request["paths"]}
    try:
        normalized = context_request_format.validate_changes(requested)
    except ValueError as exc:
        raise BudgetedContextResponseError(f"response.changes.request: {exc}") from exc
    if normalized != requested:
        raise BudgetedContextResponseError(
            "response.changes.request.paths: must be sorted, unique and normalized"
        )
    paths = _portable_paths(changes["paths"], "response.changes.paths")
    if changes["path_basis"] != "source-root":
        raise BudgetedContextResponseError("response.changes.path_basis: must be source-root")
    if not isinstance(changes["selection_boundary_changed"], bool):
        raise BudgetedContextResponseError(
            "response.changes.selection_boundary_changed: must be a boolean"
        )
    expected_id = "sha256:" + hashlib.sha256(
        json.dumps(paths, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if changes["paths_id"] != expected_id:
        raise BudgetedContextResponseError("response.changes.paths_id: does not hash paths")
    affected = _object(changes["affected_pages"], "response.changes.affected_pages")
    if set(affected) != set(paths):
        raise BudgetedContextResponseError(
            "response.changes.affected_pages: must map exactly the changed paths"
        )
    for path, pages in affected.items():
        field = f"response.changes.affected_pages.{path}"
        pages = _portable_paths(pages, field)
        if any(not page.endswith(".md") for page in pages):
            raise BudgetedContextResponseError(f"{field}: must name Markdown pages")


def _portable_paths(value: object, field: str) -> list[str]:
    paths = context_packet._string_list(value, field)
    for path in paths:
        try:
            normalized = context_request_format.portable_path(path)
        except ValueError as exc:
            raise BudgetedContextResponseError(f"{field}: {exc}") from exc
        if normalized != path:
            raise BudgetedContextResponseError(f"{field}: paths must be normalized")
    if paths != sorted(set(paths)):
        raise BudgetedContextResponseError(f"{field}: must be sorted and unique")
    return paths


def _validate_context(value: object) -> None:
    context = _object(value, "response.context")
    if context.get("protocol") != CONTEXT_KNOWLEDGE_PROTOCOL_VERSION:
        raise BudgetedContextResponseError(
            f"response.context.protocol: must be {CONTEXT_KNOWLEDGE_PROTOCOL_VERSION}"
        )
    if context.get("ok") is not True or context.get("format") != "json":
        raise BudgetedContextResponseError("response.context: must be a successful JSON context")
    if "source_priorities" not in context:
        raise BudgetedContextResponseError("response.context.source_priorities: is required")
    context_response_format.validate_context_response(context)


def _validate_packet(value: object) -> None:
    packet = _object(value, "response.packet")
    if packet.get("schema_version") != _PACKET_SCHEMA_VERSION:
        raise BudgetedContextResponseError(
            f"response.packet.schema_version: must be {_PACKET_SCHEMA_VERSION}"
        )
    context_packet.validate_context_packet(context_packet._encode_packet_payload(packet))


def _validate_metadata(value: object) -> None:
    metadata = _object(value, "response.metadata")
    _exact(metadata, _METADATA_REQUIRED, _METADATA_OPTIONAL, "response.metadata")
    budget = context_packet._nonnegative_integer(metadata["budget"], "response.metadata.budget")
    used = context_packet._nonnegative_integer(metadata["used"], "response.metadata.used")
    if used > budget:
        raise BudgetedContextResponseError("response.metadata.used: exceeds budget")
    if not isinstance(metadata["truncated"], bool):
        raise BudgetedContextResponseError("response.metadata.truncated: must be a boolean")
    context_packet._string_list(metadata["omitted_files"], "response.metadata.omitted_files")
    _object(metadata["downgraded_files"], "response.metadata.downgraded_files")
    context_packet._validate_explicit_source_bounds(metadata)
    knowledge = _object(metadata["knowledge"], "response.metadata.knowledge")
    context_packet._validate_explicit_knowledge_response(
        knowledge,
        {"knowledge_mode": knowledge.get("mode")},
        source_priorities=context_packet._explicit_response_source_priorities(metadata),
    )
    if "ranking_policy" in metadata:
        context_packet._validate_explicit_ranking_policy(
            metadata["ranking_policy"], knowledge, response_truncated=metadata["truncated"]
        )


def _validate_invalid_request(data: Mapping[str, Any]) -> None:
    _exact(data, {"protocol", "ok", "error"}, frozenset(), "response")
    error = _object(data["error"], "response.error")
    if error.get("code") != "invalid_request":
        raise BudgetedContextResponseError(
            f"response.error.code: unsupported error code {error.get('code')!r}"
        )
    _exact(error, {"code", "message"}, {"field"}, "response.error")
    _text(error["message"], "response.error.message")
    if "field" in error:
        _text(error["field"], "response.error.field")


def _validate_refusal(data: Mapping[str, Any]) -> None:
    _exact(data, {"protocol", "ok", "error", "accounting", "diagnostics"}, frozenset(), "response")
    if data["error"] != "cannot-fit":
        raise BudgetedContextResponseError(f"response.error: unsupported error {data['error']!r}")
    accounting = _accounting(data["accounting"], "response.accounting")
    if accounting["exact_compliance"]:
        raise BudgetedContextResponseError(
            "response.accounting.exact_compliance: a refusal claims no compliance"
        )
    if accounting["used_tokens"] <= accounting["budget_tokens"]:
        raise BudgetedContextResponseError(
            "response.accounting.used_tokens: a refused candidate must exceed the budget"
        )
    diagnostics = _object(data["diagnostics"], "response.diagnostics")
    field = "response.diagnostics"
    _exact(diagnostics, _REFUSAL_FIELDS, frozenset(), field)
    if diagnostics["schema_version"] != CONTEXT_BUDGET_REFUSAL_SCHEMA_VERSION:
        raise BudgetedContextResponseError(
            f"{field}.schema_version: must be {CONTEXT_BUDGET_REFUSAL_SCHEMA_VERSION}"
        )
    _sha256(diagnostics["request_id"], f"{field}.request_id")
    if diagnostics["selection_policy"] not in _SELECTION_POLICIES:
        raise BudgetedContextResponseError(f"{field}.selection_policy: unsupported policy")
    for name, expected in _REFUSAL_CONSTANTS.items():
        if diagnostics[name] != expected:
            raise BudgetedContextResponseError(f"{field}.{name}: must be {expected}")
    if diagnostics["counter_id"] != accounting["counter_id"]:
        raise BudgetedContextResponseError(f"{field}.counter_id: must match the accounting counter")
    if diagnostics["budget_mode"] != accounting["mode"]:
        raise BudgetedContextResponseError(f"{field}.budget_mode: must match the accounting mode")
    if diagnostics["emitted_context_bytes"] != 0 or isinstance(diagnostics["emitted_context_bytes"], bool):
        raise BudgetedContextResponseError(f"{field}.emitted_context_bytes: a refusal emits nothing")
    source = _object(diagnostics["source"], f"{field}.source")
    _exact(source, {"total", "returned", "omitted"}, frozenset(), f"{field}.source")
    counts = {
        name: context_packet._nonnegative_integer(source[name], f"{field}.source.{name}")
        for name in ("total", "returned", "omitted")
    }
    if counts["total"] != counts["returned"] + counts["omitted"]:
        raise BudgetedContextResponseError(
            f"{field}.source.total: must equal returned plus omitted"
        )
    _validate_native(diagnostics["native"], f"{field}.native")
    components = _object(diagnostics["component_bytes"], f"{field}.component_bytes")
    _exact(components, _COMPONENT_FIELDS, frozenset(), f"{field}.component_bytes")
    if components["measurement"] != _COMPONENT_MEASUREMENT:
        raise BudgetedContextResponseError(
            f"{field}.component_bytes.measurement: must be {_COMPONENT_MEASUREMENT}"
        )
    for name in sorted(_COMPONENT_FIELDS - {"measurement"}):
        context_packet._nonnegative_integer(components[name], f"{field}.component_bytes.{name}")
    recovery = diagnostics["recovery"]
    if not isinstance(recovery, list) or len(recovery) != len(_RECOVERY_ROUTES):
        raise BudgetedContextResponseError(f"{field}.recovery: must list both recovery routes")
    for index, (route, expected) in enumerate(zip(recovery, _RECOVERY_ROUTES)):
        route_field = f"{field}.recovery[{index}]"
        route = _object(route, route_field)
        _exact(route, {"id", "automatic", "new_request_binding_required", "description"},
               frozenset(), route_field)
        if route["id"] != expected:
            raise BudgetedContextResponseError(f"{route_field}.id: must be {expected}")
        if route["automatic"] is not False or route["new_request_binding_required"] is not True:
            raise BudgetedContextResponseError(
                f"{route_field}: recovery is never automatic and needs a new request"
            )
        _text(route["description"], f"{route_field}.description")


def _validate_native(value: object, field: str) -> None:
    native = _object(value, field)
    _exact(native, {"mode", "status", "availability", "bounds"}, frozenset(), field)
    if native["mode"] not in _NATIVE_MODES:
        raise BudgetedContextResponseError(f"{field}.mode: unsupported knowledge mode")
    if native["status"] not in _NATIVE_STATUSES:
        raise BudgetedContextResponseError(f"{field}.status: unsupported knowledge status")
    if native["availability"] not in _NATIVE_AVAILABILITY:
        raise BudgetedContextResponseError(f"{field}.availability: unsupported availability")
    bounds = _object(native["bounds"], f"{field}.bounds")
    for name, bound in bounds.items():
        if name not in _NATIVE_COLLECTIONS:
            raise BudgetedContextResponseError(f"{field}.bounds.{name}: is not supported")
        context_packet._validate_collection_bound(bound, f"{field}.bounds.{name}")


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise BudgetedContextResponseError(f"{field}: must be a JSON object")
    return value


def _exact(
    value: Mapping[str, Any], required: set[str] | frozenset[str],
    optional: set[str] | frozenset[str], field: str,
) -> None:
    missing = sorted(set(required) - set(value))
    if missing:
        raise BudgetedContextResponseError(f"{field}.{missing[0]}: is required")
    unknown = sorted(set(value) - set(required) - set(optional))
    if unknown:
        raise BudgetedContextResponseError(f"{field}.{unknown[0]}: is not supported")


def _text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise BudgetedContextResponseError(f"{field}: must be a non-empty string")


def _sha256(value: object, field: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise BudgetedContextResponseError(f"{field}: must be a sha256 digest")
