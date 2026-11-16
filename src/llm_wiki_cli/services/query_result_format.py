"""Format checks for documentation query results and wiki search results.

``llm-wiki-documentation-query/v1`` is the envelope ``query_documentation``
returns for every operation; ``llm-wiki-search-result/v1`` is what wiki
search returns from the CLI, MCP and the Python API. These checks read no
repository or wiki state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

DOCUMENTATION_QUERY_SCHEMA_VERSION = "llm-wiki-documentation-query/v1"
SEARCH_RESULT_SCHEMA_VERSION = "llm-wiki-search-result/v1"

DOCUMENTATION_QUERY_OPERATIONS = (
    "explain", "concept", "related", "surface", "typed", "symbol", "entrypoint",
    "flow-segment", "dependency", "impact",
)
QUERY_COST_SCOPES = ("snapshot-index-only", "targeted-extraction", "full-inventory")

#: Field families of a documentation query result. Values are kept as
#: produced by each operation; only their JSON type is part of the format.
_QUERY_STRING_FIELDS = frozenset({"direction", "segment_schema"})
_QUERY_NULLABLE_STRING_FIELDS = frozenset({"basis", "path"})
_QUERY_COUNT_FIELDS = frozenset({"total", "returned"})
_QUERY_BOOLEAN_FIELDS = frozenset({"include_evidence"})
_QUERY_OBJECT_FIELDS = frozenset({
    "knowledge", "provenance", "typed_graph", "coverage", "work", "follow_up", "metrics",
})
_QUERY_NULLABLE_OBJECT_FIELDS = frozenset({
    "evidence", "concept", "symbol", "flow", "data_flow", "owner", "callable", "maintenance",
})
_QUERY_STRING_LIST_FIELDS = frozenset({
    "kinds", "origins", "resolutions", "inbound", "outbound", "impacted_paths", "limitations",
})
_QUERY_OBJECT_LIST_FIELDS = frozenset({
    "relationships", "related_concepts", "unresolved_targets", "external_targets", "edges",
    "pages", "callers", "callees", "steps", "cycle_groups", "concepts", "raw_evidence",
    "sections",
})
_QUERY_ENVELOPE_FIELDS = frozenset({
    "schema_version", "operation", "query", "found", "ambiguous", "matches", "bounds",
    "truncated", "cost",
})
QUERY_PAYLOAD_FIELDS = (
    _QUERY_STRING_FIELDS | _QUERY_NULLABLE_STRING_FIELDS | _QUERY_COUNT_FIELDS
    | _QUERY_BOOLEAN_FIELDS | _QUERY_OBJECT_FIELDS | _QUERY_NULLABLE_OBJECT_FIELDS
    | _QUERY_STRING_LIST_FIELDS | _QUERY_OBJECT_LIST_FIELDS
    | {"load_order_index", "result_omitted"}
)
#: Fields an operation always returns unless its records were omitted.
QUERY_OPERATION_FIELDS: Mapping[str, frozenset[str]] = {
    "concept": frozenset({"concept", "knowledge"}),
    "explain": frozenset({"concept", "evidence", "knowledge", "total", "returned"}),
    "symbol": frozenset({"pages", "callers", "callees"}),
    "impact": frozenset({
        "concepts", "impacted_paths", "knowledge", "limitations", "pages", "relationships",
    }),
}
QUERY_RESULT_OMITTED_REASON = "serialized-result-byte-limit"

SEARCH_MODES = ("ranked", "ranked-v1", "ranked-v2", "substring")
#: The wiki page kinds a search result can return.
SEARCH_PAGE_KINDS = (
    "api-contracts", "dependencies", "entities", "flows", "guides", "index", "infrastructure",
    "load-order", "log", "modules", "workflows",
)
#: The ranking version each ranked mode reports.
SEARCH_RANKINGS: Mapping[str, str] = {
    "ranked": "llm-wiki-search/lexical-v2",
    "ranked-v2": "llm-wiki-search/lexical-v2",
    "ranked-v1": "llm-wiki-search/lexical-v1",
}
SEARCH_DISCOVERY_SCHEMA_VERSION = "llm-wiki-discovery/v1"
SEARCH_SOURCE_INDEX_SCHEMA_VERSION = "llm-wiki-source-search-index/v1"
_SEARCH_ENVELOPE_FIELDS = frozenset({
    "schema_version", "query", "mode", "total", "returned", "count", "truncated", "bounds",
    "results",
})
_SEARCH_RANKED_FIELDS = frozenset({"ranking", "corpus_id", "scanned", "resource_limits"})
_SEARCH_CURRENT_FIELDS = frozenset({"experimental", "definitive_answer"})
_SEARCH_MATCH_FIELDS = frozenset({"kind", "id", "uri", "path", "title", "snippet"})
_SEARCH_RANKED_MATCH_FIELDS = frozenset({"score", "reasons", "provenance"})
_SEARCH_SECTION_FIELDS = frozenset({"matched_sections", "matched_section_locations"})
_SEARCH_MAX_RESULTS = 100


class QueryResultError(ValueError):
    """A documentation query or search result does not follow its format."""


def validate_documentation_query_result(document: object) -> None:
    """Raise ``QueryResultError`` unless *document* is a documentation query result."""
    data = _object(document, "result")
    _fields(data, _QUERY_ENVELOPE_FIELDS, QUERY_PAYLOAD_FIELDS, "result")
    if data["schema_version"] != DOCUMENTATION_QUERY_SCHEMA_VERSION:
        raise QueryResultError("result.schema_version: unsupported format")
    operation = data["operation"]
    if operation not in DOCUMENTATION_QUERY_OPERATIONS:
        raise QueryResultError(f"result.operation: unsupported operation {operation!r}")
    for name in ("found", "ambiguous", "truncated"):
        _boolean(data[name], f"result.{name}")
    matches = _objects(data["matches"], "result.matches")
    bounds = _object(data["bounds"], "result.bounds")
    any_truncated = False
    for name, bound in bounds.items():
        any_truncated |= _bound(bound, f"result.bounds.{name}")
    if "matches" not in bounds:
        raise QueryResultError("result.bounds.matches: is required")
    if bounds["matches"]["returned"] != len(matches):
        raise QueryResultError("result.bounds.matches: does not count the returned matches")
    if data["truncated"] is not any_truncated:
        raise QueryResultError("result.truncated: must report whether any bound is truncated")
    _cost(data["cost"])
    for name in data.keys() - _QUERY_ENVELOPE_FIELDS:
        _payload_field(name, data[name])
    if "result_omitted" in data:
        omitted = _object(data["result_omitted"], "result.result_omitted")
        _fields(omitted, {"reason", "records_returned"}, set(), "result.result_omitted")
        if omitted["reason"] != QUERY_RESULT_OMITTED_REASON or omitted["records_returned"] != 0:
            raise QueryResultError("result.result_omitted: unsupported omission")
        if matches or data["truncated"] is not True:
            raise QueryResultError("result.result_omitted: an omitted result returns no records")
        return
    missing = sorted(QUERY_OPERATION_FIELDS.get(operation, frozenset()) - set(data))
    if missing:
        raise QueryResultError(f"result.{missing[0]}: is required for {operation}")


def validate_search_result(document: object) -> None:
    """Raise ``QueryResultError`` unless *document* is a wiki search result."""
    data = _object(document, "result")
    mode = data.get("mode")
    if mode not in SEARCH_MODES:
        raise QueryResultError(f"result.mode: unsupported mode {mode!r}")
    ranked = mode != "substring"
    required = set(_SEARCH_ENVELOPE_FIELDS)
    if ranked:
        required |= _SEARCH_RANKED_FIELDS
    if mode in ("ranked", "ranked-v2"):
        required |= _SEARCH_CURRENT_FIELDS
    _fields(data, required, {"source_indexing", "discovery"}, "result")
    if data["schema_version"] != SEARCH_RESULT_SCHEMA_VERSION:
        raise QueryResultError("result.schema_version: unsupported format")
    if not isinstance(data["query"], str) or not data["query"].strip():
        raise QueryResultError("result.query: must be a non-blank string")
    results = _objects(data["results"], "result.results")
    if len(results) > _SEARCH_MAX_RESULTS:
        raise QueryResultError("result.results: returns at most 100 results")
    bounds = _object(data["bounds"], "result.bounds")
    _fields(bounds, {"results"}, set(), "result.bounds")
    truncated = _bound(bounds["results"], "result.bounds.results")
    if "limit" in bounds["results"]:
        raise QueryResultError("result.bounds.results.limit: is not supported")
    for name in ("total", "returned", "count"):
        _count(data[name], f"result.{name}")
    if not (data["returned"] == data["count"] == len(results) == bounds["results"]["returned"]):
        raise QueryResultError("result.returned: must count the returned results")
    if data["total"] != bounds["results"]["total"] or data["truncated"] is not truncated:
        raise QueryResultError("result.bounds: must match total and truncated")
    if ranked:
        if data["ranking"] != SEARCH_RANKINGS[mode]:
            raise QueryResultError(f"result.ranking: {mode} reports {SEARCH_RANKINGS[mode]}")
        _text(data["corpus_id"], "result.corpus_id")
        for name in ("scanned", "resource_limits"):
            usage = _object(data[name], f"result.{name}")
            _fields(usage, {"bytes", "pages"}, set(), f"result.{name}")
            _count(usage["bytes"], f"result.{name}.bytes")
            _count(usage["pages"], f"result.{name}.pages")
    if mode in ("ranked", "ranked-v2"):
        if data["experimental"] is not False or data["definitive_answer"] is not False:
            raise QueryResultError("result: ranked search is neither experimental nor definitive")
    for name, version in (
        ("source_indexing", SEARCH_SOURCE_INDEX_SCHEMA_VERSION),
        ("discovery", SEARCH_DISCOVERY_SCHEMA_VERSION),
    ):
        if name in data and _object(data[name], f"result.{name}").get("schema_version") != version:
            raise QueryResultError(f"result.{name}.schema_version: must be {version}")
    if "source_indexing" in data and mode not in ("ranked", "ranked-v2"):
        raise QueryResultError("result.source_indexing: requires current ranked mode")
    for index, match in enumerate(results):
        _search_match(match, mode, indexed="source_indexing" in data, field=f"result.results[{index}]")


def _search_match(match: Mapping[str, Any], mode: str, *, indexed: bool, field: str) -> None:
    required = set(_SEARCH_MATCH_FIELDS)
    if mode != "substring":
        required |= _SEARCH_RANKED_MATCH_FIELDS
    if mode in ("ranked", "ranked-v2"):
        required |= _SEARCH_SECTION_FIELDS
    _fields(match, required, {"indexing"} if indexed else set(), field)
    for name in _SEARCH_MATCH_FIELDS:
        if not isinstance(match[name], str):
            raise QueryResultError(f"{field}.{name}: must be a string")
    if match["kind"] not in SEARCH_PAGE_KINDS:
        raise QueryResultError(f"{field}.kind: unsupported page kind")
    if mode == "substring":
        return
    score = match["score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise QueryResultError(f"{field}.score: must be a number")
    _strings(match["reasons"], f"{field}.reasons")
    _object(match["provenance"], f"{field}.provenance")
    if mode in ("ranked", "ranked-v2"):
        _list(match["matched_sections"], f"{field}.matched_sections")
        _objects(match["matched_section_locations"], f"{field}.matched_section_locations")
    if "indexing" in match:
        _object(match["indexing"], f"{field}.indexing")


def _payload_field(name: str, value: object) -> None:
    field = f"result.{name}"
    if name in _QUERY_STRING_FIELDS:
        _text(value, field)
    elif name in _QUERY_NULLABLE_STRING_FIELDS:
        if value is not None:
            _text(value, field)
    elif name in _QUERY_COUNT_FIELDS:
        _count(value, field)
    elif name in _QUERY_BOOLEAN_FIELDS:
        _boolean(value, field)
    elif name in _QUERY_OBJECT_FIELDS:
        _object(value, field)
    elif name in _QUERY_NULLABLE_OBJECT_FIELDS:
        if value is not None:
            _object(value, field)
    elif name in _QUERY_STRING_LIST_FIELDS:
        _strings(value, field)
    elif name in _QUERY_OBJECT_LIST_FIELDS:
        _objects(value, field)
    elif name == "load_order_index":
        if value is not None:
            _count(value, field)


def _cost(value: object) -> None:
    cost = _object(value, "result.cost")
    _fields(cost, {"scope", "full_inventory_performed", "supplied_paths"}, set(), "result.cost")
    if cost["scope"] not in QUERY_COST_SCOPES:
        raise QueryResultError("result.cost.scope: unsupported scope")
    if cost["full_inventory_performed"] is not (cost["scope"] == "full-inventory"):
        raise QueryResultError("result.cost.full_inventory_performed: must match the scope")
    _count(cost["supplied_paths"], "result.cost.supplied_paths")


def _bound(value: object, field: str) -> bool:
    bound = _object(value, field)
    _fields(bound, {"total", "returned", "truncated"}, {"limit"}, field)
    total = _count(bound["total"], f"{field}.total")
    returned = _count(bound["returned"], f"{field}.returned")
    _boolean(bound["truncated"], f"{field}.truncated")
    if returned > total or bound["truncated"] is not (total > returned):
        raise QueryResultError(f"{field}: returned and truncated must follow total")
    if "limit" in bound and returned > _count(bound["limit"], f"{field}.limit"):
        raise QueryResultError(f"{field}: returned exceeds the limit")
    return bound["truncated"]


def _fields(
    value: Mapping[str, Any], required: set[str] | frozenset[str],
    optional: set[str] | frozenset[str], field: str,
) -> None:
    missing = sorted(set(required) - set(value))
    if missing:
        raise QueryResultError(f"{field}.{missing[0]}: is required")
    unknown = sorted(set(value) - set(required) - set(optional))
    if unknown:
        raise QueryResultError(f"{field}.{unknown[0]}: is not supported")


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise QueryResultError(f"{field}: must be a JSON object")
    return value


def _list(value: object, field: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise QueryResultError(f"{field}: must be an array")
    return value


def _objects(value: object, field: str) -> list[Mapping[str, Any]]:
    return [_object(item, f"{field}[{index}]") for index, item in enumerate(_list(value, field))]


def _strings(value: object, field: str) -> None:
    if any(not isinstance(item, str) for item in _list(value, field)):
        raise QueryResultError(f"{field}: must be an array of strings")


def _count(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise QueryResultError(f"{field}: must be a non-negative integer")
    return value


def _boolean(value: object, field: str) -> None:
    if not isinstance(value, bool):
        raise QueryResultError(f"{field}: must be a boolean")


def _text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise QueryResultError(f"{field}: must be a non-empty string")
