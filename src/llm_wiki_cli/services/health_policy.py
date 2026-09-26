"""Pure release-health decisions derived from one validated CI evaluation."""

from __future__ import annotations

import copy
from enum import Enum
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


class DoctorStatus(str, Enum):
    """Closed overall health vocabulary for the doctor contract."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    ABSENT = "absent"


DOCTOR_EXIT_CODES: Mapping[DoctorStatus, int] = {
    DoctorStatus.HEALTHY: 0,
    DoctorStatus.DEGRADED: 1,
    DoctorStatus.UNHEALTHY: 2,
    DoctorStatus.ABSENT: 3,
}


def classify_health_sections(
    *,
    strict: bool,
    source_selection_mismatch: bool,
    availability: Mapping[str, object],
    freshness: Mapping[str, object],
    snapshot: Mapping[str, object],
    governance: Mapping[str, object],
    drift: Mapping[str, object],
    verification: Mapping[str, object],
) -> tuple[DoctorStatus, tuple[str, ...], tuple[str, ...]]:
    availability_state = availability["state"]
    if availability_state == "absent":
        if source_selection_mismatch:
            return DoctorStatus.UNHEALTHY, (), ("source-selection-mismatch",)
        return DoctorStatus.ABSENT, (), ()

    unhealthy: list[str] = []
    degraded: list[str] = []
    if source_selection_mismatch:
        unhealthy.append("source-selection-mismatch")
    if availability_state == "unsupported":
        unhealthy.append("knowledge-unsupported")
    elif availability_state == "degraded":
        degraded.append("knowledge-degraded")
    if snapshot["state"] == "mixed":
        unhealthy.append("mixed-snapshot")
    if governance["state"] == "invalid":
        unhealthy.append("invalid-governance")
    if drift["state"] == "stale-confirmed":
        unhealthy.append("stale-confirmed")
    elif drift["state"] == "indeterminate":
        (unhealthy if strict else degraded).append("freshness-indeterminate")
    elif drift["state"] == "nonsemantic-change":
        (unhealthy if strict else degraded).append("nonsemantic-source-change")
    if not freshness["evaluated"]:
        degraded.append("freshness-unevaluated")
    expired_reviews = governance["expired_reviews"]
    if isinstance(expired_reviews, bool) or not isinstance(expired_reviews, int):
        raise TypeError("governance expired_reviews must be an integer")
    if expired_reviews > 0:
        degraded.append("expired-reviews")
    if verification["state"] in {"failed", "invalid", "stale"}:
        unhealthy.append(f"verification-{verification['state']}")

    unhealthy_reasons = tuple(dict.fromkeys(unhealthy))
    degraded_reasons = tuple(dict.fromkeys(degraded))
    if unhealthy_reasons:
        return DoctorStatus.UNHEALTHY, degraded_reasons, unhealthy_reasons
    if degraded_reasons:
        return DoctorStatus.DEGRADED, degraded_reasons, ()
    return DoctorStatus.HEALTHY, (), ()


CI_CHECK_V3_SCHEMA_VERSION = "llm-wiki-ci-check/v3"

POLICY_SCHEMA = "llm-wiki-repository-health-policy/v1"
PREFLIGHT_SCHEMA = "llm-wiki-maintenance-preflight/v1"
POLICY_ID = "strict-repository-health/v1"
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{40}\Z")


class MaintenanceError(ValueError):
    """Maintenance evidence is absent, inconsistent or not bound to this candidate."""


def strict_json(raw: bytes) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise MaintenanceError("duplicate evidence field")
            result[key] = value
        return result

    def invalid(value):
        raise MaintenanceError("non-finite evidence number")

    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise MaintenanceError("invalid evidence JSON") from exc
    if not isinstance(value, dict):
        raise MaintenanceError("evidence must be an object")
    return value


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _binding(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "candidate_sha",
        "candidate_tree",
        "candidate_version",
        "concepts_total",
        "source_archive_sha256",
        "src_dir",
        "wiki_dir",
        "selection_fingerprint",
        "selection_inputs_hash",
        "live_source_hash",
        "knowledge_index_hash",
        "surface_index_hash",
        "evaluated_envelope_hash",
    }:
        raise MaintenanceError("binding fields do not match the contract")
    for key in ("candidate_sha", "candidate_tree"):
        if not isinstance(value[key], str) or not _SHA.fullmatch(value[key]):
            raise MaintenanceError("invalid candidate identity")
    for key in ("src_dir", "wiki_dir", "candidate_version"):
        if not isinstance(value[key], str) or not value[key]:
            raise MaintenanceError("binding scope must be explicit")
    if value["concepts_total"] is not None and (
        type(value["concepts_total"]) is not int or value["concepts_total"] < 0
    ):
        raise MaintenanceError("invalid bound concept inventory")
    for key in set(value) - {
        "candidate_sha",
        "candidate_tree",
        "candidate_version",
        "concepts_total",
        "src_dir",
        "wiki_dir",
    }:
        item = value[key]
        if item is not None and (
            not isinstance(item, str) or not _HASH.fullmatch(item)
        ):
            raise MaintenanceError("invalid binding commitment")
    return value


def strict_health_projection(
    health: Mapping[str, Any],
    *,
    selection_mismatch: bool = False,
    validate_full_report: bool = True,
) -> dict[str, Any]:
    """Reclassify validated sections using the standalone doctor's classifier."""
    if validate_full_report:
        from .ci_report import validate_doctor_payload

        validate_doctor_payload(
            health, expected_strict=False, source_selection_mismatch=selection_mismatch
        )
    result = copy.deepcopy(dict(health))
    status, degraded, unhealthy = classify_health_sections(
        strict=True,
        source_selection_mismatch=selection_mismatch,
        availability=health["availability"],
        freshness=health["freshness"],
        snapshot=health["snapshot_parity"],
        governance=health["governance"],
        drift=health["drift"],
        verification=health["verification_receipt"],
    )
    result.update(
        strict=True,
        status=status.value,
        exit_code={
            "healthy": 0,
            "degraded": 1,
            "unhealthy": 2,
            "absent": 3,
        }[status.value],
        degraded_reasons=list(degraded),
        unhealthy_reasons=list(unhealthy),
    )
    if validate_full_report:
        validate_doctor_payload(
            result, expected_strict=True, source_selection_mismatch=selection_mismatch
        )
    return result


def _admission_shape(report: Mapping[str, Any]) -> None:
    """Stdlib admission invariants for already producer-validated, hosted bytes.

    Full public-contract validation runs at production. Admission independently
    verifies every field used to admit a release, with the same policy builder
    and classifier; it never needs to import or execute the candidate package.
    """

    def require(condition, message):
        if not condition:
            raise MaintenanceError(message)

    require(
        set(report)
        in [
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
                "check_exit_code",
                "command_exit_code",
                "runtime",
            }
            | extra
            for extra in (set(), {"knowledge_summary"})
        ],
        "invalid CI admission envelope",
    )
    require(
        report["strict"] is True and report["knowledge_drift_gate"] is False,
        "invalid integrity policy",
    )
    require(
        type(report["ok"]) is bool and isinstance(report["issues"], list),
        "invalid integrity result",
    )
    require(
        type(report["issue_count"]) is int
        and report["issue_count"] == len(report["issues"]),
        "invalid issue count",
    )
    require(
        report["ok"] == (report["issue_count"] == 0),
        "copied integrity verdict disagrees",
    )
    require(
        type(report["check_exit_code"]) is int
        and report["check_exit_code"] == (0 if report["ok"] else 1),
        "invalid check exit",
    )
    health = report["knowledge_health"]
    require(
        isinstance(health, dict)
        and health.get("schema_version") == "llm-wiki-doctor/v3"
        and health.get("strict") is False,
        "invalid nested health version/policy",
    )
    require(
        (health["src_dir"], health["wiki_dir"])
        == (report["src_dir"], report["wiki_dir"]),
        "inconsistent nested scope",
    )
    details = health["health_details"]
    require(
        details["schema_version"] == "llm-wiki-health-details/v1",
        "unsupported health detail",
    )
    require(
        (details["scope"]["src_dir"], details["scope"]["wiki_dir"])
        == (report["src_dir"], report["wiki_dir"]),
        "inconsistent captured scope",
    )
    coverage = details["coverage"]
    for name in (
        "total",
        "modeled",
        "unmodeled",
        "evaluated",
        "comparison_attempted",
        "comparable",
    ):
        require(
            coverage[name] is None
            or type(coverage[name]) is int
            and coverage[name] >= 0,
            "invalid concept count",
        )
    outcome = coverage["outcomes"]
    states = {
        "current",
        "unknown",
        "basis-incompatible",
        "nonsemantic-source-change",
        "source-changed",
        "source-missing",
    }
    if outcome is not None:
        require(
            isinstance(outcome, dict) and set(outcome) == states,
            "invalid modeled outcomes",
        )
        require(
            all(type(n) is int and n >= 0 for n in outcome.values()),
            "invalid outcome count",
        )
        require(
            sum(outcome.values()) == coverage["modeled"]
            and coverage["total"] == coverage["modeled"] + coverage["unmodeled"],
            "coverage does not partition inventory",
        )
        require(
            coverage["evaluated"] == coverage["modeled"]
            and coverage["comparable"]
            == sum(
                outcome[name]
                for name in ("current", "nonsemantic-source-change", "source-changed")
            ),
            "comparison counts disagree",
        )
        require(
            coverage["comparison_attempted"]
            == coverage["modeled"] - outcome["unknown"],
            "attempt count disagrees",
        )
        expected = dict(outcome)
        expected["unknown"] += coverage["unmodeled"]
        require(
            health["freshness"]["counts_by_state"] == expected
            and health["freshness"]["concepts"] == coverage["total"]
            and health["freshness"]["evaluated"] is True,
            "freshness projection disagrees",
        )
    else:
        require(
            all(
                coverage[name] is None
                for name in ("evaluated", "comparison_attempted", "comparable")
            ),
            "unevaluated counts must be null",
        )
    require(type(details["snapshot"]["validated"]) is bool, "invalid snapshot proof")
    require(
        details["evaluation"]["state"]
        in {"evaluated", "partial", "failed", "unavailable", "not-evaluated"},
        "invalid evaluation state",
    )
    require(
        health["availability"]["state"]
        in {"ready", "degraded", "unsupported", "absent"},
        "invalid availability",
    )
    require(
        health["snapshot_parity"]["state"]
        in {"valid", "mixed", "invalid", "not-available"},
        "invalid parity",
    )
    governance = health["governance"]
    require(
        governance["state"] in {"valid", "invalid", "not-present", "not-available"},
        "invalid governance",
    )
    require(
        type(governance["expired_reviews"]) is int
        and governance["expired_reviews"] >= 0,
        "invalid review count",
    )
    if governance["state"] == "valid":
        require(
            governance["ledger"] == governance["projection"] == "valid"
            and governance["issue_count"] == 0,
            "inconsistent valid governance",
        )
    if governance["state"] == "not-present":
        require(
            governance["ledger"] == governance["projection"] == "not-present"
            and governance["issue_count"] == 0,
            "inconsistent absent governance",
        )
    verification = health["verification_receipt"]
    require(
        verification["state"]
        in {"valid", "failed", "invalid", "stale", "absent", "not-evaluated"},
        "invalid verification state",
    )
    if verification["state"] == "valid":
        require(
            verification["passed"] is True
            and verification["recorded_result"] == "passed",
            "inconsistent verification",
        )
    if verification["state"] in {"absent", "not-evaluated"}:
        require(
            verification["passed"] is None and verification["recorded_result"] is None,
            "absent verification carries a result",
        )
    drift = health["drift"]
    require(
        drift["state"]
        in {
            "current",
            "stale-confirmed",
            "indeterminate",
            "nonsemantic-change",
            "not-evaluated",
        },
        "invalid drift",
    )
    for key in (
        "confirmed_stale",
        "indeterminate",
        "nonsemantic_changes",
        "diagnostic_count",
    ):
        require(type(drift[key]) is int and drift[key] >= 0, "invalid drift counts")
    if drift["state"] == "current":
        require(
            not any(
                drift[k]
                for k in (
                    "confirmed_stale",
                    "indeterminate",
                    "nonsemantic_changes",
                    "diagnostic_count",
                )
            ),
            "current drift has findings",
        )


def derive_policy(
    report_bytes: bytes,
    preflight_bytes: bytes,
    *,
    binding: Mapping[str, Any],
    validate_full_report: bool = True,
) -> dict[str, Any]:
    """Return an auditable result; input reports never change integrity outcomes."""
    binding = _binding(binding)
    report = strict_json(report_bytes)
    if report.get("schema_version") != CI_CHECK_V3_SCHEMA_VERSION:
        raise MaintenanceError("repository health requires an explicit CI v3 report")
    exit_code = report.get("command_exit_code")
    if type(exit_code) is not int:
        raise MaintenanceError("report command exit code is missing or invalid")
    if validate_full_report:
        from .ci_report import validate_ci_check_payload

        validate_ci_check_payload(report, cli_exit=exit_code)
    _admission_shape(report)
    preflight = strict_json(preflight_bytes)
    if set(preflight) != {
        "schema_version",
        "status",
        "binding",
        "installed",
        "issues",
        "limitations",
        "remedy",
    }:
        raise MaintenanceError("invalid preflight envelope")
    if preflight["schema_version"] != PREFLIGHT_SCHEMA or preflight["status"] not in {
        "ready",
        "blocked",
    }:
        raise MaintenanceError("unsupported preflight result")
    if _binding(preflight["binding"]) != binding:
        raise MaintenanceError("preflight belongs to another candidate or scope")
    if not isinstance(preflight["issues"], list) or (
        preflight["status"] == "ready"
    ) != (not preflight["issues"]):
        raise MaintenanceError("preflight status does not match issues")
    installed = preflight["installed"]
    if preflight["status"] == "ready":
        if not isinstance(installed, dict) or set(installed) != {
            "version",
            "import_root",
            "implementation_hash",
            "editable",
        }:
            raise MaintenanceError(
                "ready preflight lacks installed implementation evidence"
            )
        if (
            installed["version"] != binding["candidate_version"]
            or type(installed["editable"]) is not bool
        ):
            raise MaintenanceError("preflight installed candidate mismatch")
        if (
            not isinstance(installed["import_root"], str)
            or not installed["import_root"]
            or not isinstance(installed["implementation_hash"], str)
            or not _HASH.fullmatch(installed["implementation_hash"])
        ):
            raise MaintenanceError("preflight implementation commitment is invalid")
    health = report["knowledge_health"]
    if (report["src_dir"], report["wiki_dir"]) != (
        binding["src_dir"],
        binding["wiki_dir"],
    ):
        raise MaintenanceError("report is not for the declared repository scope")
    details = health["health_details"]
    live_basis = details["basis"]["live"]
    if (
        live_basis is not None
        and live_basis["tool"]["version"] != binding["candidate_version"]
    ):
        raise MaintenanceError("report was evaluated by a different candidate version")
    selection = details["scope"]["selection"]
    actual = {
        **details["snapshot"],
        "selection_fingerprint": selection["fingerprint"],
        "selection_inputs_hash": selection["inputs_hash"],
    }
    for key in (
        "selection_fingerprint",
        "selection_inputs_hash",
        "live_source_hash",
        "knowledge_index_hash",
        "surface_index_hash",
        "evaluated_envelope_hash",
    ):
        if actual[key] != binding[key]:
            raise MaintenanceError(
                f"report {key} does not match captured preflight inputs"
            )
    strict = strict_health_projection(
        health,
        selection_mismatch=any(
            row["category"] == "source-selection-mismatch" for row in report["issues"]
        ),
        validate_full_report=validate_full_report,
    )
    reasons = []
    if preflight["status"] != "ready":
        reasons.append("preflight-blocked")
    if not report["ok"] or report["command_exit_code"] != 0:
        reasons.append("integrity-or-output-failed")
    if (
        details["basis"]["recorded"] is None
        or details["basis"]["live"] is None
        or details["basis"]["recorded"] != details["basis"]["live"]
    ):
        reasons.append("producer-basis-not-identical")
    if strict["status"] != "healthy":
        reasons.append("strict-health-" + strict["status"])
    if details["evaluation"]["state"] != "evaluated":
        reasons.append("incomplete-evaluation")
    if not details["snapshot"]["validated"]:
        reasons.append("snapshot-not-validated")
    if health["snapshot_parity"]["state"] != "valid":
        reasons.append("snapshot-parity-not-valid")
    if health["governance"]["state"] not in {"valid", "not-present"}:
        reasons.append("governance-not-validated")
    if health["verification_receipt"]["state"] not in {"valid", "absent"}:
        reasons.append("verification-not-validated")
    if selection["state"] not in {"legacy", "configured"}:
        reasons.append("selection-not-evaluated")
    if any(
        binding[key] is None
        for key in (
            "knowledge_index_hash",
            "surface_index_hash",
            "evaluated_envelope_hash",
            "live_source_hash",
        )
    ):
        reasons.append("missing-snapshot-binding")
    coverage = details["coverage"]
    if coverage["total"] != binding["concepts_total"]:
        raise MaintenanceError(
            "report concept total does not match the committed inventory"
        )
    if coverage["modeled"] is None or coverage["evaluated"] != coverage["modeled"]:
        reasons.append("modeled-inventory-not-evaluated")
    if not coverage["modeled"]:
        reasons.append("no-modeled-coverage")
    outcomes = coverage["outcomes"]
    if outcomes is None or any(
        count for state, count in outcomes.items() if state != "current"
    ):
        reasons.append("modeled-freshness-not-current")
    return {
        "schema_version": POLICY_SCHEMA,
        "policy": POLICY_ID,
        "binding": dict(binding),
        "report_sha256": digest(report_bytes),
        "preflight_sha256": digest(preflight_bytes),
        "status": "pass" if not reasons else "fail",
        "reasons": sorted(reasons),
        "strict_health": strict["status"],
        "coverage": copy.deepcopy(coverage),
        "evaluation": details["evaluation"]["state"],
    }


def verify_policy(
    receipt: object,
    report_bytes: bytes,
    preflight_bytes: bytes,
    *,
    binding: Mapping[str, Any],
    validate_full_report: bool = True,
) -> Mapping[str, Any]:
    """Recompute the complete receipt, rejecting copied verdicts and stale digests."""
    expected = derive_policy(
        report_bytes,
        preflight_bytes,
        binding=binding,
        validate_full_report=validate_full_report,
    )
    if json.dumps(receipt, sort_keys=True, allow_nan=False) != json.dumps(
        expected, sort_keys=True, allow_nan=False
    ):
        raise MaintenanceError("policy receipt does not match the evaluated inputs")
    return expected
