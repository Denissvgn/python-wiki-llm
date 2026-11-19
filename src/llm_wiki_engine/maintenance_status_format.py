"""Published maintenance status format: ``llm-wiki-maintenance-status/v1``.

A status payload is one bounded read of ordinary review: the recorded review
state of each maintenance record and, when source was captured, its current
effective state. The format is closed. The checks here are the ones a JSON
Schema cannot express: availability and evaluation agree with the analysis
scope, every bound counts what it bounds, records are ordered and unique, each
record's qualification follows from what was evaluated, and an embedded
per-path summary agrees with the records it summarizes.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .canonical_json import compact_line_bytes

MAINTENANCE_STATUS_SCHEMA_VERSION = "llm-wiki-maintenance-status/v1"
STATUS_MAX_BYTES = 65536
STATUS_MAX_RECORDS = 128
STATUS_HISTORY_LIMIT = 5
STATUS_LIMITATIONS = (
    "ordinary-acknowledgment-is-not-human-governance-review",
    "captured-syntax-is-not-runtime-equivalence",
    "captured-prose-is-not-a-correctness-verdict",
    "snapshot-status-does-not-establish-current-acknowledgment",
)
ANALYSIS_SCOPES = ("full-inventory", "selected-header", "selected-source", "snapshot")
SNAPSHOT_SCOPES = ("selected-header", "snapshot")
AVAILABILITY = ("ready", "partial", "unadopted")
SUMMARY_AVAILABILITY = (*AVAILABILITY, "unavailable")
RECORD_STATUSES = ("pending", "acknowledged")
MAPPING_STATES = ("resolved", "deleted", "ambiguous")
BASIS_SCOPES = ("module", "class", "callable")
RECORD_QUALIFICATIONS = ("snapshot", "current-capture", "current-basis-unavailable")
SOURCE_LOCATION_QUALIFICATIONS = ("captured", "not-observed")
ACTOR_KINDS = ("agent", "human")
ACTOR_AUTHORITY = "ordinary-maintenance"

STATUS_FIELDS = (
    "schema_version",
    "availability",
    "adoption_id",
    "state_hash",
    "analysis_scope",
    "live_evaluation_performed",
    "native_prose_coherent",
    "requires_sync",
    "coverage",
    "bounds",
    "records",
    "limitations",
)
STATUS_OPTIONAL_FIELDS = ("summary",)
COVERAGE_FIELDS = (
    "source_backed_semantic_total",
    "tracked_semantic_total",
    "untracked_semantic_total",
    "issues",
    "untracked_targets",
    "issue_bounds",
    "untracked_target_bounds",
)
BOUNDS_FIELDS = ("total", "returned", "omitted", "truncated", "limit", "max_records", "max_bytes")
LIST_BOUNDS_FIELDS = ("total", "returned", "truncated")
HISTORY_BOUNDS_FIELDS = ("total", "returned", "omitted", "truncated")
RECORD_FIELDS = (
    "record_id",
    "coordinate",
    "target",
    "mapping",
    "recorded_status",
    "effective_status",
    "reasons",
    "recorded_basis",
    "expected_basis",
    "basis_available",
    "acknowledgment",
    "acknowledgment_history",
    "history_bounds",
    "source_location",
    "qualification",
    "governance_effect",
)
COORDINATE_FIELDS = ("source_path", "qualified_owner", "occurrence")
TARGET_FIELDS = ("canonical_path", "section_locator", "ownership")
MAPPING_FIELDS = ("state", "previous_coordinate", "candidates", "previous_target")
BASIS_FIELDS = (
    "coordinate",
    "source_hash",
    "executable_hash",
    "documentation_hash",
    "prose_hash",
    "comparison_id",
    "producer_hash",
    "target",
    "scope",
)
BASIS_OPTIONAL_HASHES = ("source_hash", "executable_hash", "documentation_hash", "prose_hash")
ACKNOWLEDGMENT_FIELDS = (
    "acknowledgment_id",
    "record_id",
    "basis",
    "basis_hash",
    "actor",
    "governance_effect",
)
ACTOR_FIELDS = ("kind", "actor_id", "authority")
SOURCE_LOCATION_FIELDS = ("source_path", "line", "qualification")
ISSUE_OPTIONAL_FIELDS = ("canonical_path", "coordinate", "scope", "record_id")
SUMMARY_FIELDS = (
    "availability",
    "analysis_scope",
    "live_evaluation_performed",
    "native_prose_coherent",
    "requires_sync",
    "total",
    "pending",
    "acknowledged",
    "unavailable",
    "ambiguous",
    "deleted",
    "untracked",
    "truncated",
    "limitations",
)
SUMMARY_COUNTS = ("total", "pending", "acknowledged", "unavailable", "ambiguous", "deleted", "untracked")
SUMMARY_FLAGS = ("live_evaluation_performed", "native_prose_coherent", "requires_sync", "truncated")
MAX_TEXT = 4096
MAX_ID = 128
MAX_OCCURRENCE = 1_000_000
MAX_CANDIDATES = 8
MAX_REASONS = 16
MAX_LIMIT = 1000
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RECORD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")


class MaintenanceStatusError(ValueError):
    """A maintenance status payload does not satisfy its published format."""


def validate_maintenance_status(document: object) -> None:
    """Raise ``MaintenanceStatusError`` unless ``document`` is a valid status payload."""
    status = _fields(document, "status", STATUS_FIELDS, STATUS_OPTIONAL_FIELDS)
    if status["schema_version"] != MAINTENANCE_STATUS_SCHEMA_VERSION:
        raise MaintenanceStatusError(
            f"schema_version: expected {MAINTENANCE_STATUS_SCHEMA_VERSION!r}"
        )
    _check_qualification(status)
    _check_coverage(status["coverage"])
    records = _sequence(status["records"], "records")
    _check_bounds(status["bounds"], records)
    for index, record in enumerate(records):
        _check_record(record, f"records[{index}]", status["live_evaluation_performed"])
    ids = [record["record_id"] for record in records]
    if ids != sorted(set(ids)):
        raise MaintenanceStatusError("records: must be unique and ordered by record_id")
    if status["availability"] == "unadopted" and records:
        raise MaintenanceStatusError("records: an unadopted wiki has no maintenance records")
    if "summary" in status:
        _check_summary(status["summary"], status)
    if len(compact_line_bytes(status)) > STATUS_MAX_BYTES:
        raise MaintenanceStatusError(f"status: exceeds {STATUS_MAX_BYTES} canonical bytes")


def _check_qualification(status: Mapping[str, Any]) -> None:
    _choice(status["availability"], "availability", AVAILABILITY)
    _choice(status["analysis_scope"], "analysis_scope", ANALYSIS_SCOPES)
    for key in ("live_evaluation_performed", "native_prose_coherent", "requires_sync"):
        _flag(status[key], key)
    if status["limitations"] != list(STATUS_LIMITATIONS):
        raise MaintenanceStatusError("limitations: must list the status limitations in order")
    if status["requires_sync"] is status["native_prose_coherent"]:
        raise MaintenanceStatusError("requires_sync: must be true exactly when native prose is incoherent")
    if status["analysis_scope"] in SNAPSHOT_SCOPES and status["live_evaluation_performed"]:
        raise MaintenanceStatusError("live_evaluation_performed: a snapshot read evaluates nothing")
    adopted = status["availability"] != "unadopted"
    if adopted:
        _identifier(status["adoption_id"], "adoption_id")
        _hash(status["state_hash"], "state_hash")
        expected = "partial" if status["analysis_scope"] == "selected-header" else "ready"
        if status["availability"] != expected:
            raise MaintenanceStatusError(f"availability: an adopted {status['analysis_scope']} read is {expected}")
    elif status["adoption_id"] is not None or status["state_hash"] is not None:
        raise MaintenanceStatusError("adoption_id: an unadopted wiki has no adoption or state hash")


def _check_coverage(value: object) -> None:
    coverage = _fields(value, "coverage", COVERAGE_FIELDS)
    for key in COVERAGE_FIELDS[:3]:
        _count(coverage[key], f"coverage.{key}")
    issues = _sequence(coverage["issues"], "coverage.issues")
    targets = _sequence(coverage["untracked_targets"], "coverage.untracked_targets")
    for index, issue in enumerate(issues):
        _issue(issue, f"coverage.issues[{index}]")
    for index, target in enumerate(targets):
        _target(target, f"coverage.untracked_targets[{index}]")
    _list_bounds(coverage["issue_bounds"], "coverage.issue_bounds", issues)
    _list_bounds(coverage["untracked_target_bounds"], "coverage.untracked_target_bounds", targets)
    if coverage["untracked_target_bounds"]["total"] < coverage["untracked_semantic_total"]:
        raise MaintenanceStatusError(
            "coverage.untracked_target_bounds.total: counts every untracked semantic target"
        )


def _list_bounds(value: object, field: str, items: Sequence[Any]) -> None:
    bounds = _fields(value, field, LIST_BOUNDS_FIELDS)
    _count(bounds["total"], f"{field}.total")
    _count(bounds["returned"], f"{field}.returned")
    _flag(bounds["truncated"], f"{field}.truncated")
    if bounds["returned"] != len(items) or len(items) > STATUS_MAX_RECORDS:
        raise MaintenanceStatusError(f"{field}.returned: counts the listed items, at most {STATUS_MAX_RECORDS}")
    if bounds["returned"] > bounds["total"] or bounds["truncated"] is not (bounds["returned"] < bounds["total"]):
        raise MaintenanceStatusError(f"{field}: truncated exactly when fewer than total are listed")


def _check_bounds(value: object, records: Sequence[Any]) -> None:
    bounds = _fields(value, "bounds", BOUNDS_FIELDS)
    for key in ("total", "returned", "omitted"):
        _count(bounds[key], f"bounds.{key}")
    _flag(bounds["truncated"], "bounds.truncated")
    if not _integer(bounds["limit"]) or not 1 <= bounds["limit"] <= MAX_LIMIT:
        raise MaintenanceStatusError(f"bounds.limit: must be between 1 and {MAX_LIMIT}")
    if bounds["max_records"] != STATUS_MAX_RECORDS or bounds["max_bytes"] != STATUS_MAX_BYTES:
        raise MaintenanceStatusError("bounds: max_records and max_bytes are the status budget")
    if bounds["returned"] != len(records):
        raise MaintenanceStatusError("bounds.returned: counts the listed records")
    if bounds["returned"] > min(bounds["limit"], STATUS_MAX_RECORDS):
        raise MaintenanceStatusError("bounds.returned: stays within the limit")
    if bounds["omitted"] != bounds["total"] - bounds["returned"]:
        raise MaintenanceStatusError("bounds.omitted: is total minus returned")
    if bounds["truncated"] is not (bounds["omitted"] > 0):
        raise MaintenanceStatusError("bounds.truncated: true exactly when records are omitted")


def _check_record(value: object, field: str, live: bool) -> None:
    record = _fields(value, field, RECORD_FIELDS)
    record_id = record["record_id"]
    _record_id(record_id, f"{field}.record_id")
    _coordinate(record["coordinate"], f"{field}.coordinate")
    _target(record["target"], f"{field}.target")
    _mapping(record["mapping"], f"{field}.mapping")
    _choice(record["recorded_status"], f"{field}.recorded_status", RECORD_STATUSES)
    if record["effective_status"] is not None:
        _choice(record["effective_status"], f"{field}.effective_status", RECORD_STATUSES)
    _reasons(record["reasons"], f"{field}.reasons")
    _basis(record["recorded_basis"], f"{field}.recorded_basis")
    if record["expected_basis"] is not None:
        _basis(record["expected_basis"], f"{field}.expected_basis")
    _flag(record["basis_available"], f"{field}.basis_available")
    if record["acknowledgment"] is not None:
        _acknowledgment(record["acknowledgment"], f"{field}.acknowledgment", record_id)
    history = _sequence(record["acknowledgment_history"], f"{field}.acknowledgment_history")
    for index, item in enumerate(history):
        _acknowledgment(item, f"{field}.acknowledgment_history[{index}]", record_id)
    _history_bounds(record["history_bounds"], f"{field}.history_bounds", history)
    _source_location(record["source_location"], f"{field}.source_location", record["coordinate"])
    _choice(record["qualification"], f"{field}.qualification", RECORD_QUALIFICATIONS)
    if record["governance_effect"] != "none":
        raise MaintenanceStatusError(f"{field}.governance_effect: ordinary review has no governance effect")
    _check_record_consistency(record, field, live)


def _check_record_consistency(record: Mapping[str, Any], field: str, live: bool) -> None:
    for key in ("recorded_basis", "expected_basis"):
        basis = record[key]
        if basis is not None and (
            basis["coordinate"] != record["coordinate"] or basis["target"] != record["target"]
        ):
            raise MaintenanceStatusError(f"{field}.{key}: describes the record's coordinate and target")
    if record["basis_available"] is not (record["expected_basis"] is not None):
        raise MaintenanceStatusError(f"{field}.basis_available: true exactly when an expected basis is given")
    if (record["recorded_status"] == "acknowledged") is not (record["acknowledgment"] is not None):
        raise MaintenanceStatusError(f"{field}.acknowledgment: present exactly when the record is acknowledged")
    if not live:
        if record["effective_status"] is not None or record["expected_basis"] is not None:
            raise MaintenanceStatusError(f"{field}: a snapshot read evaluates no current status")
        expected = "snapshot"
    else:
        if record["effective_status"] is None:
            raise MaintenanceStatusError(f"{field}.effective_status: a live read evaluates every record")
        expected = "current-capture" if record["basis_available"] else "current-basis-unavailable"
        if record["effective_status"] == "acknowledged" and (
            record["recorded_status"] != "acknowledged" or not record["basis_available"]
        ):
            raise MaintenanceStatusError(
                f"{field}.effective_status: stays acknowledged only for an unchanged acknowledged record"
            )
    if record["qualification"] != expected:
        raise MaintenanceStatusError(f"{field}.qualification: must be {expected!r}")


def _history_bounds(value: object, field: str, history: Sequence[Any]) -> None:
    bounds = _fields(value, field, HISTORY_BOUNDS_FIELDS)
    for key in ("total", "returned", "omitted"):
        _count(bounds[key], f"{field}.{key}")
    _flag(bounds["truncated"], f"{field}.truncated")
    if bounds["returned"] != len(history) or len(history) > STATUS_HISTORY_LIMIT:
        raise MaintenanceStatusError(
            f"{field}.returned: counts the listed history, at most {STATUS_HISTORY_LIMIT}"
        )
    if bounds["omitted"] != bounds["total"] - bounds["returned"] or bounds["truncated"] is not (
        bounds["omitted"] > 0
    ):
        raise MaintenanceStatusError(f"{field}: omitted is total minus returned and sets truncated")


def _source_location(value: object, field: str, coordinate: Mapping[str, Any]) -> None:
    location = _fields(value, field, SOURCE_LOCATION_FIELDS)
    if location["source_path"] != coordinate["source_path"]:
        raise MaintenanceStatusError(f"{field}.source_path: is the record's source path")
    line = location["line"]
    if line is not None and (not _integer(line) or line < 1):
        raise MaintenanceStatusError(f"{field}.line: must be a positive line number or null")
    _choice(location["qualification"], f"{field}.qualification", SOURCE_LOCATION_QUALIFICATIONS)
    if (location["qualification"] == "captured") is not (line is not None):
        raise MaintenanceStatusError(f"{field}.qualification: captured exactly when a line is known")


def check_maintenance_summary(value: object, field: str = "summary") -> Mapping[str, Any]:
    """Check a compact maintenance summary on its own and return it."""
    summary = _fields(value, field, SUMMARY_FIELDS)
    _choice(summary["availability"], f"{field}.availability", SUMMARY_AVAILABILITY)
    _choice(summary["analysis_scope"], f"{field}.analysis_scope", ANALYSIS_SCOPES)
    for key in SUMMARY_FLAGS:
        _flag(summary[key], f"{field}.{key}")
    for key in SUMMARY_COUNTS:
        _count(summary[key], f"{field}.{key}")
    if summary["limitations"] != list(STATUS_LIMITATIONS):
        raise MaintenanceStatusError(f"{field}.limitations: must list the status limitations in order")
    if summary["requires_sync"] is summary["native_prose_coherent"]:
        raise MaintenanceStatusError(f"{field}.requires_sync: must negate native_prose_coherent")
    if summary["analysis_scope"] in SNAPSHOT_SCOPES and summary["live_evaluation_performed"]:
        raise MaintenanceStatusError(f"{field}.live_evaluation_performed: a snapshot read evaluates nothing")
    if summary["pending"] + summary["acknowledged"] > summary["total"] or any(
        summary[key] > summary["total"] for key in SUMMARY_COUNTS[1:6]
    ):
        raise MaintenanceStatusError(f"{field}: subgroup counts stay within the total")
    if not summary["live_evaluation_performed"] and summary["acknowledged"]:
        raise MaintenanceStatusError(f"{field}.acknowledged: a snapshot establishes no current acknowledgment")
    return summary


def _check_summary(value: object, status: Mapping[str, Any]) -> None:
    summary = check_maintenance_summary(value)
    for key in ("availability", "analysis_scope", "live_evaluation_performed",
                "native_prose_coherent", "requires_sync", "limitations"):
        if summary[key] != status[key]:
            raise MaintenanceStatusError(f"summary.{key}: must match the status payload")
    bounds = status["bounds"]
    if summary["total"] != bounds["total"] or summary["truncated"] is not bounds["truncated"]:
        raise MaintenanceStatusError("summary: total and truncated follow the record bounds")
    if not bounds["truncated"]:
        counts = _summary_counts(status["records"])
        for key, count in counts.items():
            if summary[key] != count:
                raise MaintenanceStatusError(f"summary.{key}: must count the listed records")


def _summary_counts(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    def effective(row):
        return row["effective_status"] or row["recorded_status"]

    return {
        "pending": sum(effective(row) == "pending" for row in records),
        "acknowledged": sum(row["effective_status"] == "acknowledged" for row in records),
        "unavailable": sum(
            row["effective_status"] is None or not row["basis_available"] for row in records
        ),
        "ambiguous": sum(row["mapping"]["state"] == "ambiguous" for row in records),
        "deleted": sum(
            row["mapping"]["state"] == "deleted"
            or "source-deleted" in row["reasons"]
            or "target-deleted" in row["reasons"]
            for row in records
        ),
    }


def _issue(value: object, field: str) -> None:
    if not isinstance(value, Mapping):
        raise MaintenanceStatusError(f"{field}: must be an object")
    unknown = set(value) - {"reason", *ISSUE_OPTIONAL_FIELDS}
    if unknown or "reason" not in value:
        raise MaintenanceStatusError(f"{field}: has a reason and only {', '.join(ISSUE_OPTIONAL_FIELDS)}")
    _text(value["reason"], f"{field}.reason", MAX_ID)
    if "canonical_path" in value:
        _text(value["canonical_path"], f"{field}.canonical_path", MAX_TEXT)
    if "coordinate" in value:
        _coordinate(value["coordinate"], f"{field}.coordinate")
    if "scope" in value and value["scope"] is not None:
        _choice(value["scope"], f"{field}.scope", BASIS_SCOPES)
    if "record_id" in value:
        _record_id(value["record_id"], f"{field}.record_id")


def check_coordinate(value: object, field: str = "coordinate") -> None:
    """Check a maintenance source coordinate."""
    _coordinate(value, field)


def check_target(value: object, field: str = "target") -> None:
    """Check a maintenance semantic target."""
    _target(value, field)


def _coordinate(value: object, field: str) -> None:
    coordinate = _fields(value, field, COORDINATE_FIELDS)
    _text(coordinate["source_path"], f"{field}.source_path", MAX_TEXT)
    _text(coordinate["qualified_owner"], f"{field}.qualified_owner", MAX_TEXT)
    occurrence = coordinate["occurrence"]
    if not _integer(occurrence) or not 1 <= occurrence <= MAX_OCCURRENCE:
        raise MaintenanceStatusError(f"{field}.occurrence: must be between 1 and {MAX_OCCURRENCE}")


def _target(value: object, field: str) -> None:
    target = _fields(value, field, TARGET_FIELDS)
    _text(target["canonical_path"], f"{field}.canonical_path", MAX_TEXT)
    _text(target["section_locator"], f"{field}.section_locator", MAX_TEXT)
    if target["ownership"] != "semantic":
        raise MaintenanceStatusError(f"{field}.ownership: must be 'semantic'")


def _mapping(value: object, field: str) -> None:
    mapping = _fields(value, field, MAPPING_FIELDS)
    _choice(mapping["state"], f"{field}.state", MAPPING_STATES)
    if mapping["previous_coordinate"] is not None:
        _coordinate(mapping["previous_coordinate"], f"{field}.previous_coordinate")
    if mapping["previous_target"] is not None:
        _target(mapping["previous_target"], f"{field}.previous_target")
    candidates = _sequence(mapping["candidates"], f"{field}.candidates")
    if len(candidates) > MAX_CANDIDATES:
        raise MaintenanceStatusError(f"{field}.candidates: at most {MAX_CANDIDATES}")
    for index, candidate in enumerate(candidates):
        entry = _fields(candidate, f"{field}.candidates[{index}]", ("coordinate", "target"))
        _coordinate(entry["coordinate"], f"{field}.candidates[{index}].coordinate")
        _target(entry["target"], f"{field}.candidates[{index}].target")
    if any(candidates[index] in candidates[:index] for index in range(len(candidates))):
        raise MaintenanceStatusError(f"{field}.candidates: must be unique")


def _basis(value: object, field: str) -> None:
    basis = _fields(value, field, BASIS_FIELDS)
    _coordinate(basis["coordinate"], f"{field}.coordinate")
    _target(basis["target"], f"{field}.target")
    for key in BASIS_OPTIONAL_HASHES:
        if basis[key] is not None:
            _hash(basis[key], f"{field}.{key}")
    _hash(basis["comparison_id"], f"{field}.comparison_id")
    _hash(basis["producer_hash"], f"{field}.producer_hash")
    _choice(basis["scope"], f"{field}.scope", BASIS_SCOPES)


def _acknowledgment(value: object, field: str, record_id: str) -> None:
    item = _fields(value, field, ACKNOWLEDGMENT_FIELDS)
    _hash(item["acknowledgment_id"], f"{field}.acknowledgment_id")
    if item["record_id"] != record_id:
        raise MaintenanceStatusError(f"{field}.record_id: acknowledges this record")
    _basis(item["basis"], f"{field}.basis")
    _hash(item["basis_hash"], f"{field}.basis_hash")
    actor = _fields(item["actor"], f"{field}.actor", ACTOR_FIELDS)
    _choice(actor["kind"], f"{field}.actor.kind", ACTOR_KINDS)
    _text(actor["actor_id"], f"{field}.actor.actor_id", 256)
    if actor["authority"] != ACTOR_AUTHORITY or item["governance_effect"] != "none":
        raise MaintenanceStatusError(f"{field}: ordinary acknowledgment has no governance authority")


def _reasons(value: object, field: str) -> None:
    reasons = _sequence(value, field)
    for index, reason in enumerate(reasons):
        _text(reason, f"{field}[{index}]", MAX_ID)
    if list(reasons) != sorted(set(reasons)):
        raise MaintenanceStatusError(f"{field}: must be unique and sorted")


def _fields(
    value: object, field: str, required: Sequence[str], optional: Sequence[str] = ()
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MaintenanceStatusError(f"{field}: must be an object")
    missing = [key for key in required if key not in value]
    unknown = sorted(set(value) - set(required) - set(optional))
    if missing or unknown:
        raise MaintenanceStatusError(f"{field}: missing {missing}, unknown {unknown}")
    return value


def _sequence(value: object, field: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise MaintenanceStatusError(f"{field}: must be an array")
    return value


def _choice(value: object, field: str, choices: Sequence[str]) -> None:
    if not isinstance(value, str) or value not in choices:
        raise MaintenanceStatusError(f"{field}: must be one of {', '.join(choices)}")


def _text(value: object, field: str, limit: int) -> None:
    if not isinstance(value, str) or not 1 <= len(value) <= limit:
        raise MaintenanceStatusError(f"{field}: must be a string of 1 to {limit} characters")


def _identifier(value: object, field: str) -> None:
    _text(value, field, MAX_ID)


def _record_id(value: object, field: str) -> None:
    if not isinstance(value, str) or not _RECORD_ID.match(value):
        raise MaintenanceStatusError(f"{field}: must be a record identifier")


def _hash(value: object, field: str) -> None:
    if not isinstance(value, str) or not _HASH.match(value):
        raise MaintenanceStatusError(f"{field}: must be a sha256 digest")


def _flag(value: object, field: str) -> None:
    if not isinstance(value, bool):
        raise MaintenanceStatusError(f"{field}: must be a boolean")


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _count(value: object, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise MaintenanceStatusError(f"{field}: must be a non-negative integer")
