"""Published maintenance queue format: ``llm-wiki-maintenance-queue/v1``.

The queue is an advisory ranking of wiki pages that may need maintenance. The
format is additive, so consumers accept fields it does not list; the compact
maintenance summary and the source coordinates and semantic targets it embeds
keep their closed shapes. The checks here are the ones a JSON Schema cannot
express: counts add up, items are ranked by score and path and each score is
the sum of its reasons, an item's category and classification follow from its
evidence, coverage gaps and ordinary-review details count what they list,
review custody agrees with its evidence, an incompatible source selection
marks every item, and ``queue_id`` hashes the rest of the report.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .maintenance_status_format import (
    MaintenanceStatusError,
    check_coordinate,
    check_maintenance_summary,
    check_target,
)

MAINTENANCE_QUEUE_SCHEMA_VERSION = "llm-wiki-maintenance-queue/v1"
MIN_QUEUE_LIMIT = 1
MAX_QUEUE_LIMIT = 1000
QUEUE_MAX_DETAILS = 128
QUEUE_MAX_BYTES = 65536
FRESHNESS_STATES = (
    "current",
    "source-changed",
    "source-missing",
    "basis-incompatible",
    "nonsemantic-source-change",
    "unknown",
)
ORDINARY_CATEGORIES = ("ordinary-maintenance", "ordinary-coverage-gap")
ACTIONABLE_STATES = ("source-changed", "source-missing")
CLASSIFICATIONS = ("actionable", "informational")
LINT_SEVERITIES = ("error", "warning", "info")
CUSTODY_AVAILABILITY = ("ready", "partial", "unadopted", "unavailable")
CUSTODY_EVIDENCE = (
    "captured-maintenance-status",
    "validated-native-manifest",
    "no-validated-native-manifest",
)
TARGET_ATTRIBUTIONS = ("retained", "candidate")
INCOMPATIBLE_SELECTION_REASON = "source-selection-basis-incompatible"

QUEUE_FIELDS = (
    "schema_version",
    "advisory",
    "limit",
    "total",
    "returned",
    "omitted",
    "items",
    "qualification",
    "limitations",
    "diagnostics",
    "basis",
    "queue_id",
)
ITEM_FIELDS = (
    "path",
    "kind",
    "source_path",
    "classification",
    "observed_change_category",
    "freshness",
    "ownership",
    "placeholder_signals",
    "work_status",
    "lint_severity",
    "reachable_from_index",
    "source_fan_in",
    "score",
    "reasons",
)
COVERAGE_GAP_FIELDS = ("coverage_gaps", "coverage_gap_bounds")
ORDINARY_REVIEW_FIELDS = (
    "maintenance",
    "record_ids",
    "record_bounds",
    "semantic_targets",
    "semantic_target_bounds",
)
FRESHNESS_FIELDS = ("state", "reason", "description", "live_comparison_performed")
OWNERSHIP_FIELDS = ("surface_role", "semantic_section", "instruction")
REASON_FIELDS = ("code", "message", "weight")
GAP_BOUNDS_FIELDS = ("total", "returned", "omitted", "truncated")
RECORD_BOUNDS_FIELDS = ("total", "returned", "omitted", "truncated", "limit", "max_records", "max_bytes")
TARGET_BOUNDS_FIELDS = ("total", "returned", "omitted", "truncated", "max_records", "max_bytes")
SEMANTIC_TARGET_FIELDS = ("record_id", "coordinate", "target", "attribution")
QUALIFICATION_FIELDS = (
    "ordinary_review_custody",
    "freshness_states",
    "authoring_hint_pages",
    "scope",
    "limitations",
)
CUSTODY_FIELDS = (
    "availability",
    "durable_owner_available",
    "evidence",
    "live_evaluation_performed",
    "source_prose_correctness",
    "review_route",
    "limitation",
)
REVIEW_ROUTE_FIELDS = ("interface", "instruction")
BASIS_FIELDS = ("source_identity", "wiki_identity", "knowledge_reason", "source_selection_compatible")
DIAGNOSTIC_FIELDS = ("category", "severity", "message")
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


class MaintenanceQueueError(ValueError):
    """A maintenance queue report does not satisfy its published format."""


def validate_maintenance_queue(document: object) -> None:
    """Raise ``MaintenanceQueueError`` unless ``document`` is a valid queue report."""
    try:
        _validate(document)
    except MaintenanceStatusError as exc:
        raise MaintenanceQueueError(str(exc)) from exc


def maintenance_queue_id(report: Mapping[str, Any]) -> str:
    """The identity of a queue report: a hash of everything but ``queue_id``."""
    body = {key: value for key, value in report.items() if key != "queue_id"}
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate(document: object) -> None:
    queue = _fields(document, "queue", QUEUE_FIELDS)
    if queue["schema_version"] != MAINTENANCE_QUEUE_SCHEMA_VERSION:
        raise MaintenanceQueueError(f"schema_version: expected {MAINTENANCE_QUEUE_SCHEMA_VERSION!r}")
    if queue["advisory"] is not True:
        raise MaintenanceQueueError("advisory: the queue is always advisory")
    limit = queue["limit"]
    if not _integer(limit) or not MIN_QUEUE_LIMIT <= limit <= MAX_QUEUE_LIMIT:
        raise MaintenanceQueueError(f"limit: must be between {MIN_QUEUE_LIMIT} and {MAX_QUEUE_LIMIT}")
    for key in ("total", "returned", "omitted"):
        _count(queue[key], key)
    items = _sequence(queue["items"], "items")
    for index, item in enumerate(items):
        _check_item(item, f"items[{index}]")
    _check_counts(queue, items)
    _check_qualification(queue["qualification"])
    _texts(queue["limitations"], "limitations")
    for index, diagnostic in enumerate(_sequence(queue["diagnostics"], "diagnostics")):
        _check_diagnostic(diagnostic, f"diagnostics[{index}]")
    basis = _fields(queue["basis"], "basis", BASIS_FIELDS)
    _hash(basis["source_identity"], "basis.source_identity")
    _hash(basis["wiki_identity"], "basis.wiki_identity")
    _text(basis["knowledge_reason"], "basis.knowledge_reason")
    _flag(basis["source_selection_compatible"], "basis.source_selection_compatible")
    if not basis["source_selection_compatible"] and any(
        item["freshness"]["reason"] != INCOMPATIBLE_SELECTION_REASON for item in items
    ):
        raise MaintenanceQueueError(
            f"items: an incompatible source selection marks every item {INCOMPATIBLE_SELECTION_REASON}"
        )
    _hash(queue["queue_id"], "queue_id")
    if queue["queue_id"] != maintenance_queue_id(queue):
        raise MaintenanceQueueError("queue_id: must hash the rest of the report")


def _check_counts(queue: Mapping[str, Any], items: Sequence[Mapping[str, Any]]) -> None:
    if queue["returned"] != len(items):
        raise MaintenanceQueueError("returned: counts the listed items")
    if queue["total"] != queue["returned"] + queue["omitted"]:
        raise MaintenanceQueueError("total: is returned plus omitted")
    if queue["returned"] != min(queue["limit"], queue["total"]):
        raise MaintenanceQueueError("returned: lists items up to the limit")
    paths = [item["path"] for item in items]
    if len(set(paths)) != len(paths):
        raise MaintenanceQueueError("items: each page appears once")
    ranking = [(-item["score"], item["path"]) for item in items]
    if ranking != sorted(ranking):
        raise MaintenanceQueueError("items: ranked by descending score, then path")


def _check_item(value: object, field: str) -> None:
    item = _fields(value, field, ITEM_FIELDS)
    _text(item["path"], f"{field}.path")
    _text(item["kind"], f"{field}.kind")
    _optional_text(item["source_path"], f"{field}.source_path")
    _choice(item["classification"], f"{field}.classification", CLASSIFICATIONS)
    category = item["observed_change_category"]
    _choice(category, f"{field}.observed_change_category", (*FRESHNESS_STATES, *ORDINARY_CATEGORIES))
    freshness = _fields(item["freshness"], f"{field}.freshness", FRESHNESS_FIELDS)
    _choice(freshness["state"], f"{field}.freshness.state", FRESHNESS_STATES)
    _text(freshness["reason"], f"{field}.freshness.reason")
    _string(freshness["description"], f"{field}.freshness.description")
    _flag(freshness["live_comparison_performed"], f"{field}.freshness.live_comparison_performed")
    ownership = _fields(item["ownership"], f"{field}.ownership", OWNERSHIP_FIELDS)
    _optional_text(ownership["surface_role"], f"{field}.ownership.surface_role")
    _optional_text(ownership["semantic_section"], f"{field}.ownership.semantic_section")
    _text(ownership["instruction"], f"{field}.ownership.instruction")
    _texts(item["placeholder_signals"], f"{field}.placeholder_signals")
    _optional_text(item["work_status"], f"{field}.work_status")
    if item["lint_severity"] is not None:
        _choice(item["lint_severity"], f"{field}.lint_severity", LINT_SEVERITIES)
    if item["reachable_from_index"] is not None:
        _flag(item["reachable_from_index"], f"{field}.reachable_from_index")
    if item["source_fan_in"] is not None:
        _count(item["source_fan_in"], f"{field}.source_fan_in")
    if not _integer(item["score"]):
        raise MaintenanceQueueError(f"{field}.score: must be an integer")
    reasons = _sequence(item["reasons"], f"{field}.reasons")
    for index, reason in enumerate(reasons):
        entry = _fields(reason, f"{field}.reasons[{index}]", REASON_FIELDS)
        _text(entry["code"], f"{field}.reasons[{index}].code")
        _string(entry["message"], f"{field}.reasons[{index}].message")
        if not _integer(entry["weight"]):
            raise MaintenanceQueueError(f"{field}.reasons[{index}].weight: must be an integer")
    _check_coverage_gaps(item, field)
    _check_ordinary_review(item, field)
    _check_item_consistency(item, field, reasons)


def _check_item_consistency(item: Mapping[str, Any], field: str, reasons: Sequence[Any]) -> None:
    if not reasons:
        raise MaintenanceQueueError(f"{field}.reasons: every queued page gives a reason")
    if item["score"] != sum(reason["weight"] for reason in reasons):
        raise MaintenanceQueueError(f"{field}.score: is the sum of its reason weights")
    category, state = item["observed_change_category"], item["freshness"]["state"]
    if category in ORDINARY_CATEGORIES:
        if state != "unknown":
            raise MaintenanceQueueError(f"{field}.freshness.state: an ordinary-review item has unknown freshness")
    elif category != state:
        raise MaintenanceQueueError(f"{field}.observed_change_category: is the freshness state")
    if category == "ordinary-maintenance" and "maintenance" not in item:
        raise MaintenanceQueueError(f"{field}: an ordinary-maintenance item carries its review details")
    if category == "ordinary-coverage-gap" and "coverage_gaps" not in item:
        raise MaintenanceQueueError(f"{field}: an ordinary-coverage-gap item lists its gaps")
    actionable = (
        item["lint_severity"] is not None
        or category in ACTIONABLE_STATES
        or "maintenance" in item
    )
    if actionable and item["classification"] != "actionable":
        raise MaintenanceQueueError(
            f"{field}.classification: lint findings, source changes and ordinary review are actionable"
        )


def _check_coverage_gaps(item: Mapping[str, Any], field: str) -> None:
    if not _together(item, COVERAGE_GAP_FIELDS, field):
        return
    gaps = _sequence(item["coverage_gaps"], f"{field}.coverage_gaps")
    for index, gap in enumerate(gaps):
        name = f"{field}.coverage_gaps[{index}]"
        if not isinstance(gap, Mapping):
            raise MaintenanceQueueError(f"{name}: must be an object")
        _text(gap.get("reason"), f"{name}.reason")
        if "target" in gap:
            check_target(gap["target"], f"{name}.target")
            if gap["target"]["canonical_path"] != item["path"]:
                raise MaintenanceQueueError(f"{name}.target: is a section of this page")
    _bounds(item["coverage_gap_bounds"], f"{field}.coverage_gap_bounds", GAP_BOUNDS_FIELDS, gaps)


def _check_ordinary_review(item: Mapping[str, Any], field: str) -> None:
    if not _together(item, ORDINARY_REVIEW_FIELDS, field):
        return
    summary = check_maintenance_summary(item["maintenance"], f"{field}.maintenance")
    record_ids = _sequence(item["record_ids"], f"{field}.record_ids")
    for index, record_id in enumerate(record_ids):
        _text(record_id, f"{field}.record_ids[{index}]")
    if list(record_ids) != sorted(set(record_ids)):
        raise MaintenanceQueueError(f"{field}.record_ids: must be unique and sorted")
    bounds = _bounds(item["record_bounds"], f"{field}.record_bounds", RECORD_BOUNDS_FIELDS, record_ids)
    limit = bounds["limit"]
    if not _integer(limit) or not MIN_QUEUE_LIMIT <= limit <= MAX_QUEUE_LIMIT or bounds["returned"] > limit:
        raise MaintenanceQueueError(f"{field}.record_bounds.limit: bounds the listed records")
    _budget(bounds, f"{field}.record_bounds")
    if summary["total"] != bounds["total"] or summary["truncated"] is not bounds["truncated"]:
        raise MaintenanceQueueError(f"{field}.maintenance: total and truncated follow the record bounds")
    targets = _sequence(item["semantic_targets"], f"{field}.semantic_targets")
    for index, value in enumerate(targets):
        name = f"{field}.semantic_targets[{index}]"
        target = _fields(value, name, SEMANTIC_TARGET_FIELDS)
        check_coordinate(target["coordinate"], f"{name}.coordinate")
        check_target(target["target"], f"{name}.target")
        _choice(target["attribution"], f"{name}.attribution", TARGET_ATTRIBUTIONS)
        if target["record_id"] not in record_ids:
            raise MaintenanceQueueError(f"{name}.record_id: names a listed record")
        if target["target"]["canonical_path"] != item["path"]:
            raise MaintenanceQueueError(f"{name}.target: is a section of this page")
    target_bounds = _bounds(
        item["semantic_target_bounds"], f"{field}.semantic_target_bounds", TARGET_BOUNDS_FIELDS, targets
    )
    _budget(target_bounds, f"{field}.semantic_target_bounds")


def _check_qualification(value: object) -> None:
    qualification = _fields(value, "qualification", QUALIFICATION_FIELDS)
    custody = _fields(
        qualification["ordinary_review_custody"], "qualification.ordinary_review_custody", CUSTODY_FIELDS
    )
    field = "qualification.ordinary_review_custody"
    _choice(custody["availability"], f"{field}.availability", CUSTODY_AVAILABILITY)
    _flag(custody["durable_owner_available"], f"{field}.durable_owner_available")
    _choice(custody["evidence"], f"{field}.evidence", CUSTODY_EVIDENCE)
    _flag(custody["live_evaluation_performed"], f"{field}.live_evaluation_performed")
    if custody["source_prose_correctness"] != "not-established":
        raise MaintenanceQueueError(f"{field}.source_prose_correctness: the queue never establishes correctness")
    route = _fields(custody["review_route"], f"{field}.review_route", REVIEW_ROUTE_FIELDS)
    _text(route["interface"], f"{field}.review_route.interface")
    _text(route["instruction"], f"{field}.review_route.instruction")
    _text(custody["limitation"], f"{field}.limitation")
    _check_custody(custody, field)
    states = qualification["freshness_states"]
    if not isinstance(states, Mapping):
        raise MaintenanceQueueError("qualification.freshness_states: must be an object")
    for state, count in states.items():
        _choice(state, "qualification.freshness_states", FRESHNESS_STATES)
        _count(count, f"qualification.freshness_states.{state}")
    _count(qualification["authoring_hint_pages"], "qualification.authoring_hint_pages")
    _string(qualification["scope"], "qualification.scope")
    _texts(qualification["limitations"], "qualification.limitations")


def _check_custody(custody: Mapping[str, Any], field: str) -> None:
    availability, evidence = custody["availability"], custody["evidence"]
    if custody["durable_owner_available"] is not (availability in ("ready", "partial")):
        raise MaintenanceQueueError(f"{field}.durable_owner_available: a ready or partial custody has an owner")
    expected = {
        "captured-maintenance-status": ("ready", "partial", "unadopted"),
        "validated-native-manifest": ("partial", "unadopted"),
        "no-validated-native-manifest": ("unavailable",),
    }[evidence]
    if availability not in expected:
        raise MaintenanceQueueError(f"{field}.availability: {evidence} gives {', '.join(expected)}")
    if evidence != "captured-maintenance-status" and custody["live_evaluation_performed"]:
        raise MaintenanceQueueError(f"{field}.live_evaluation_performed: only captured status is evaluated")


def _check_diagnostic(value: object, field: str) -> None:
    diagnostic = _fields(value, field, DIAGNOSTIC_FIELDS)
    _text(diagnostic["category"], f"{field}.category")
    _text(diagnostic["severity"], f"{field}.severity")
    _string(diagnostic["message"], f"{field}.message")
    if "path" in diagnostic:
        _optional_text(diagnostic["path"], f"{field}.path")


def _together(item: Mapping[str, Any], fields: Sequence[str], field: str) -> bool:
    present = [key for key in fields if key in item]
    if present and len(present) != len(fields):
        raise MaintenanceQueueError(f"{field}: {', '.join(fields)} appear together")
    return bool(present)


def _bounds(value: object, field: str, fields: Sequence[str], items: Sequence[Any]) -> Mapping[str, Any]:
    bounds = _fields(value, field, fields)
    for key in ("total", "returned", "omitted"):
        _count(bounds[key], f"{field}.{key}")
    _flag(bounds["truncated"], f"{field}.truncated")
    if bounds["returned"] != len(items) or len(items) > QUEUE_MAX_DETAILS:
        raise MaintenanceQueueError(f"{field}.returned: counts the listed entries, at most {QUEUE_MAX_DETAILS}")
    if bounds["omitted"] != bounds["total"] - bounds["returned"]:
        raise MaintenanceQueueError(f"{field}.omitted: is total minus returned")
    if bounds["truncated"] is not (bounds["omitted"] > 0):
        raise MaintenanceQueueError(f"{field}.truncated: true exactly when entries are omitted")
    return bounds


def _budget(bounds: Mapping[str, Any], field: str) -> None:
    if bounds["max_records"] != QUEUE_MAX_DETAILS or bounds["max_bytes"] != QUEUE_MAX_BYTES:
        raise MaintenanceQueueError(f"{field}: max_records and max_bytes are the detail budget")


def _fields(value: object, field: str, required: Sequence[str]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MaintenanceQueueError(f"{field}: must be an object")
    missing = [key for key in required if key not in value]
    if missing:
        raise MaintenanceQueueError(f"{field}: missing {missing}")
    return value


def _sequence(value: object, field: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise MaintenanceQueueError(f"{field}: must be an array")
    return value


def _choice(value: object, field: str, choices: Sequence[str]) -> None:
    if not isinstance(value, str) or value not in choices:
        raise MaintenanceQueueError(f"{field}: must be one of {', '.join(choices)}")


def _string(value: object, field: str) -> None:
    if not isinstance(value, str):
        raise MaintenanceQueueError(f"{field}: must be a string")


def _text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise MaintenanceQueueError(f"{field}: must be a non-empty string")


def _optional_text(value: object, field: str) -> None:
    if value is not None:
        _text(value, field)


def _texts(value: object, field: str) -> None:
    for index, item in enumerate(_sequence(value, field)):
        _text(item, f"{field}[{index}]")


def _hash(value: object, field: str) -> None:
    if not isinstance(value, str) or not _HASH.match(value):
        raise MaintenanceQueueError(f"{field}: must be a sha256 digest")


def _flag(value: object, field: str) -> None:
    if not isinstance(value, bool):
        raise MaintenanceQueueError(f"{field}: must be a boolean")


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _count(value: object, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise MaintenanceQueueError(f"{field}: must be a non-negative integer")
