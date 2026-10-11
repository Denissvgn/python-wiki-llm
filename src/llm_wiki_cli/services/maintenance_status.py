"""Immutable read-only ordinary maintenance reports from one captured basis."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any

from .immutable import freeze
from .implementation_evidence import compare_implementation_observations
from .knowledge_storage import canonical_bytes
from .maintenance_evidence import MaintenanceCapture, owner_key
from .maintenance_state import (
    canonical_hash,
    validate_maintenance_adoption,
    validate_maintenance_state,
)

SCHEMA = "llm-wiki-maintenance-status/v1"
MAX_BYTES = 65536
MAX_RECORDS = 128
HISTORY_LIMIT = 5
LIMITATIONS = (
    "ordinary-acknowledgment-is-not-human-governance-review",
    "captured-syntax-is-not-runtime-equivalence",
    "captured-prose-is-not-a-correctness-verdict",
    "snapshot-status-does-not-establish-current-acknowledgment",
)
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
ANALYSIS_SCOPES = frozenset(
    {"snapshot", "selected-source", "full-inventory", "selected-header"}
)
SUMMARY_FIELDS = frozenset(
    {
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
    }
)


def _limit(value):
    if type(value) is not int or not 1 <= value <= 1000:
        raise ValueError("Maintenance status limit must be between 1 and 1000")
    return value


def _history(row, count):
    history = row["acknowledgment_history"]
    row["acknowledgment_history"] = history[-count:] if count else []
    row["history_bounds"] = {
        "total": len(history),
        "returned": min(count, len(history)),
        "omitted": max(0, len(history) - count),
        "truncated": len(history) > count,
    }


def _trim_coverage(result):
    """Auxiliary details yield to existing record and basis observations."""
    coverage = result["coverage"]
    while len(canonical_bytes(result)) > MAX_BYTES and (
        coverage.get("issues") or coverage.get("untracked_targets")
    ):
        key = "issues" if coverage.get("issues") else "untracked_targets"
        coverage[key].pop()
        bound = coverage[
            "issue_bounds" if key == "issues" else "untracked_target_bounds"
        ]
        bound.update(returned=len(coverage[key]), truncated=True)


@dataclass(frozen=True)
class MaintenanceStatusReport:
    payload: Mapping[str, Any]
    by_record: Mapping[str, Mapping[str, Any]]
    by_path: Mapping[str, tuple[str, ...]]

    def __post_init__(self):
        for name in ("payload", "by_record", "by_path"):
            object.__setattr__(self, name, freeze(dict(getattr(self, name))))

    def to_payload(self, *, record_id=None, limit=30) -> dict:
        limit = _limit(limit)
        if record_id is not None and (
            not isinstance(record_id, str) or record_id not in self.by_record
        ):
            raise ValueError("Maintenance record was not found in captured authority")
        result = deepcopy(dict(self.payload))
        available = (
            [self.by_record[record_id]]
            if record_id
            else [self.by_record[key] for key in sorted(self.by_record)]
        )
        selected = []
        result["records"] = selected
        coverage = result["coverage"]
        all_issues = len(coverage.get("issues", []))
        coverage["issues"] = coverage.get("issues", [])[:MAX_RECORDS]
        coverage["untracked_targets"] = coverage.get("untracked_targets", [])[
            :MAX_RECORDS
        ]
        coverage["issue_bounds"] = {
            "total": all_issues,
            "returned": len(coverage.get("issues", [])),
            "truncated": all_issues > len(coverage.get("issues", [])),
        }
        coverage["untracked_target_bounds"] = {
            "total": max(
                coverage.get("untracked_semantic_total", 0),
                len(coverage.get("untracked_targets", [])),
            ),
            "returned": len(coverage.get("untracked_targets", [])),
            "truncated": len(coverage.get("untracked_targets", []))
            < coverage.get("untracked_semantic_total", 0),
        }
        while len(canonical_bytes(result)) > MAX_BYTES and (
            coverage.get("issues") or coverage.get("untracked_targets")
        ):
            key = "issues" if coverage.get("issues") else "untracked_targets"
            coverage[key].pop()
            bound = coverage[
                "issue_bounds" if key == "issues" else "untracked_target_bounds"
            ]
            bound.update(returned=len(coverage[key]), truncated=True)
        result["bounds"] = {
            "total": len(available),
            "returned": 0,
            "omitted": len(available),
            "truncated": bool(available),
            "limit": limit,
            "max_records": MAX_RECORDS,
            "max_bytes": MAX_BYTES,
        }
        while len(canonical_bytes(result)) > MAX_BYTES and (
            coverage.get("issues") or coverage.get("untracked_targets")
        ):
            key = "issues" if coverage.get("issues") else "untracked_targets"
            coverage[key].pop()
            coverage[
                "issue_bounds" if key == "issues" else "untracked_target_bounds"
            ].update(returned=len(coverage[key]), truncated=True)
        if record_id:
            for key, bound_key in (
                ("issues", "issue_bounds"),
                ("untracked_targets", "untracked_target_bounds"),
            ):
                coverage[key] = []
                coverage[bound_key].update(
                    returned=0, truncated=coverage[bound_key]["total"] > 0
                )
        for value in available[: min(limit, MAX_RECORDS)]:
            full = deepcopy(dict(value))
            candidate = deepcopy(full)
            _history(candidate, HISTORY_LIMIT)
            selected.append(candidate)
            _trim_coverage(result)
            while (
                len(canonical_bytes(result)) > MAX_BYTES
                and candidate["acknowledgment_history"]
            ):
                _history(candidate, len(candidate["acknowledgment_history"]) - 1)
                # _history's denominator is the complete retained authority.
                candidate["history_bounds"]["total"] = len(
                    full["acknowledgment_history"]
                )
                candidate["history_bounds"]["omitted"] = len(
                    full["acknowledgment_history"]
                ) - len(candidate["acknowledgment_history"])
                candidate["history_bounds"]["truncated"] = True
            if len(canonical_bytes(result)) > MAX_BYTES:
                selected.pop()
                if record_id:
                    raise ValueError(
                        "Selected maintenance record exceeds the status byte budget"
                    )
                break
        result["bounds"].update(
            returned=len(selected),
            omitted=len(available) - len(selected),
            truncated=len(selected) < len(available),
        )
        _trim_coverage(result)
        while len(canonical_bytes(result)) > MAX_BYTES and selected:
            if record_id:
                raise ValueError(
                    "Selected maintenance record exceeds the final status byte budget"
                )
            selected.pop()
            result["bounds"].update(
                returned=len(selected),
                omitted=len(available) - len(selected),
                truncated=True,
            )
        if len(canonical_bytes(result)) > MAX_BYTES:
            raise ValueError("Maintenance status metadata exceeds its byte budget")
        return result

    def for_path(self, path) -> dict:
        ids = self.by_path.get(path, ())
        payload = deepcopy(dict(self.payload))
        coverage = payload["coverage"]
        coverage["issues"] = [
            value
            for value in coverage.get("issues", ())
            if value.get("canonical_path") == path
        ]
        coverage["untracked_targets"] = [
            value
            for value in coverage.get("untracked_targets", ())
            if value["canonical_path"] == path
        ]
        coverage["untracked_semantic_total"] = len(coverage["untracked_targets"])
        scoped = MaintenanceStatusReport(
            payload, {key: self.by_record[key] for key in ids}, {path: tuple(ids)}
        )
        result = scoped.to_payload(limit=MAX_RECORDS)
        result["summary"] = _summary(
            self.payload,
            [self.by_record[key] for key in ids],
            truncated=result["bounds"]["truncated"],
            untracked=sum(
                target["canonical_path"] == path
                for target in self.payload["coverage"].get("untracked_targets", ())
            ),
        )
        _trim_coverage(result)
        while len(canonical_bytes(result)) > MAX_BYTES and result["records"]:
            result["records"].pop()
            result["bounds"].update(
                returned=len(result["records"]),
                omitted=len(ids) - len(result["records"]),
                truncated=True,
            )
            result["summary"]["truncated"] = True
        if len(canonical_bytes(result)) > MAX_BYTES:
            raise ValueError("Maintenance per-path metadata exceeds its byte budget")
        return result


def _source_location(coordinate, scope, envelope):
    rows = (
        envelope.get("files", {})
        .get(coordinate["source_path"], {})
        .get("observations", ())
        if isinstance(envelope, Mapping)
        else ()
    )
    matches = [
        row
        for row in rows
        if row.get("evidence", {}).get("coordinate") == coordinate
        and row["evidence"].get("scope") == scope
    ]
    line = matches[0].get("line") if len(matches) == 1 else None
    return {
        "source_path": coordinate["source_path"],
        "line": line if type(line) is int and line >= 1 else None,
        "qualification": "captured" if line is not None else "not-observed",
    }


def build_maintenance_status(
    state,
    marker,
    capture: MaintenanceCapture | None = None,
    *,
    implementation_observations=None,
    analysis_scope="snapshot",
    native_prose_coherent=True,
    coverage=None,
    analysis_compatibility_hash=None,
) -> MaintenanceStatusReport:
    """Project existing records only; no transition, allocation or storage writes."""
    scope = "selected-source" if analysis_scope == "selected" else analysis_scope
    if scope not in ANALYSIS_SCOPES or type(native_prose_coherent) is not bool:
        raise ValueError("Invalid maintenance read qualification")
    if capture is not None and not isinstance(capture, MaintenanceCapture):
        raise TypeError("Maintenance capture must come from the captured join")
    live = capture is not None and scope not in {"snapshot", "selected-header"}
    base = {
        "schema_version": SCHEMA,
        "availability": "unadopted"
        if state is None
        else "partial"
        if scope == "selected-header"
        else "ready",
        "adoption_id": None,
        "state_hash": None,
        "analysis_scope": scope,
        "live_evaluation_performed": live,
        "native_prose_coherent": native_prose_coherent,
        "requires_sync": not native_prose_coherent,
        "coverage": {
            "source_backed_semantic_total": 0,
            "tracked_semantic_total": 0,
            "untracked_semantic_total": 0,
            "issues": [],
            "untracked_targets": [],
        },
        "limitations": list(LIMITATIONS),
    }
    if state is None:
        if marker is not None:
            raise ValueError("Adopted maintenance marker has no durable owner")
        if live and capture is not None:
            base["coverage"] = {
                "source_backed_semantic_total": capture.source_backed_semantic_total,
                "tracked_semantic_total": 0,
                "untracked_semantic_total": capture.source_backed_semantic_total,
                "issues": deepcopy(list(capture.issues)),
                "untracked_targets": [
                    deepcopy(value["target"])
                    for value in capture.by_owner.values()
                    if value["target_presence"] == "present"
                ],
            }
        return MaintenanceStatusReport(base, {}, {})
    owner, guard = (
        validate_maintenance_state(state),
        validate_maintenance_adoption(marker),
    )
    if owner["adoption_id"] != guard["adoption_id"] or owner[
        "guard_hash"
    ] != canonical_hash(guard):
        raise ValueError("Maintenance marker and authority disagree")
    base.update(adoption_id=owner["adoption_id"], state_hash=canonical_hash(owner))
    known = {
        owner_key(value["coordinate"], value["target"])
        for value in owner["observations"].values()
    }
    if live and capture is not None:
        untracked = [
            deepcopy(value["target"])
            for key, value in capture.by_owner.items()
            if key not in known and value["target_presence"] == "present"
        ]
        base["coverage"] = {
            "source_backed_semantic_total": capture.source_backed_semantic_total,
            "tracked_semantic_total": capture.tracked_semantic_total,
            "untracked_semantic_total": max(
                capture.source_backed_semantic_total - capture.tracked_semantic_total,
                len(untracked),
            ),
            "issues": deepcopy(list(capture.issues)),
            "untracked_targets": untracked,
        }
    if coverage is not None:
        base["coverage"] = deepcopy(dict(coverage))
    records, by_path = {}, {}
    qualified_analysis = (
        isinstance(analysis_compatibility_hash, str)
        and _HASH.fullmatch(analysis_compatibility_hash) is not None
    )
    for record_id, record in owner["records"].items():
        observed = owner["observations"][record_id]
        current = (
            capture.by_owner.get(owner_key(observed["coordinate"], observed["target"]))
            if live and capture is not None
            else None
        )
        reasons = set(record["reasons"])
        mapping = deepcopy(record["mapping"])
        effective = None
        basis = None
        comparison = None
        if live:
            effective = record["status"]
            if mapping["state"] != "resolved":
                effective = "pending"
                reasons.add(
                    "move-unresolved"
                    if mapping["state"] == "ambiguous"
                    else "source-deleted"
                )
            elif current is None:
                effective = "pending"
                reasons.add("current-basis-unavailable")
            else:
                if current["presence"] == "deleted":
                    reasons.add("source-deleted")
                if current["target_presence"] == "deleted":
                    reasons.add("target-deleted")
                if current["basis"] != observed["basis"]:
                    for key, reason in (
                        ("source_hash", "source-basis-changed"),
                        ("prose_hash", "prose-changed"),
                        ("comparison_id", "producer-incompatible"),
                        ("scope", "scope-incompatible"),
                    ):
                        if current["basis"][key] != observed["basis"][key]:
                            reasons.add(reason)
                    comparison = compare_implementation_observations(
                        observed["implementation"],
                        current["implementation"],
                        analysis_scope=scope,
                        expected_analysis_hash=analysis_compatibility_hash,
                    )
                    if comparison.state == "changed":
                        reasons.add("executable-syntax-changed")
                    elif comparison.state == "unavailable":
                        reasons.add("implementation-unavailable")
                    effective = "pending"
                valid = (
                    qualified_analysis
                    and current["presence"] == current["target_presence"] == "present"
                    and current["implementation"]["status"] == "available"
                    and current["implementation"]["producer"][
                        "analysis_compatibility_hash"
                    ]
                    == analysis_compatibility_hash
                    and current["basis"]["prose_hash"] is not None
                    and (
                        comparison is None
                        or comparison.reason != "identical-source-observation-mismatch"
                    )
                )
                if valid:
                    basis = deepcopy(current["basis"])
                else:
                    effective = "pending"
                    reasons.add("current-basis-unavailable")
        acknowledgment = next(
            (
                value
                for value in record["acknowledgment_history"]
                if value["acknowledgment_id"] == record["current_acknowledgment_id"]
            ),
            None,
        )
        row = {
            "record_id": record_id,
            "coordinate": deepcopy(observed["coordinate"]),
            "target": deepcopy(observed["target"]),
            "mapping": mapping,
            "recorded_status": record["status"],
            "effective_status": effective,
            "reasons": sorted(reasons),
            "recorded_basis": deepcopy(observed["basis"]),
            "expected_basis": basis,
            "basis_available": basis is not None,
            "acknowledgment": deepcopy(acknowledgment),
            "acknowledgment_history": deepcopy(record["acknowledgment_history"]),
            "source_location": _source_location(
                observed["coordinate"],
                observed["implementation"]["scope"],
                implementation_observations,
            ),
            "qualification": "snapshot"
            if not live
            else "current-capture"
            if basis is not None
            else "current-basis-unavailable",
            "governance_effect": "none",
        }
        records[record_id] = row
        targets = [
            observed["target"],
            *(candidate["target"] for candidate in mapping["candidates"]),
        ]
        for target in targets:
            path = target["canonical_path"]
            if record_id not in by_path.setdefault(path, []):
                by_path[path].append(record_id)
    return MaintenanceStatusReport(
        base, records, {path: tuple(ids) for path, ids in by_path.items()}
    )


def compact_maintenance_summary(value) -> dict:
    """No coordinates, hashes, actor history or prose enter curated context."""
    if isinstance(value, Mapping) and set(value) == SUMMARY_FIELDS:
        return validate_maintenance_summary(value)
    if isinstance(value, Mapping) and "summary" in value:
        return validate_maintenance_summary(value["summary"])
    payload = value.payload if isinstance(value, MaintenanceStatusReport) else value
    rows = (
        list(value.by_record.values())
        if isinstance(value, MaintenanceStatusReport)
        else payload.get("records", ())
    )
    return _summary(
        payload,
        rows,
        truncated=bool(payload.get("bounds", {}).get("truncated", False)),
        untracked=payload.get("coverage", {}).get("untracked_semantic_total", 0),
    )


def _summary(payload, rows, *, truncated=False, untracked=0):
    result = {
        key: payload[key]
        for key in (
            "availability",
            "analysis_scope",
            "live_evaluation_performed",
            "native_prose_coherent",
            "requires_sync",
        )
    }
    result.update(
        total=len(rows),
        pending=sum(
            (row.get("effective_status") or row.get("recorded_status")) == "pending"
            for row in rows
        ),
        acknowledged=sum(row.get("effective_status") == "acknowledged" for row in rows),
        unavailable=sum(
            row.get("effective_status") is None or not row.get("basis_available", False)
            for row in rows
        ),
        ambiguous=sum(
            row.get("mapping", {}).get("state") == "ambiguous" for row in rows
        ),
        deleted=sum(
            row.get("mapping", {}).get("state") == "deleted"
            or "source-deleted" in row.get("reasons", ())
            or "target-deleted" in row.get("reasons", ())
            for row in rows
        ),
        untracked=untracked,
        truncated=truncated,
        limitations=list(LIMITATIONS),
    )
    return validate_maintenance_summary(result)


def validate_maintenance_summary(value) -> dict:
    if not isinstance(value, Mapping) or set(value) != SUMMARY_FIELDS:
        raise ValueError("Maintenance summary fields must match the closed contract")
    if (
        not isinstance(value["availability"], str)
        or value["availability"] not in {"ready", "partial", "unadopted", "unavailable"}
        or not isinstance(value["analysis_scope"], str)
        or value["analysis_scope"] not in ANALYSIS_SCOPES
    ):
        raise ValueError("Unsupported maintenance summary qualification")
    for key in (
        "live_evaluation_performed",
        "native_prose_coherent",
        "requires_sync",
        "truncated",
    ):
        if type(value[key]) is not bool:
            raise ValueError("Maintenance summary flags must be booleans")
    for key in (
        "total",
        "pending",
        "acknowledged",
        "unavailable",
        "ambiguous",
        "deleted",
        "untracked",
    ):
        if type(value[key]) is not int or value[key] < 0:
            raise ValueError("Maintenance summary counts must be nonnegative integers")
    if (
        value["requires_sync"] != (not value["native_prose_coherent"])
        or not isinstance(value["limitations"], (list, tuple))
        or list(value["limitations"]) != list(LIMITATIONS)
    ):
        raise ValueError("Maintenance summary limitations/coherence disagree")
    if (
        value["analysis_scope"] in {"snapshot", "selected-header"}
        and value["live_evaluation_performed"]
    ):
        raise ValueError("Snapshot/header maintenance cannot claim live evaluation")
    if (
        any(
            value[key] > value["total"]
            for key in (
                "pending",
                "acknowledged",
                "unavailable",
                "ambiguous",
                "deleted",
            )
        )
        or value["pending"] + value["acknowledged"] > value["total"]
    ):
        raise ValueError("Maintenance summary subgroup counts exceed their total")
    if not value["live_evaluation_performed"] and value["acknowledged"]:
        raise ValueError("Snapshot maintenance cannot claim current acknowledgment")
    return deepcopy(dict(value))


def marker_from_validated_state(state) -> dict:
    """Reconstruct fixed v1 fields and verify the immutable commitment."""
    marker = {
        "schema_version": "llm-wiki-maintenance-adoption/v1",
        "adoption_id": state["adoption_id"],
        "min_manifest_version": 7,
        "features": {
            "implementation_evidence": 1,
            "maintenance_state": 1,
            "ordinary_acknowledgment": 1,
        },
    }
    if canonical_hash(marker) != state["guard_hash"]:
        raise ValueError("Validated authority does not bind the immutable v1 marker")
    return marker


def snapshot_report_for_view(view) -> MaintenanceStatusReport | None:
    manifest = view.manifest_basis
    state = manifest.maintenance_state if manifest is not None else None
    return (
        None
        if state is None
        else build_maintenance_status(state, marker_from_validated_state(state))
    )


def attach_maintenance_status(
    captured, *, live=True, analysis_scope=None, native_prose_coherent=True
):
    """Reuse captured source; historical native gaps stay separately disclosed."""
    from dataclasses import replace
    from .maintenance_service import maintenance_report_from_captured

    if not getattr(captured, "capture_implementation_requested", False):
        return replace(
            captured,
            knowledge_view=replace(captured.knowledge_view, maintenance_report=None),
        )
    if not live:
        report = snapshot_report_for_view(captured.knowledge_view)
    else:
        report = maintenance_report_from_captured(
            captured, raw_pages=captured.raw_content_by_page
        )
    return (
        captured
        if report is None
        else replace(
            captured,
            knowledge_view=replace(captured.knowledge_view, maintenance_report=report),
        )
    )


def attach_maintenance_view_from_inputs(
    view, inventory_result, *, content_by_page, raw_content_by_page, analysis_scope
):
    """Join existing guarded query inputs without extracting source again."""
    from dataclasses import replace
    from .extraction_service import InventoryResult
    from .maintenance_evidence import captured_observations_from_knowledge
    from .python_implementation import analysis_identity
    from .source_snapshot import confirmed_missing_source_paths

    if (
        not view.ready
        or view.knowledge is None
        or view.manifest_basis is None
        or view.manifest_basis.maintenance_state is None
    ):
        return view
    if (
        not isinstance(inventory_result, InventoryResult)
        or inventory_result.source_snapshot is None
    ):
        return view
    state = view.manifest_basis.maintenance_state
    snapshot = inventory_result.source_snapshot
    missing = confirmed_missing_source_paths(
        snapshot,
        {o["coordinate"]["source_path"] for o in state["observations"].values()},
    )
    analysis = analysis_identity(inventory_result.analysis_components)
    capture = captured_observations_from_knowledge(
        view.knowledge,
        content_by_page=content_by_page,
        raw_content_by_page=raw_content_by_page,
        page_source_mappings=view.manifest_basis.page_source_mappings,
        captures=inventory_result.implementation_observations,
        source_content_hashes=snapshot.captured_content_hashes,
        captured_paths=set(snapshot.captured_content_hashes) | set(missing),
        missing_source_paths=missing,
        analysis_compatibility_hash=analysis,
        previous_state=state,
    )
    report = build_maintenance_status(
        state,
        marker_from_validated_state(state),
        capture,
        implementation_observations=inventory_result.implementation_observations,
        analysis_scope=analysis_scope,
        analysis_compatibility_hash=analysis,
    )
    return replace(view, maintenance_report=report)
