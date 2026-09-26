"""Render a GitHub job summary from the stable doctor JSON contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from llm_wiki_cli.services.ci_report import validate_doctor_payload
from llm_wiki_cli.services.contracts import DOCTOR_V3_SCHEMA_VERSION
from llm_wiki_cli.services.health_summary import (
    FRESHNESS_DISCLOSURE,
    detailed_health_rows,
    freshness_counts,
    health_policy,
    optional_status,
    reason_list,
    summary_cell,
)


SCHEMA_VERSION = "llm-wiki-doctor/v1"
DASHBOARD_RECEIPT_SCHEMA = "llm-wiki-doctor-dashboard/v1"
DASHBOARD_RECEIPT_V2_SCHEMA = "llm-wiki-doctor-dashboard/v2"
SUMMARY_MAX_BYTES = 8192
SUMMARY_MAX_LINES = 40
CELL_MAX_BYTES = 240
STATUS_SEVERITY = {
    "healthy": 0,
    "degraded": 1,
    "unhealthy": 2,
    "absent": 3,
}
FAIL_THRESHOLDS = {
    "degraded": 1,
    "unhealthy": 2,
}
FRESHNESS_STATES = frozenset(
    {
        "unknown",
        "current",
        "nonsemantic-source-change",
        "source-changed",
        "basis-incompatible",
        "source-missing",
    }
)
AVAILABILITY_STATES = frozenset({"ready", "absent", "degraded", "unsupported"})
SNAPSHOT_STATES = frozenset({"valid", "mixed", "invalid", "not-available"})
GOVERNANCE_STATES = frozenset({"valid", "invalid", "not-present", "not-available"})
GOVERNANCE_LEDGER_STATES = frozenset({"valid", "invalid", "not-present"})
GOVERNANCE_PROJECTION_STATES = frozenset(
    {"valid", "invalid", "not-present", "not-available"}
)
DRIFT_STATES = frozenset(
    {
        "current",
        "stale-confirmed",
        "indeterminate",
        "nonsemantic-change",
        "not-evaluated",
    }
)
VERIFICATION_STATES = frozenset(
    {"valid", "failed", "invalid", "stale", "absent", "not-evaluated"}
)
RECORDED_RESULTS = frozenset({"passed", "failed"})

REPORT_FIELDS = frozenset(
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
AVAILABILITY_FIELDS = frozenset({"state", "reason", "usable"})
FRESHNESS_FIELDS = frozenset({"evaluated", "disclosure", "concepts", "counts_by_state"})
SNAPSHOT_FIELDS = frozenset({"state", "issue_count", "reasons"})
GOVERNANCE_FIELDS = frozenset(
    {
        "state",
        "ledger",
        "projection",
        "expired_reviews",
        "issue_count",
        "reasons",
    }
)
DRIFT_FIELDS = frozenset(
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
VERIFICATION_FIELDS = frozenset({"state", "reason", "recorded_result", "passed"})


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    parser.add_argument("--fail-on", choices=sorted(FAIL_THRESHOLDS), required=True)
    parser.add_argument(
        "--doctor-exit-code",
        choices=range(4),
        required=True,
        type=int,
    )
    parser.add_argument(
        "--expected-strict",
        choices=("true", "false"),
        required=True,
    )
    parser.add_argument("--receipt")
    parser.add_argument("--evidence-artifact")
    return parser.parse_args()


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _required_object(
    value: object,
    field: str,
    expected: frozenset[str],
) -> Mapping[str, Any]:
    result = _object(value, field)
    missing = sorted(expected - set(result))
    if missing:
        raise ValueError(f"{field}.{missing[0]} is required")
    return result


def _exact_object(
    value: object,
    field: str,
    expected: frozenset[str],
) -> Mapping[str, Any]:
    result = _required_object(value, field, expected)
    unknown = sorted(set(result) - expected)
    if unknown:
        raise ValueError(f"{field}.{unknown[0]} is not supported")
    return result


def _enum(
    value: object,
    field: str,
    allowed: frozenset[str] | Mapping[str, int],
) -> str:
    result = _string(value, field)
    if result not in allowed:
        raise ValueError(f"{field} is unsupported")
    return result


def _boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _nullable_boolean(value: object, field: str) -> bool | None:
    if value is None:
        return None
    return _boolean(value, field)


def _nonnegative_integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return [_string(item, f"{field}[{index}]") for index, item in enumerate(value)]


def _freshness_counts(
    value: object,
    field: str,
) -> Mapping[str, Any] | None:
    if value is None:
        return None
    counts = _exact_object(value, field, FRESHNESS_STATES)
    for state in sorted(FRESHNESS_STATES):
        _nonnegative_integer(counts[state], f"{field}.{state}")
    return counts


def _validate_availability(value: object) -> None:
    section = _required_object(value, "report.availability", AVAILABILITY_FIELDS)
    state = _enum(
        section["state"],
        "report.availability.state",
        AVAILABILITY_STATES,
    )
    _string(section["reason"], "report.availability.reason")
    usable = _boolean(section["usable"], "report.availability.usable")
    expected_usable = state in {"ready", "degraded"}
    if usable is not expected_usable:
        raise ValueError(
            "report.availability.usable does not match report.availability.state"
        )


def _validate_freshness(value: object) -> None:
    section = _required_object(value, "report.freshness", FRESHNESS_FIELDS)
    evaluated = _boolean(section["evaluated"], "report.freshness.evaluated")
    _string(section["disclosure"], "report.freshness.disclosure")
    concepts = _nonnegative_integer(section["concepts"], "report.freshness.concepts")
    counts = _freshness_counts(
        section["counts_by_state"],
        "report.freshness.counts_by_state",
    )
    if evaluated != (counts is not None):
        raise ValueError(
            "report.freshness.counts_by_state does not match report.freshness.evaluated"
        )
    if counts is not None and sum(int(value) for value in counts.values()) != concepts:
        raise ValueError(
            "report.freshness.concepts does not match report.freshness.counts_by_state"
        )


def _validate_snapshot(value: object) -> None:
    section = _required_object(value, "report.snapshot_parity", SNAPSHOT_FIELDS)
    _enum(
        section["state"],
        "report.snapshot_parity.state",
        SNAPSHOT_STATES,
    )
    _nonnegative_integer(
        section["issue_count"],
        "report.snapshot_parity.issue_count",
    )
    _string_list(section["reasons"], "report.snapshot_parity.reasons")


def _validate_governance(value: object) -> None:
    section = _required_object(value, "report.governance", GOVERNANCE_FIELDS)
    _enum(section["state"], "report.governance.state", GOVERNANCE_STATES)
    _enum(
        section["ledger"],
        "report.governance.ledger",
        GOVERNANCE_LEDGER_STATES,
    )
    _enum(
        section["projection"],
        "report.governance.projection",
        GOVERNANCE_PROJECTION_STATES,
    )
    _nonnegative_integer(
        section["expired_reviews"],
        "report.governance.expired_reviews",
    )
    _nonnegative_integer(
        section["issue_count"],
        "report.governance.issue_count",
    )
    _string_list(section["reasons"], "report.governance.reasons")


def _validate_drift(value: object) -> None:
    section = _required_object(value, "report.drift", DRIFT_FIELDS)
    state = _enum(section["state"], "report.drift.state", DRIFT_STATES)
    for field in (
        "confirmed_stale",
        "indeterminate",
        "nonsemantic_changes",
        "diagnostic_count",
    ):
        _nonnegative_integer(section[field], f"report.drift.{field}")
    counts = _freshness_counts(
        section["counts_by_state"],
        "report.drift.counts_by_state",
    )
    if (state == "not-evaluated") != (counts is None):
        raise ValueError(
            "report.drift.counts_by_state does not match report.drift.state"
        )
    _string_list(section["reasons"], "report.drift.reasons")


def _validate_verification(value: object) -> None:
    section = _required_object(
        value,
        "report.verification_receipt",
        VERIFICATION_FIELDS,
    )
    _enum(
        section["state"],
        "report.verification_receipt.state",
        VERIFICATION_STATES,
    )
    _string(section["reason"], "report.verification_receipt.reason")
    recorded = section["recorded_result"]
    if recorded is not None:
        _enum(
            recorded,
            "report.verification_receipt.recorded_result",
            RECORDED_RESULTS,
        )
    _nullable_boolean(
        section["passed"],
        "report.verification_receipt.passed",
    )


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value!r} is not supported")


def load_report(
    path: str | Path,
    *,
    doctor_exit_code: int,
    expected_strict: bool | None = None,
) -> Mapping[str, Any]:
    """Load and strictly validate a supported health doctor contract."""

    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f"doctor report is not readable JSON: {exc}") from exc
    return _validate_report_bytes(raw, doctor_exit_code=doctor_exit_code, expected_strict=expected_strict)


def _validate_report_bytes(
    raw: bytes, *, doctor_exit_code: int, expected_strict: bool | None,
) -> Mapping[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_strict_json_object, parse_constant=_reject_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"doctor report is not readable JSON: {exc}") from exc
    report = _required_object(payload, "report", REPORT_FIELDS)
    if report.get("schema_version") not in {SCHEMA_VERSION, DOCTOR_V3_SCHEMA_VERSION}:
        raise ValueError("report.schema_version must be a supported health doctor version")
    status = _enum(report["status"], "report.status", STATUS_SEVERITY)
    exit_code = report.get("exit_code")
    if (
        isinstance(exit_code, bool)
        or not isinstance(exit_code, int)
        or exit_code != STATUS_SEVERITY[status]
    ):
        raise ValueError("report.exit_code does not match report.status")
    if (
        isinstance(doctor_exit_code, bool)
        or not isinstance(doctor_exit_code, int)
        or doctor_exit_code not in STATUS_SEVERITY.values()
    ):
        raise ValueError("doctor_exit_code must be an integer from 0 through 3")
    if exit_code != doctor_exit_code:
        raise ValueError(
            "report.exit_code does not match the captured doctor process exit code"
        )
    strict = _boolean(report["strict"], "report.strict")
    if expected_strict is not None and strict is not expected_strict:
        raise ValueError("report.strict does not match the requested strict mode")
    _string(report["wiki_dir"], "report.wiki_dir")
    _string(report["src_dir"], "report.src_dir")
    _validate_availability(report["availability"])
    _validate_freshness(report["freshness"])
    _validate_snapshot(report["snapshot_parity"])
    _validate_governance(report["governance"])
    _validate_drift(report["drift"])
    _validate_verification(report["verification_receipt"])
    _string_list(report["degraded_reasons"], "report.degraded_reasons")
    _string_list(report["unhealthy_reasons"], "report.unhealthy_reasons")
    validate_doctor_payload(
        report,
        expected_strict=strict,
        allow_additive=True,
    )
    return report


def _cell(value: object) -> str:
    return summary_cell(value, CELL_MAX_BYTES)


def render_summary(
    report: Mapping[str, Any], *, fail_on: str | None = None,
    report_name: str = "doctor.json", evidence_artifact: str | None = None,
) -> str:
    """Return a compact Markdown table without interpreting human text."""

    availability = _object(report["availability"], "report.availability")
    freshness = _object(report["freshness"], "report.freshness")
    snapshot = _object(report["snapshot_parity"], "report.snapshot_parity")
    governance = _object(report["governance"], "report.governance")
    drift = _object(report["drift"], "report.drift")
    verification = _object(
        report["verification_receipt"],
        "report.verification_receipt",
    )
    if fail_on is not None and fail_on not in FAIL_THRESHOLDS:
        raise ValueError("unsupported dashboard failure threshold")
    _string(report_name, "report name")
    if evidence_artifact is not None:
        _string(evidence_artifact, "evidence artifact")
    rows = (
        ("Overall", report["status"]),
        ("Wiki scope", report["wiki_dir"]),
        ("Source scope", report["src_dir"]),
        ("Health classification", health_policy(report["strict"])),
        ("Action failure threshold", (
            "not supplied (classification only)" if fail_on is None else
            "degraded, unhealthy or absent" if fail_on == "degraded" else
            "unhealthy or absent"
        )),
        ("Availability", availability.get("state", "unknown")),
        ("Freshness", freshness.get("disclosure", "unknown")),
        ("Freshness states", freshness_counts(freshness["counts_by_state"])),
        ("Snapshot parity", snapshot.get("state", "unknown")),
        ("Governance", optional_status(governance["state"], absent="not-present")),
        (
            "Drift",
            (
                f"{drift.get('state', 'unknown')} "
                f"(confirmed={drift.get('confirmed_stale', 0)}, "
                f"indeterminate={drift.get('indeterminate', 0)})"
            ),
        ),
        ("Verification receipt", optional_status(verification["state"], absent="absent")),
        ("Drift diagnostics", drift["diagnostic_count"]),
        ("Drift reasons", reason_list(drift["reasons"])),
        ("Health reasons", reason_list(sorted(set(
            report["unhealthy_reasons"] + report["degraded_reasons"]
        )))),
    )
    rows += tuple(detailed_health_rows(report))
    lines = [
        "## LLM Wiki doctor dashboard",
        "",
        (
            "> Diagnostic knowledge-health dashboard only. It does not run or "
            "replace `llm-wiki ci-check`; the blocking integrity context remains "
            "`LLM Wiki integrity`."
        ),
        "",
        "| Check | Result |",
        "|---|---|",
        *(f"| {_cell(label)} | `{_cell(value)}` |" for label, value in rows),
        "",
        FRESHNESS_DISCLOSURE,
        "",
        (
            "Captured coverage, primary concept reasons and producer versions are available in the full v3 JSON."
            if report["schema_version"] == DOCTOR_V3_SCHEMA_VERSION else
            "Doctor v1 supplies no per-reason counts, recovery hints or producer versions."
        ),
        "",
        f"Full JSON: `{_cell(report_name)}`. Text marked `[truncated]` is abbreviated.",
    ]
    if evidence_artifact is not None:
        lines.append(f"Evidence artifact: `{_cell(evidence_artifact)}`.")
    rendered = "\n".join(lines) + "\n\n"
    if (
        len(rendered.splitlines()) > SUMMARY_MAX_LINES
        or len(rendered.encode("utf-8")) > SUMMARY_MAX_BYTES
    ):
        raise ValueError("rendered summary exceeds its fixed bounds")
    return rendered


def _append(path: str | None, content: str) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8", newline="\n") as output:
        output.write(content)


def _write_receipt(
    path: str | None,
    *,
    report_path: str | Path,
    report: Mapping[str, Any],
    fail_on: str,
    doctor_exit_code: int,
    dashboard_exit_code: int,
) -> None:
    if not path:
        return
    target = Path(path)
    if target.exists() or target.is_symlink():
        raise ValueError("dashboard receipt path must not already exist")
    report_bytes = Path(report_path).read_bytes()
    captured = _validate_report_bytes(report_bytes, doctor_exit_code=doctor_exit_code, expected_strict=report["strict"])
    if captured != report:
        raise ValueError("doctor report changed after validation")
    receipt = {
        "schema_version": DASHBOARD_RECEIPT_V2_SCHEMA if report["schema_version"] == DOCTOR_V3_SCHEMA_VERSION else DASHBOARD_RECEIPT_SCHEMA,
        "report_schema_version": report["schema_version"],
        "status": report["status"],
        "strict": report["strict"],
        "fail_on": fail_on,
        "doctor_exit_code": doctor_exit_code,
        "dashboard_exit_code": dashboard_exit_code,
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
    }
    target.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    args = _arguments()
    try:
        report = load_report(
            args.report,
            doctor_exit_code=args.doctor_exit_code,
            expected_strict=args.expected_strict == "true",
        )
        summary = render_summary(
            report, fail_on=args.fail_on, report_name=Path(args.report).name,
            evidence_artifact=args.evidence_artifact,
        )
    except ValueError as exc:
        raise SystemExit(f"Invalid doctor JSON contract: {exc}") from exc

    _append(os.environ.get("GITHUB_STEP_SUMMARY"), summary)
    _append(
        os.environ.get("GITHUB_OUTPUT"),
        f"status={report['status']}\n",
    )
    threshold = FAIL_THRESHOLDS[args.fail_on]
    dashboard_exit = int(STATUS_SEVERITY[str(report["status"])] >= threshold)
    try:
        _write_receipt(
            args.receipt,
            report_path=args.report,
            report=report,
            fail_on=args.fail_on,
            doctor_exit_code=args.doctor_exit_code,
            dashboard_exit_code=dashboard_exit,
        )
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Could not write dashboard receipt: {exc}") from exc
    return dashboard_exit


if __name__ == "__main__":
    raise SystemExit(main())
