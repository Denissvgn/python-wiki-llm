"""Format checks for the ``llm-wiki-extract/v1`` source inventory payload.

``extract`` prints a per-file source inventory plus, under ``--deep``, entry
points, data flows, dependency and API-contract analysis. The format is
additive: consumers must tolerate fields they do not know, so file records
and analysis blocks stay open and only the fields every consumer relies on
are checked. The versioned ``data_flow_details`` sibling is strict.

These checks read no source files: they confirm a decoded payload is
internally consistent. A summary payload (``extract --summary``) lists symbol
names as strings; a full payload lists symbol records.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .contracts import (
    EXTRACT_DATA_FLOW_DETAILS_SCHEMA_VERSION as EXTRACT_DATA_FLOW_DETAILS_SCHEMA_VERSION,
    EXTRACT_SCHEMA_VERSION as EXTRACT_SCHEMA_VERSION,
)
from .validation import SharedValidationError, require_portable_relative_path

#: Symbol lists a summary collapses to names; a full payload lists records.
#: ``exports`` lists names in both, so it is not one of them.
EXTRACT_SYMBOL_LISTS = ("classes", "functions", "imports", "constants", "module_calls")
#: Symbol lists whose records always name their symbol.
EXTRACT_NAMED_SYMBOL_LISTS = ("classes", "functions")
#: Blocks ``extract --deep`` adds; they appear together or not at all.
EXTRACT_DEEP_BLOCKS = ("api_contracts", "dependencies", "data_flows")
#: Each ``data_flow_details`` state with the reason it carries.
DATA_FLOW_DETAILS_STATES = {
    "evaluated": None,
    "not_evaluated": "deep-analysis-disabled",
    "unsupported": "no-supported-language-analyzer",
}
DATA_FLOW_DETAILS_FIELDS = (
    "schema_version", "state", "reason", "flows", "coverage", "effective_limits",
)
DATA_FLOW_DETAILS_COVERAGE_FIELDS = (
    "observed", "emitted", "omitted", "limit", "truncated", "truncation_reason",
    "upstream_analyzer_limitations",
)
DATA_FLOW_EFFECTIVE_LIMIT_FIELDS = (
    "flows_per_extract", "flow_depth", "steps_per_flow", "effects_per_kind_per_step",
    "boundaries_per_flow", "transfers_per_flow", "gaps_per_flow",
)
DATA_FLOW_TRUNCATION_REASON = "collection-limit"
UNSUPPORTED_LIMITATION_PREFIX = "unsupported-source-language:"

_Check = Callable[[object], bool]


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _string(value: object) -> bool:
    return isinstance(value, str)


def _string_or_null(value: object) -> bool:
    return value is None or isinstance(value, str)


def _array(value: object) -> bool:
    return isinstance(value, list)


def _object(value: object) -> bool:
    return isinstance(value, Mapping)


def _count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _positive(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


_ENTRYPOINT_FIELDS: dict[str, _Check] = {
    "id": _text, "category": _string, "file": _string_or_null, "symbol": _string, "label": _string,
}
_ENTRYPOINT_OPTIONAL: dict[str, _Check] = {"routes": _array, "related_modules": _array}
_DEPENDENCY_FIELDS: dict[str, _Check] = {
    "edges": _array, "cycles": _array, "external": _object, "load_order": _object,
}
_DEPENDENCY_OPTIONAL: dict[str, _Check] = {"version_details": _object}
_API_CONTRACT_FIELDS: dict[str, _Check] = {
    "source": _string, "applications": _array, "operations": _array, "diagnostics": _array,
}
_COVERAGE_CHECKS: dict[str, _Check] = {
    "observed": _count, "emitted": _count, "omitted": _count, "limit": _positive,
    "truncated": lambda value: isinstance(value, bool),
    "truncation_reason": lambda value: value in (DATA_FLOW_TRUNCATION_REASON, None),
    "upstream_analyzer_limitations": _array,
}


class ExtractPayloadError(ValueError):
    """An extract payload does not follow its format."""


def validate_extract_payload(document: object) -> None:
    """Raise ``ExtractPayloadError`` unless *document* is a valid extract payload."""

    payload = _mapping(document, "payload")
    if payload.get("schema_version") != EXTRACT_SCHEMA_VERSION:
        raise ExtractPayloadError(f"schema_version: expected {EXTRACT_SCHEMA_VERSION!r}")
    inventory = _mapping(payload.get("inventory"), "inventory")
    _check_inventory(inventory)
    for path, record in _mapping(payload.get("docker", {}), "docker").items():
        _portable(path, f"docker[{path!r}]")
        _mapping(record, f"docker[{path!r}]")
    unsupported = _check_unsupported(payload.get("unsupported_sources", {}))
    warnings = _sequence(payload.get("warnings", []), "warnings")
    if not all(isinstance(warning, str) for warning in warnings):
        raise ExtractPayloadError("warnings: must be strings")

    present = [name for name in EXTRACT_DEEP_BLOCKS if name in payload]
    if present and len(present) != len(EXTRACT_DEEP_BLOCKS):
        raise ExtractPayloadError(
            f"{', '.join(EXTRACT_DEEP_BLOCKS)} appear together; found only {', '.join(present)}"
        )
    deep = bool(present)
    if deep:
        _fields(payload["dependencies"], "dependencies", _DEPENDENCY_FIELDS, _DEPENDENCY_OPTIONAL)
        contracts = _fields(payload["api_contracts"], "api_contracts", _API_CONTRACT_FIELDS)
        excluded = _mapping(contracts.get("excluded_counts", {}), "api_contracts.excluded_counts")
        if not all(_count(value) for value in excluded.values()):
            raise ExtractPayloadError("api_contracts.excluded_counts: must be counts")
    entrypoints = _check_entrypoints(payload.get("entrypoints", []), deep=deep)
    flows = _sequence(payload["data_flows"], "data_flows") if deep else None
    if flows is not None and _ids(flows, "data_flows") != entrypoints:
        raise ExtractPayloadError("data_flows: must describe each entry point in order")
    if "data_flow_details" in payload:
        _check_data_flow_details(
            payload["data_flow_details"], deep=deep, flows=flows,
            empty_inventory=not inventory, unsupported=unsupported,
        )


def _check_inventory(inventory: Mapping[str, Any]) -> None:
    item_kinds: set[type] = set()
    for path, record in inventory.items():
        field = f"inventory[{path!r}]"
        _portable(path, field)
        record = _mapping(record, field)
        if "language" in record and not _text(record["language"]):
            raise ExtractPayloadError(f"{field}.language: must name a language")
        if not _string_or_null(record.get("package")):
            raise ExtractPayloadError(f"{field}.package: must be a string or null")
        for name in (*EXTRACT_SYMBOL_LISTS, "exports"):
            for index, item in enumerate(_sequence(record.get(name, []), f"{field}.{name}")):
                if not isinstance(item, (str, Mapping)):
                    raise ExtractPayloadError(f"{field}.{name}[{index}]: must be a name or a record")
                if name in EXTRACT_SYMBOL_LISTS:
                    item_kinds.add(str if isinstance(item, str) else dict)
                if isinstance(item, Mapping) and name in EXTRACT_NAMED_SYMBOL_LISTS:
                    if not _text(item.get("name")):
                        raise ExtractPayloadError(f"{field}.{name}[{index}].name: must be a symbol name")
    if len(item_kinds) > 1:
        raise ExtractPayloadError(
            "inventory: symbol lists hold either names (summary) or records, not both"
        )


def _check_unsupported(value: object) -> frozenset[str]:
    unsupported = _mapping(value, "unsupported_sources")
    for language, entry in unsupported.items():
        field = f"unsupported_sources[{language!r}]"
        entry = _fields(entry, field, {"count": _positive, "paths": _array}, closed=True)
        paths = entry["paths"]
        for path in paths:
            _portable(path, f"{field}.paths")
        if not paths or len(set(paths)) != len(paths):
            raise ExtractPayloadError(f"{field}.paths: must list each source once")
        if entry["count"] != len(paths):
            raise ExtractPayloadError(f"{field}.count: must count its paths")
    return frozenset(unsupported)


def _check_entrypoints(value: object, *, deep: bool) -> list[str]:
    entrypoints = _sequence(value, "entrypoints")
    if entrypoints and not deep:
        raise ExtractPayloadError("entrypoints: only extract --deep detects entry points")
    for index, entry in enumerate(entrypoints):
        _fields(entry, f"entrypoints[{index}]", _ENTRYPOINT_FIELDS, _ENTRYPOINT_OPTIONAL)
    ids = _ids(entrypoints, "entrypoints")
    if len(set(ids)) != len(ids):
        raise ExtractPayloadError("entrypoints: ids must be unique")
    return ids


def _check_data_flow_details(
    value: object, *, deep: bool, flows: Sequence[Any] | None,
    empty_inventory: bool, unsupported: frozenset[str],
) -> None:
    details = _mapping(value, "data_flow_details")
    if set(details) != set(DATA_FLOW_DETAILS_FIELDS):
        raise ExtractPayloadError(f"data_flow_details: must have exactly {', '.join(DATA_FLOW_DETAILS_FIELDS)}")
    if details["schema_version"] != EXTRACT_DATA_FLOW_DETAILS_SCHEMA_VERSION:
        raise ExtractPayloadError(
            f"data_flow_details.schema_version: expected {EXTRACT_DATA_FLOW_DETAILS_SCHEMA_VERSION!r}"
        )
    state = details["state"]
    if state not in DATA_FLOW_DETAILS_STATES or details["reason"] != DATA_FLOW_DETAILS_STATES[state]:
        raise ExtractPayloadError("data_flow_details: state and reason do not match")
    expected = (
        "not_evaluated" if not deep
        else "unsupported" if empty_inventory and unsupported
        else "evaluated"
    )
    if state != expected:
        raise ExtractPayloadError(f"data_flow_details.state: expected {expected!r} for this payload")
    coverage = _fields(details["coverage"], "data_flow_details.coverage", _COVERAGE_CHECKS, closed=True)
    limits = _fields(
        details["effective_limits"], "data_flow_details.effective_limits",
        dict.fromkeys(DATA_FLOW_EFFECTIVE_LIMIT_FIELDS, _positive), closed=True,
    )
    detailed = _ids(_sequence(details["flows"], "data_flow_details.flows"), "data_flow_details.flows")
    observed, limit = coverage["observed"], coverage["limit"]
    emitted = min(observed, limit)
    if (
        coverage["emitted"] != emitted or len(detailed) != emitted
        or coverage["omitted"] != observed - emitted
        or coverage["truncated"] is not (observed > emitted)
        or coverage["truncation_reason"] != (DATA_FLOW_TRUNCATION_REASON if observed > emitted else None)
    ):
        raise ExtractPayloadError(
            "data_flow_details.coverage: emitted flows are the first observed flows up to the limit"
        )
    if limits["flows_per_extract"] != limit:
        raise ExtractPayloadError("data_flow_details.coverage.limit: must be the flows_per_extract limit")
    if flows is None and observed:
        raise ExtractPayloadError("data_flow_details: flows need extract --deep")
    if flows is not None:
        if observed != len(flows):
            raise ExtractPayloadError("data_flow_details.coverage.observed: must count data_flows")
        if detailed != _ids(flows, "data_flows")[:emitted]:
            raise ExtractPayloadError("data_flow_details.flows: must detail the first data_flows in order")
    _check_limitations(coverage["upstream_analyzer_limitations"], unsupported)


def _check_limitations(limitations: Sequence[Any], unsupported: frozenset[str]) -> None:
    field = "data_flow_details.coverage.upstream_analyzer_limitations"
    if not all(_text(reason) for reason in limitations):
        raise ExtractPayloadError(f"{field}: must be reason codes")
    if list(limitations) != sorted(set(limitations)):
        raise ExtractPayloadError(f"{field}: must be sorted and unique")
    named = {
        reason.removeprefix(UNSUPPORTED_LIMITATION_PREFIX) for reason in limitations
        if reason.startswith(UNSUPPORTED_LIMITATION_PREFIX)
    }
    if named != unsupported:
        raise ExtractPayloadError(f"{field}: must name exactly the unsupported source languages")


def _fields(
    value: object, field: str, required: Mapping[str, _Check],
    optional: Mapping[str, _Check] | None = None, *, closed: bool = False,
) -> Mapping[str, Any]:
    record = _mapping(value, field)
    missing = sorted(set(required) - set(record))
    if missing:
        raise ExtractPayloadError(f"{field}: missing {', '.join(missing)}")
    if closed and set(record) != set(required):
        raise ExtractPayloadError(f"{field}: must have exactly {', '.join(required)}")
    checks = {**(optional or {}), **required}
    for name, check in checks.items():
        if name in record and not check(record[name]):
            raise ExtractPayloadError(f"{field}.{name}: has the wrong type or value")
    return record


def _ids(records: Sequence[Any], field: str) -> list[str]:
    ids = []
    for index, record in enumerate(records):
        record_id = _mapping(record, f"{field}[{index}]").get("id")
        if not _text(record_id):
            raise ExtractPayloadError(f"{field}[{index}].id: must be an id")
        ids.append(record_id)
    return ids


def _portable(value: object, field: str) -> None:
    if _canonical_portable_path(value) != value:
        raise ExtractPayloadError(f"{field}: must be a portable repository-relative path")


def _canonical_portable_path(value: object) -> str | None:
    try:
        return require_portable_relative_path(value)
    except SharedValidationError:
        return None


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExtractPayloadError(f"{field}: must be an object")
    return value


def _sequence(value: object, field: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ExtractPayloadError(f"{field}: must be an array")
    return value
