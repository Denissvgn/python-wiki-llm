"""Versioned full-integrity CI report composition and validation.

The producer composes the knowledge-health projection from the exact
``LintReport`` already built by ``ci-check``.  It never invokes ``doctor`` or
performs another source extraction.  The strict loader and bounded renderer
are used by the portable GitHub integrity wrapper; broad ``ci-check`` policy
and its process exit remain authoritative over the nested health dashboard.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .contracts import CI_CHECK_SCHEMA_VERSION, DOCTOR_SCHEMA_VERSION
from .doctor_service import compose_doctor_report
from .knowledge_observability import KnowledgeAggregateSummary
from .lint_service import LintReport, report_to_dict


_CI_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "wiki_dir",
        "src_dir",
        "strict",
        "knowledge_drift_gate",
        "knowledge_drift_report",
        "ok",
        "issue_count",
        "issues",
        "diagnostics",
        "execution",
        "knowledge_health",
    }
)
_CI_OPTIONAL_FIELDS = frozenset({"knowledge_summary"})
_KNOWLEDGE_SUMMARY_FIELDS = frozenset(
    {
        "availability",
        "reason",
        "freshness",
        "concepts_evaluated",
        "freshness_counts",
        "evidence_issue_counts",
        "degraded_reason",
        "phase_durations_ms",
        "freshness_evaluated",
        "concepts_total",
        "concepts_by_kind",
        "evidence_by_state",
        "freshness_by_state",
    }
)
_LINT_ISSUE_REQUIRED_FIELDS = frozenset(
    {"category", "message", "severity", "path", "target"}
)
_LINT_ISSUE_OPTIONAL_FIELDS = frozenset({"reason_code", "hint"})
_EXTRACTOR_JOB_FIELDS = frozenset(
    {
        "requested_jobs",
        "resolved_jobs",
        "eligible_parallel_plans",
        "effective_workers",
        "parallel_plan_ids",
        "sequential_plan_ids",
        "cache_elided_plan_ids",
    }
)
_DOCTOR_FIELDS = frozenset(
    {
        "schema_version",
        "status",
        "exit_code",
        "strict",
        "wiki_dir",
        "src_dir",
        "availability",
        "freshness",
        "snapshot_parity",
        "governance",
        "drift",
        "verification_receipt",
        "degraded_reasons",
        "unhealthy_reasons",
    }
)
_AVAILABILITY_FIELDS = frozenset({"state", "reason", "usable"})
_FRESHNESS_FIELDS = frozenset(
    {"evaluated", "disclosure", "concepts", "counts_by_state"}
)
_SNAPSHOT_FIELDS = frozenset({"state", "issue_count", "reasons"})
_GOVERNANCE_FIELDS = frozenset(
    {
        "state",
        "ledger",
        "projection",
        "expired_reviews",
        "issue_count",
        "reasons",
    }
)
_DRIFT_FIELDS = frozenset(
    {
        "state",
        "confirmed_stale",
        "indeterminate",
        "nonsemantic_changes",
        "counts_by_state",
        "diagnostic_count",
        "reasons",
    }
)
_VERIFICATION_FIELDS = frozenset({"state", "reason", "recorded_result", "passed"})
_FRESHNESS_STATES = frozenset(
    {
        "unknown",
        "current",
        "nonsemantic-source-change",
        "source-changed",
        "basis-incompatible",
        "source-missing",
    }
)
_DOCTOR_STATUS_EXIT = {
    "healthy": 0,
    "degraded": 1,
    "unhealthy": 2,
    "absent": 3,
}
_AVAILABILITY_STATES = frozenset({"ready", "absent", "degraded", "unsupported"})
_SNAPSHOT_STATES = frozenset({"valid", "mixed", "invalid", "not-available"})
_GOVERNANCE_STATES = frozenset({"valid", "invalid", "not-present", "not-available"})
_GOVERNANCE_LEDGER_STATES = frozenset({"valid", "invalid", "not-present"})
_GOVERNANCE_PROJECTION_STATES = frozenset(
    {"valid", "invalid", "not-present", "not-available"}
)
_DRIFT_STATES = frozenset(
    {
        "current",
        "stale-confirmed",
        "indeterminate",
        "nonsemantic-change",
        "not-evaluated",
    }
)
_VERIFICATION_STATES = frozenset(
    {"valid", "failed", "invalid", "stale", "absent", "not-evaluated"}
)
_RECORDED_RESULTS = frozenset({"passed", "failed"})
_JSON_EVIDENCE_STATES = frozenset(
    {
        "available (validated llm-wiki-ci-check/v1)",
        "unavailable (no output)",
        "unavailable (unexpected evidence-path collision)",
        "unavailable (could not preserve validated output)",
        "unavailable (invalid v1 output; diagnostic raw available)",
        "unavailable (invalid output could not be preserved)",
        "unavailable (empty output)",
        "unavailable (raw output is not a regular file)",
    }
)
_SUMMARY_MAX_LINES = 40
_SUMMARY_MAX_BYTES = 8192
_STATUS_RECORD_LIMIT = 20
_REASON_RE = re.compile(r"\[reason=([a-z0-9-]+(?:,[a-z0-9-]+)*)\]")


class CiCheckReportError(ValueError):
    """A field-specific failure in the versioned CI report contract."""


def build_ci_check_payload(report: LintReport) -> dict[str, object]:
    """Compose CI v1 and doctor v1 from one already evaluated lint report."""

    if not isinstance(report, LintReport):
        raise TypeError("report must be a LintReport")
    payload: dict[str, object] = {
        "schema_version": CI_CHECK_SCHEMA_VERSION,
        **report_to_dict(report, include_execution=True),
    }
    payload["knowledge_health"] = compose_doctor_report(
        report,
        strict=False,
        wiki_dir=report.wiki_dir,
        src_dir=report.src_dir,
    ).to_payload()
    return payload


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CiCheckReportError("duplicate object key")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise CiCheckReportError(f"non-finite JSON number {value!r} is not supported")


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CiCheckReportError(f"{field} must be an object")
    return value


def _exact_object(
    value: object,
    field: str,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> Mapping[str, Any]:
    result = _object(value, field)
    missing = sorted(required - set(result))
    if missing:
        raise CiCheckReportError(f"{field}.{missing[0]} is required")
    unknown = sorted(set(result) - required - optional)
    if unknown:
        raise CiCheckReportError(f"{field} contains an unsupported field")
    return result


def _contract_object(
    value: object,
    field: str,
    required: frozenset[str],
    *,
    allow_additive: bool,
) -> Mapping[str, Any]:
    result = _object(value, field)
    missing = sorted(required - set(result))
    if missing:
        raise CiCheckReportError(f"{field}.{missing[0]} is required")
    if not allow_additive:
        unknown = sorted(set(result) - required)
        if unknown:
            raise CiCheckReportError(f"{field} contains an unsupported field")
    return result


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CiCheckReportError(f"{field} must be a non-empty string")
    return value


def _nullable_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _string(value, field)


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise CiCheckReportError(f"{field} must be a boolean")
    return value


def _nullable_boolean(value: object, field: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, field)


def _nullable_nonnegative_integer(value: object, field: str) -> int | None:
    if value is None:
        return None
    return _nonnegative_integer(value, field)


def _nonnegative_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CiCheckReportError(f"{field} must be a non-negative integer")
    return value


def _positive_integer(value: object, field: str) -> int:
    result = _nonnegative_integer(value, field)
    if result < 1:
        raise CiCheckReportError(f"{field} must be greater than zero")
    return result


def _enum(
    value: object,
    field: str,
    allowed: Mapping[str, object] | frozenset[str],
) -> str:
    result = _string(value, field)
    if result not in allowed:
        raise CiCheckReportError(f"{field} is unsupported")
    return result


def _array(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise CiCheckReportError(f"{field} must be an array")
    return value


def _string_array(value: object, field: str) -> list[str]:
    return [
        _string(item, f"{field}[{index}]")
        for index, item in enumerate(_array(value, field))
    ]


def _canonical_string_array(value: object, field: str) -> list[str]:
    values = _string_array(value, field)
    if values != sorted(set(values)):
        raise CiCheckReportError(f"{field} must be unique and sorted")
    return values


def _count_mapping(
    value: object,
    field: str,
    *,
    exact_keys: frozenset[str] | None = None,
) -> dict[str, int]:
    counts = _object(value, field)
    if exact_keys is not None and set(counts) != exact_keys:
        raise CiCheckReportError(f"{field} keys do not match the contract")
    result: dict[str, int] = {}
    for key, raw_count in counts.items():
        normalized = _string(key, f"{field} key")
        result[normalized] = _nonnegative_integer(raw_count, f"{field}.{normalized}")
    return result


def _finding_reasons(findings: Sequence[Mapping[str, Any]]) -> list[str]:
    reasons: set[str] = set()
    for finding in findings:
        reason_code = finding.get("reason_code")
        if isinstance(reason_code, str) and reason_code:
            reasons.add(reason_code)
        message = finding.get("message")
        if isinstance(message, str):
            for match in _REASON_RE.findall(message):
                reasons.update(match.split(","))
    return sorted(reasons) if reasons else (["unspecified"] if findings else [])


def _validate_lint_findings(
    value: object,
    field: str,
) -> list[Mapping[str, Any]]:
    findings = _array(value, field)
    validated: list[Mapping[str, Any]] = []
    for index, raw_finding in enumerate(findings):
        finding_field = f"{field}[{index}]"
        finding = _exact_object(
            raw_finding,
            finding_field,
            _LINT_ISSUE_REQUIRED_FIELDS,
            _LINT_ISSUE_OPTIONAL_FIELDS,
        )
        _string(finding["category"], f"{finding_field}.category")
        _string(finding["message"], f"{finding_field}.message")
        _string(finding["severity"], f"{finding_field}.severity")
        _nullable_string(finding["path"], f"{finding_field}.path")
        _nullable_string(finding["target"], f"{finding_field}.target")
        for optional in _LINT_ISSUE_OPTIONAL_FIELDS & set(finding):
            _nullable_string(finding[optional], f"{finding_field}.{optional}")
        validated.append(finding)
    return validated


def _canonical_plan_ids(value: object, field: str) -> list[str]:
    identifiers = _string_array(value, field)
    if identifiers != sorted(set(identifiers)):
        raise CiCheckReportError(f"{field} must be unique and sorted")
    return identifiers


def _validate_execution(value: object) -> None:
    execution = _exact_object(value, "report.execution", frozenset({"extractor_jobs"}))
    jobs = _exact_object(
        execution["extractor_jobs"],
        "report.execution.extractor_jobs",
        _EXTRACTOR_JOB_FIELDS,
    )
    requested = jobs["requested_jobs"]
    if requested != "auto":
        requested = _positive_integer(
            requested,
            "report.execution.extractor_jobs.requested_jobs",
        )
    resolved = _positive_integer(
        jobs["resolved_jobs"],
        "report.execution.extractor_jobs.resolved_jobs",
    )
    if requested != "auto" and requested != resolved:
        raise CiCheckReportError(
            "report.execution.extractor_jobs.requested_jobs must equal "
            "resolved_jobs unless it is 'auto'"
        )
    eligible = _nonnegative_integer(
        jobs["eligible_parallel_plans"],
        "report.execution.extractor_jobs.eligible_parallel_plans",
    )
    effective = _nonnegative_integer(
        jobs["effective_workers"],
        "report.execution.extractor_jobs.effective_workers",
    )
    parallel = _canonical_plan_ids(
        jobs["parallel_plan_ids"],
        "report.execution.extractor_jobs.parallel_plan_ids",
    )
    sequential = _canonical_plan_ids(
        jobs["sequential_plan_ids"],
        "report.execution.extractor_jobs.sequential_plan_ids",
    )
    cache_elided = _canonical_plan_ids(
        jobs["cache_elided_plan_ids"],
        "report.execution.extractor_jobs.cache_elided_plan_ids",
    )
    if eligible != len(parallel):
        raise CiCheckReportError(
            "report.execution.extractor_jobs.eligible_parallel_plans must equal "
            "the parallel plan count"
        )
    plan_sets = [set(parallel), set(sequential), set(cache_elided)]
    if any(
        left & right
        for index, left in enumerate(plan_sets)
        for right in plan_sets[index + 1 :]
    ):
        raise CiCheckReportError(
            "report.execution.extractor_jobs plan identifiers must be disjoint"
        )
    if parallel:
        expected_workers = min(resolved, len(parallel))
    elif sequential:
        expected_workers = 1
    else:
        expected_workers = 0
    if effective != expected_workers:
        raise CiCheckReportError(
            "report.execution.extractor_jobs.effective_workers does not match "
            "the planned work"
        )


def _freshness_counts(value: object, field: str) -> Mapping[str, Any] | None:
    if value is None:
        return None
    counts = _exact_object(value, field, _FRESHNESS_STATES)
    for state in sorted(_FRESHNESS_STATES):
        _nonnegative_integer(counts[state], f"{field}.{state}")
    return counts


def _validate_knowledge_summary(
    value: object,
    *,
    health: Mapping[str, Any],
) -> None:
    field = "report.knowledge_summary"
    summary = _exact_object(value, field, _KNOWLEDGE_SUMMARY_FIELDS)
    try:
        aggregate = KnowledgeAggregateSummary(
            availability=summary["availability"],
            reason=summary["reason"],
            concepts_evaluated=summary["concepts_evaluated"],
            freshness_counts=summary["freshness_counts"],
            evidence_issue_counts=summary["evidence_issue_counts"],
            degraded_reason=summary["degraded_reason"],
            phase_durations_ms=summary["phase_durations_ms"],
            freshness_evaluated=summary["freshness_evaluated"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CiCheckReportError(f"{field} is inconsistent: {exc}") from exc
    if _string(summary["freshness"], f"{field}.freshness") != aggregate.freshness:
        raise CiCheckReportError(f"{field}.freshness is inconsistent")

    concepts_total = _nonnegative_integer(
        summary["concepts_total"], f"{field}.concepts_total"
    )
    concepts_by_kind = _count_mapping(
        summary["concepts_by_kind"], f"{field}.concepts_by_kind"
    )
    if sum(concepts_by_kind.values()) != concepts_total:
        raise CiCheckReportError(
            f"{field}.concepts_by_kind does not match concepts_total"
        )
    _count_mapping(summary["evidence_by_state"], f"{field}.evidence_by_state")
    freshness_by_state = _count_mapping(
        summary["freshness_by_state"], f"{field}.freshness_by_state"
    )
    expected_freshness_by_state = (
        {}
        if aggregate.freshness_counts is None
        else dict(aggregate.freshness_counts)
    )
    if freshness_by_state != expected_freshness_by_state:
        raise CiCheckReportError(
            f"{field}.freshness_by_state does not match freshness_counts"
        )

    availability = _object(
        health["availability"], "report.knowledge_health.availability"
    )
    freshness = _object(health["freshness"], "report.knowledge_health.freshness")
    if aggregate.availability != availability["state"]:
        raise CiCheckReportError(
            f"{field}.availability does not match report.knowledge_health"
        )
    if aggregate.reason != availability["reason"]:
        raise CiCheckReportError(
            f"{field}.reason does not match report.knowledge_health"
        )
    if aggregate.freshness_evaluated is not freshness["evaluated"]:
        raise CiCheckReportError(
            f"{field}.freshness_evaluated does not match report.knowledge_health"
        )
    if aggregate.freshness != freshness["disclosure"]:
        raise CiCheckReportError(
            f"{field}.freshness does not match report.knowledge_health"
        )
    if aggregate.concepts_evaluated != freshness["concepts"]:
        raise CiCheckReportError(
            f"{field}.concepts_evaluated does not match report.knowledge_health"
        )
    expected_counts = (
        None
        if aggregate.freshness_counts is None
        else dict(aggregate.freshness_counts)
    )
    if expected_counts != freshness["counts_by_state"]:
        raise CiCheckReportError(
            f"{field}.freshness_counts does not match report.knowledge_health"
        )


def _expected_health_classification(
    *,
    strict: bool,
    source_selection_mismatch: bool,
    availability_state: str,
    freshness_evaluated: bool,
    snapshot_state: str,
    governance_state: str,
    expired_reviews: int,
    drift_state: str,
    verification_state: str,
) -> tuple[str, list[str], list[str]]:
    if availability_state == "absent":
        if source_selection_mismatch:
            return "unhealthy", [], ["source-selection-mismatch"]
        return "absent", [], []

    degraded: list[str] = []
    unhealthy: list[str] = []
    if source_selection_mismatch:
        unhealthy.append("source-selection-mismatch")
    if availability_state == "unsupported":
        unhealthy.append("knowledge-unsupported")
    elif availability_state == "degraded":
        degraded.append("knowledge-degraded")
    if snapshot_state == "mixed":
        unhealthy.append("mixed-snapshot")
    if governance_state == "invalid":
        unhealthy.append("invalid-governance")
    if drift_state == "stale-confirmed":
        unhealthy.append("stale-confirmed")
    elif drift_state == "indeterminate":
        (unhealthy if strict else degraded).append("freshness-indeterminate")
    elif drift_state == "nonsemantic-change":
        (unhealthy if strict else degraded).append("nonsemantic-source-change")
    if not freshness_evaluated:
        degraded.append("freshness-unevaluated")
    if expired_reviews:
        degraded.append("expired-reviews")
    if verification_state in {"failed", "invalid", "stale"}:
        unhealthy.append(f"verification-{verification_state}")

    degraded = list(dict.fromkeys(degraded))
    unhealthy = list(dict.fromkeys(unhealthy))
    status = "unhealthy" if unhealthy else "degraded" if degraded else "healthy"
    return status, degraded, unhealthy


def _validate_doctor(
    value: object,
    *,
    wiki_dir: str,
    src_dir: str,
    source_selection_mismatch: bool | None,
    expected_strict: bool,
    allow_additive: bool = False,
) -> Mapping[str, Any]:
    health = _contract_object(
        value,
        "report.knowledge_health",
        _DOCTOR_FIELDS,
        allow_additive=allow_additive,
    )
    if health["schema_version"] != DOCTOR_SCHEMA_VERSION:
        raise CiCheckReportError(
            f"report.knowledge_health.schema_version must be {DOCTOR_SCHEMA_VERSION!r}"
        )
    status = _enum(
        health["status"],
        "report.knowledge_health.status",
        _DOCTOR_STATUS_EXIT,
    )
    exit_code = _nonnegative_integer(
        health["exit_code"],
        "report.knowledge_health.exit_code",
    )
    if exit_code != _DOCTOR_STATUS_EXIT[status]:
        raise CiCheckReportError(
            "report.knowledge_health.exit_code does not match status"
        )
    strict = _boolean(health["strict"], "report.knowledge_health.strict")
    if strict is not expected_strict:
        raise CiCheckReportError(
            "report.knowledge_health.strict does not match the requested mode"
        )
    if _string(health["wiki_dir"], "report.knowledge_health.wiki_dir") != wiki_dir:
        raise CiCheckReportError(
            "report.knowledge_health.wiki_dir does not match report.wiki_dir"
        )
    if _string(health["src_dir"], "report.knowledge_health.src_dir") != src_dir:
        raise CiCheckReportError(
            "report.knowledge_health.src_dir does not match report.src_dir"
        )

    availability = _contract_object(
        health["availability"],
        "report.knowledge_health.availability",
        _AVAILABILITY_FIELDS,
        allow_additive=allow_additive,
    )
    availability_state = _enum(
        availability["state"],
        "report.knowledge_health.availability.state",
        _AVAILABILITY_STATES,
    )
    _string(
        availability["reason"],
        "report.knowledge_health.availability.reason",
    )
    usable = _boolean(
        availability["usable"],
        "report.knowledge_health.availability.usable",
    )
    if usable is not (availability_state in {"ready", "degraded"}):
        raise CiCheckReportError(
            "report.knowledge_health.availability.usable does not match state"
        )

    freshness = _contract_object(
        health["freshness"],
        "report.knowledge_health.freshness",
        _FRESHNESS_FIELDS,
        allow_additive=allow_additive,
    )
    evaluated = _boolean(
        freshness["evaluated"],
        "report.knowledge_health.freshness.evaluated",
    )
    _string(
        freshness["disclosure"],
        "report.knowledge_health.freshness.disclosure",
    )
    concepts = _nonnegative_integer(
        freshness["concepts"],
        "report.knowledge_health.freshness.concepts",
    )
    counts = _freshness_counts(
        freshness["counts_by_state"],
        "report.knowledge_health.freshness.counts_by_state",
    )
    if evaluated is not (counts is not None):
        raise CiCheckReportError(
            "report.knowledge_health.freshness.counts_by_state does not match evaluated"
        )
    if counts is not None and sum(int(count) for count in counts.values()) != concepts:
        raise CiCheckReportError(
            "report.knowledge_health.freshness.concepts does not match counts"
        )

    snapshot = _contract_object(
        health["snapshot_parity"],
        "report.knowledge_health.snapshot_parity",
        _SNAPSHOT_FIELDS,
        allow_additive=allow_additive,
    )
    snapshot_state = _enum(
        snapshot["state"],
        "report.knowledge_health.snapshot_parity.state",
        _SNAPSHOT_STATES,
    )
    snapshot_issue_count = _nonnegative_integer(
        snapshot["issue_count"],
        "report.knowledge_health.snapshot_parity.issue_count",
    )
    snapshot_reasons = _canonical_string_array(
        snapshot["reasons"],
        "report.knowledge_health.snapshot_parity.reasons",
    )
    if bool(snapshot_issue_count) is not bool(snapshot_reasons):
        raise CiCheckReportError(
            "report.knowledge_health.snapshot_parity issue count and reasons must agree"
        )

    governance = _contract_object(
        health["governance"],
        "report.knowledge_health.governance",
        _GOVERNANCE_FIELDS,
        allow_additive=allow_additive,
    )
    governance_state = _enum(
        governance["state"],
        "report.knowledge_health.governance.state",
        _GOVERNANCE_STATES,
    )
    ledger_state = _enum(
        governance["ledger"],
        "report.knowledge_health.governance.ledger",
        _GOVERNANCE_LEDGER_STATES,
    )
    projection_state = _enum(
        governance["projection"],
        "report.knowledge_health.governance.projection",
        _GOVERNANCE_PROJECTION_STATES,
    )
    expired_reviews = _nonnegative_integer(
        governance["expired_reviews"],
        "report.knowledge_health.governance.expired_reviews",
    )
    governance_issue_count = _nonnegative_integer(
        governance["issue_count"],
        "report.knowledge_health.governance.issue_count",
    )
    governance_reasons = _canonical_string_array(
        governance["reasons"],
        "report.knowledge_health.governance.reasons",
    )
    if (governance_state == "invalid") is not bool(governance_issue_count):
        raise CiCheckReportError(
            "report.knowledge_health.governance.state does not match issue_count"
        )
    if bool(governance_issue_count) is not bool(governance_reasons):
        raise CiCheckReportError(
            "report.knowledge_health.governance issue count and reasons must agree"
        )
    if governance_state == "invalid":
        valid_pair = ledger_state in {"invalid", "not-present"} and (
            projection_state in {"invalid", "not-available"}
        )
    else:
        valid_pair = ledger_state in {"valid", "not-present"} and (
            projection_state in {"valid", "not-present"}
        )
    if not valid_pair:
        raise CiCheckReportError(
            "report.knowledge_health.governance component states do not match state"
        )
    if governance_state == "valid" and "valid" not in {
        ledger_state,
        projection_state,
    }:
        raise CiCheckReportError(
            "report.knowledge_health.governance valid state has no valid component"
        )
    if governance_state == "not-present" and {
        ledger_state,
        projection_state,
    } != {"not-present"}:
        raise CiCheckReportError(
            "report.knowledge_health.governance not-present state is inconsistent"
        )

    drift = _contract_object(
        health["drift"],
        "report.knowledge_health.drift",
        _DRIFT_FIELDS,
        allow_additive=allow_additive,
    )
    drift_state = _enum(
        drift["state"],
        "report.knowledge_health.drift.state",
        _DRIFT_STATES,
    )
    confirmed_stale = _nonnegative_integer(
        drift["confirmed_stale"],
        "report.knowledge_health.drift.confirmed_stale",
    )
    indeterminate = _nonnegative_integer(
        drift["indeterminate"],
        "report.knowledge_health.drift.indeterminate",
    )
    nonsemantic_changes = _nonnegative_integer(
        drift["nonsemantic_changes"],
        "report.knowledge_health.drift.nonsemantic_changes",
    )
    diagnostic_count = _nonnegative_integer(
        drift["diagnostic_count"],
        "report.knowledge_health.drift.diagnostic_count",
    )
    drift_counts = _freshness_counts(
        drift["counts_by_state"],
        "report.knowledge_health.drift.counts_by_state",
    )
    if (drift_state == "not-evaluated") is not (drift_counts is None):
        raise CiCheckReportError(
            "report.knowledge_health.drift.counts_by_state does not match state"
        )
    if (
        None if counts is None else dict(counts)
    ) != (None if drift_counts is None else dict(drift_counts)):
        raise CiCheckReportError(
            "report.knowledge_health.drift.counts_by_state does not match freshness"
        )
    expected_confirmed = (
        0
        if drift_counts is None
        else int(drift_counts["source-changed"]) + int(drift_counts["source-missing"])
    )
    if confirmed_stale != expected_confirmed:
        raise CiCheckReportError(
            "report.knowledge_health.drift.confirmed_stale does not match counts"
        )
    expected_drift_state = (
        "not-evaluated"
        if drift_counts is None
        else "stale-confirmed"
        if confirmed_stale
        else "indeterminate"
        if indeterminate
        else "nonsemantic-change"
        if nonsemantic_changes
        else "current"
    )
    if drift_state != expected_drift_state:
        raise CiCheckReportError(
            "report.knowledge_health.drift.state does not match its counts"
        )
    if indeterminate + nonsemantic_changes > diagnostic_count:
        raise CiCheckReportError(
            "report.knowledge_health.drift diagnostic subsets exceed total"
        )
    drift_reasons = _canonical_string_array(
        drift["reasons"],
        "report.knowledge_health.drift.reasons",
    )
    if bool(diagnostic_count) is not bool(drift_reasons):
        raise CiCheckReportError(
            "report.knowledge_health.drift diagnostic count and reasons must agree"
        )

    verification = _contract_object(
        health["verification_receipt"],
        "report.knowledge_health.verification_receipt",
        _VERIFICATION_FIELDS,
        allow_additive=allow_additive,
    )
    verification_state = _enum(
        verification["state"],
        "report.knowledge_health.verification_receipt.state",
        _VERIFICATION_STATES,
    )
    _string(
        verification["reason"],
        "report.knowledge_health.verification_receipt.reason",
    )
    recorded_result = verification["recorded_result"]
    if recorded_result is not None:
        _enum(
            recorded_result,
            "report.knowledge_health.verification_receipt.recorded_result",
            _RECORDED_RESULTS,
        )
    passed = _nullable_boolean(
        verification["passed"],
        "report.knowledge_health.verification_receipt.passed",
    )
    if verification_state in {"absent", "not-evaluated"} and (
        recorded_result is not None or passed is not None
    ):
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt unrecorded state "
            "must not carry a result"
        )
    if (recorded_result is None) is not (passed is None):
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt result fields disagree"
        )
    if recorded_result == "passed" and passed is not True:
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt recorded result disagrees"
        )
    if recorded_result == "failed" and passed is not False:
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt recorded result disagrees"
        )
    if verification_state == "failed" and (
        recorded_result != "failed" or passed is not False
    ):
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt failed state is inconsistent"
        )
    if verification_state == "valid" and (
        recorded_result != "passed" or passed is not True
    ):
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt valid state is inconsistent"
        )
    if verification_state == "stale" and passed is not False:
        raise CiCheckReportError(
            "report.knowledge_health.verification_receipt stale state is inconsistent"
        )

    expected_snapshot_states = {
        "ready": {"valid"},
        "absent": {"not-available"},
        "degraded": {"mixed", "invalid"},
        "unsupported": {"not-available"},
    }
    if snapshot_state not in expected_snapshot_states[availability_state]:
        raise CiCheckReportError(
            "report.knowledge_health.snapshot_parity.state does not match availability"
        )
    if availability_state in {"absent", "unsupported"} and (
        evaluated
        or concepts != 0
        or counts is not None
        or drift_state != "not-evaluated"
    ):
        raise CiCheckReportError(
            "report.knowledge_health unavailable knowledge has evaluated freshness"
        )
    if availability_state == "absent" and (
        governance_state != "not-present" or verification_state != "absent"
    ):
        raise CiCheckReportError(
            "report.knowledge_health absent availability contradicts its sections"
        )

    degraded_reasons = _string_array(
        health["degraded_reasons"],
        "report.knowledge_health.degraded_reasons",
    )
    unhealthy_reasons = _string_array(
        health["unhealthy_reasons"],
        "report.knowledge_health.unhealthy_reasons",
    )
    if source_selection_mismatch is None:
        source_selection_mismatch = (
            "source-selection-mismatch" in unhealthy_reasons
        )
    expected_status, expected_degraded, expected_unhealthy = (
        _expected_health_classification(
            strict=strict,
            source_selection_mismatch=source_selection_mismatch,
            availability_state=availability_state,
            freshness_evaluated=evaluated,
            snapshot_state=snapshot_state,
            governance_state=governance_state,
            expired_reviews=expired_reviews,
            drift_state=drift_state,
            verification_state=verification_state,
        )
    )
    if status != expected_status:
        raise CiCheckReportError(
            "report.knowledge_health.status does not match its sections"
        )
    if degraded_reasons != expected_degraded:
        raise CiCheckReportError(
            "report.knowledge_health.degraded_reasons do not match its sections"
        )
    if unhealthy_reasons != expected_unhealthy:
        raise CiCheckReportError(
            "report.knowledge_health.unhealthy_reasons do not match its sections"
        )
    return health


def validate_doctor_payload(
    value: object,
    *,
    expected_strict: bool,
    source_selection_mismatch: bool | None = None,
    allow_additive: bool = False,
) -> Mapping[str, Any]:
    """Validate doctor v1 structure, semantics, and overall classification."""

    health = _contract_object(
        value,
        "report.knowledge_health",
        _DOCTOR_FIELDS,
        allow_additive=allow_additive,
    )
    wiki_dir = _string(health["wiki_dir"], "report.knowledge_health.wiki_dir")
    src_dir = _string(health["src_dir"], "report.knowledge_health.src_dir")
    return _validate_doctor(
        health,
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        source_selection_mismatch=source_selection_mismatch,
        expected_strict=expected_strict,
        allow_additive=allow_additive,
    )


def validate_ci_check_payload(
    value: object,
    *,
    cli_exit: int,
) -> Mapping[str, Any]:
    """Validate the complete CI v1 contract and its captured process exit."""

    report = _exact_object(
        value,
        "report",
        _CI_REQUIRED_FIELDS,
        _CI_OPTIONAL_FIELDS,
    )
    if report["schema_version"] != CI_CHECK_SCHEMA_VERSION:
        raise CiCheckReportError(
            f"report.schema_version must be {CI_CHECK_SCHEMA_VERSION!r}"
        )
    wiki_dir = _string(report["wiki_dir"], "report.wiki_dir")
    src_dir = _string(report["src_dir"], "report.src_dir")
    if not _boolean(report["strict"], "report.strict"):
        raise CiCheckReportError("report.strict must be true for ci-check")
    if _boolean(report["knowledge_drift_gate"], "report.knowledge_drift_gate"):
        raise CiCheckReportError("report.knowledge_drift_gate must be false")
    _boolean(report["knowledge_drift_report"], "report.knowledge_drift_report")
    ok = _boolean(report["ok"], "report.ok")
    issue_count = _nonnegative_integer(report["issue_count"], "report.issue_count")
    issues = _validate_lint_findings(report["issues"], "report.issues")
    diagnostics = _validate_lint_findings(
        report["diagnostics"], "report.diagnostics"
    )
    if issue_count != len(issues):
        raise CiCheckReportError("report.issue_count does not match report.issues")
    if ok is not (issue_count == 0):
        raise CiCheckReportError("report.ok does not match report.issue_count")
    _validate_execution(report["execution"])
    source_selection_mismatch = any(
        finding["category"] == "source-selection-mismatch" for finding in issues
    )
    health = _validate_doctor(
        report["knowledge_health"],
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        source_selection_mismatch=source_selection_mismatch,
        expected_strict=False,
    )
    if "knowledge_summary" in report:
        _validate_knowledge_summary(report["knowledge_summary"], health=health)

    drift = _object(health["drift"], "report.knowledge_health.drift")
    freshness_diagnostics = [
        finding
        for finding in diagnostics
        if finding["category"] == "knowledge_freshness"
    ]
    if drift["diagnostic_count"] != len(freshness_diagnostics):
        raise CiCheckReportError(
            "report.knowledge_health.drift.diagnostic_count does not match "
            "report.diagnostics"
        )
    if drift["reasons"] != _finding_reasons(freshness_diagnostics):
        raise CiCheckReportError(
            "report.knowledge_health.drift.reasons do not match report.diagnostics"
        )

    governance = _object(
        health["governance"], "report.knowledge_health.governance"
    )
    governance_issues = [
        finding
        for finding in issues
        if finding["category"] == "knowledge_governance"
    ]
    review_issues = [
        finding
        for finding in issues
        if finding["category"] == "knowledge_review"
    ]
    if governance["issue_count"] != len(governance_issues):
        raise CiCheckReportError(
            "report.knowledge_health.governance.issue_count does not match "
            "report.issues"
        )
    if governance["reasons"] != _finding_reasons(governance_issues):
        raise CiCheckReportError(
            "report.knowledge_health.governance.reasons do not match report.issues"
        )
    if governance["expired_reviews"] != len(review_issues):
        raise CiCheckReportError(
            "report.knowledge_health.governance.expired_reviews does not match "
            "report.issues"
        )

    if isinstance(cli_exit, bool) or not isinstance(cli_exit, int):
        raise CiCheckReportError("cli_exit must be an integer")
    expected_exit = 0 if ok else 1
    if cli_exit != expected_exit:
        raise CiCheckReportError("captured ci-check exit code does not match report.ok")
    return report


def load_ci_check_payload(
    path: str | Path,
    *,
    cli_exit: int,
) -> Mapping[str, Any]:
    """Read strict UTF-8 JSON and validate the complete CI v1 contract."""

    report_path = Path(path)
    if report_path.is_symlink() or not report_path.is_file():
        raise CiCheckReportError("report path must be a regular file")
    try:
        raw = report_path.read_text(encoding="utf-8")
        payload = json.loads(
            raw,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite,
        )
    except CiCheckReportError:
        raise
    except (OSError, UnicodeError, ValueError) as exc:
        raise CiCheckReportError(f"report is not strict UTF-8 JSON: {exc}") from exc
    return validate_ci_check_payload(payload, cli_exit=cli_exit)


def _clip_utf8(value: str, limit: int = 240) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= limit:
        return value
    prefix = encoded[: limit - 3]
    while True:
        try:
            return prefix.decode("utf-8") + "..."
        except UnicodeDecodeError as exc:
            prefix = prefix[: exc.start]


def render_ci_summary(
    report: Mapping[str, Any] | None,
    *,
    result: str,
    cli_exit: int,
    json_state: str,
    markdown_state: str,
    tree_state: str,
    status_records: Sequence[bytes],
    status_count: int,
    status_limit: int,
    max_lines: int,
    max_bytes: int,
) -> bytes:
    """Render fixed-state integrity and health evidence within strict bounds."""

    if result not in {"PASS", "FAIL"}:
        raise CiCheckReportError("result must be PASS or FAIL")
    for field, value in (
        ("cli_exit", cli_exit),
        ("status_count", status_count),
        ("status_limit", status_limit),
        ("max_lines", max_lines),
        ("max_bytes", max_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise CiCheckReportError(f"{field} must be a non-negative integer")
    if json_state not in _JSON_EVIDENCE_STATES:
        raise CiCheckReportError("json_state is unsupported")
    if markdown_state not in {"available", "unavailable"}:
        raise CiCheckReportError("markdown_state is unsupported")
    expected_tree_state = (
        "clean"
        if status_count == 0
        else f"dirty ({status_count} status records)"
    )
    if tree_state not in {expected_tree_state, "unavailable"}:
        raise CiCheckReportError("tree_state does not match status_count")
    if tree_state == "unavailable" and status_count:
        raise CiCheckReportError("unavailable tree state must not carry records")
    if status_limit > _STATUS_RECORD_LIMIT:
        raise CiCheckReportError("status_limit exceeds the frozen bound")
    if max_lines > _SUMMARY_MAX_LINES or max_bytes > _SUMMARY_MAX_BYTES:
        raise CiCheckReportError("summary bounds exceed the frozen limits")
    if len(status_records) != status_count:
        raise CiCheckReportError("status_count does not match the status records")
    if report is not None:
        validate_ci_check_payload(report, cli_exit=cli_exit)
    report_available = report is not None
    json_available = json_state == "available (validated llm-wiki-ci-check/v1)"
    if report_available is not json_available:
        raise CiCheckReportError("validated report and JSON evidence state disagree")
    expected_result = (
        "PASS"
        if cli_exit == 0
        and report_available
        and markdown_state == "available"
        and tree_state == "clean"
        else "FAIL"
    )
    if result != expected_result:
        raise CiCheckReportError("result does not match the validated evidence")

    lines = [
        "## LLM Wiki integrity",
        f"- Result: **{result}**",
    ]
    if cli_exit != 0:
        lines.append(f"- Original `ci-check` exit: `{cli_exit}`")
    lines.extend(
        [
            f"- JSON evidence: {json_state}",
            f"- Markdown report: {markdown_state}",
            f"- Worktree: {tree_state}",
        ]
    )
    if report is not None:
        health = _object(report["knowledge_health"], "report.knowledge_health")
        availability = _object(
            health["availability"], "report.knowledge_health.availability"
        )
        freshness = _object(health["freshness"], "report.knowledge_health.freshness")
        snapshot = _object(
            health["snapshot_parity"], "report.knowledge_health.snapshot_parity"
        )
        governance = _object(health["governance"], "report.knowledge_health.governance")
        drift = _object(health["drift"], "report.knowledge_health.drift")
        verification = _object(
            health["verification_receipt"],
            "report.knowledge_health.verification_receipt",
        )
        freshness_label = (
            f"evaluated ({freshness['concepts']} concepts)"
            if freshness["evaluated"]
            else "not evaluated"
        )
        lines.extend(
            [
                f"- Blocking issues: `{report['issue_count']}`",
                f"- Knowledge health: `{health['status']}`",
                f"- Availability: `{availability['state']}`",
                f"- Freshness: `{freshness_label}`",
                (
                    "- Snapshot / governance: "
                    f"`{snapshot['state']}` / `{governance['state']}`"
                ),
                (
                    "- Drift: "
                    f"`{drift['state']}` "
                    f"(confirmed={drift['confirmed_stale']}, "
                    f"indeterminate={drift['indeterminate']})"
                ),
                f"- Verification receipt: `{verification['state']}`",
            ]
        )
    else:
        lines.extend(
            [
                "- Blocking issues: unavailable",
                "- Knowledge health: `unavailable`",
                "- Availability: `unavailable`",
                "- Freshness: `unavailable`",
                "- Snapshot / governance: `unavailable` / `unavailable`",
                "- Drift: `unavailable`",
                "- Verification receipt: `unavailable`",
            ]
        )
    lines.append(
        "- Native drift diagnostics are advisory; integrity validation remains blocking."
    )
    if status_count:
        lines.append("- Dirty-path diagnostics (sorted and bounded):")
        for raw_record in status_records[:status_limit]:
            record = raw_record.decode("utf-8", "backslashreplace")
            record = record.replace(chr(96), "\\x60")
            lines.append(f"  - `{_clip_utf8(record)}`")
        if status_count > status_limit:
            lines.append(
                f"  - ... {status_count - status_limit} additional status records omitted"
            )

    payload = ("\n".join(lines) + "\n").encode("utf-8")
    if len(lines) > max_lines or len(payload) > max_bytes:
        raise CiCheckReportError("bounded summary invariant failed")
    return payload


def _arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--report", required=True)
    validate.add_argument("--cli-exit", required=True, type=int)

    summary = commands.add_parser("render-summary")
    summary.add_argument("--report")
    summary.add_argument("--cli-exit", required=True, type=int)
    summary.add_argument("--result", choices=("PASS", "FAIL"), required=True)
    summary.add_argument("--json-state", required=True)
    summary.add_argument("--markdown-state", required=True)
    summary.add_argument("--tree-state", required=True)
    summary.add_argument("--status-path", required=True)
    summary.add_argument("--status-count", required=True, type=int)
    summary.add_argument("--status-limit", required=True, type=int)
    summary.add_argument("--max-lines", required=True, type=int)
    summary.add_argument("--max-bytes", required=True, type=int)
    summary.add_argument("--output", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Internal CLI used by the isolated GitHub integrity wrapper."""

    args = _arguments(argv)
    try:
        if args.action == "validate":
            load_ci_check_payload(args.report, cli_exit=args.cli_exit)
            return 0

        report = (
            None
            if args.report is None
            else load_ci_check_payload(args.report, cli_exit=args.cli_exit)
        )
        status_path = Path(args.status_path)
        if status_path.is_symlink() or not status_path.is_file():
            raise CiCheckReportError("status path must be a regular file")
        status_records = status_path.read_bytes().splitlines()
        payload = render_ci_summary(
            report,
            result=args.result,
            cli_exit=args.cli_exit,
            json_state=args.json_state,
            markdown_state=args.markdown_state,
            tree_state=args.tree_state,
            status_records=status_records,
            status_count=args.status_count,
            status_limit=args.status_limit,
            max_lines=args.max_lines,
            max_bytes=args.max_bytes,
        )
        output = Path(args.output)
        if output.is_symlink() or not output.parent.is_dir():
            raise CiCheckReportError("summary output path is unsafe")
        output.write_bytes(payload)
        return 0
    except (CiCheckReportError, OSError) as exc:
        raise SystemExit(f"ci-check evidence contract failed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
