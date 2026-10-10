"""Frozen prospective triage acceptance around the source-grounded row scorer.

The caller retains the independently frozen contract and control-ID commitments.
Captures use the fixed scorer's schema, adding ``limit``, ``contract_sha256`` and
``source_plan_sha256`` and authenticated ``read_only=True`` to their envelopes.
Queue responses must retain ``advisory=True`` and captures must have no error.
Split campaign identities are retained
unchanged; pooled results sum their scored occurrences without rebinding reviews.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from tests.developer_value.triage_oracle import (
    OPERATIONS,
    commitment,
    resolve_review,
    score_campaign,
)


SPLITS = ("development", "confirmation")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _records(value: Any, name: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(v, Mapping) for v in value):
        raise ValueError(f"{name} must be a list of records.")
    return value


def _contract(
    value: Mapping[str, Any], expected_hash: str
) -> tuple[
    dict[str, Mapping[str, Any]], list[Mapping[str, Any]], list[Mapping[str, Any]]
]:
    if commitment(value) != expected_hash:
        raise ValueError("Frozen contract commitment mismatch.")
    if (
        type(value.get("schema_version")) is not int
        or value["schema_version"] != 1
        or value.get("threshold") != 0.8
        or type(value.get("required_change_coverage")) not in (int, float)
        or value.get("required_change_coverage") != 1.0
        or type(value.get("limit")) is not int
        or value["limit"] != 100
    ):
        raise ValueError("The fixed 0.8/1.0/100 acceptance policy is required.")
    plan = value.get("source_plan")
    if (
        not isinstance(plan, Mapping)
        or not plan
        or value.get("source_plan_sha256") != commitment(plan)
    ):
        raise ValueError("Frozen source plan commitment mismatch.")
    cases = _records(value.get("cases"), "cases")
    if not cases or any(
        not all(_text(c.get(k)) for k in ("case_id", "family", "fixture_type"))
        or c.get("split") not in SPLITS
        for c in cases
    ):
        raise ValueError("Each case needs an identity, split, family and fixture type.")
    case_index = {c["case_id"]: c for c in cases}
    if len(case_index) != len(cases) or {c["split"] for c in cases} != set(SPLITS):
        raise ValueError("Cases must be unique and include both frozen splits.")
    schedule = _records(value.get("schedule"), "schedule")
    if not schedule or any(
        not _text(s.get("case_id"))
        or s["case_id"] not in case_index
        or not _text(s.get("stage"))
        for s in schedule
    ):
        raise ValueError("Every scheduled stage needs a declared case and identity.")
    scheduled = [(s["case_id"], s["stage"]) for s in schedule]
    if len(set(scheduled)) != len(scheduled) or {k[0] for k in scheduled} != set(
        case_index
    ):
        raise ValueError(
            "The full schedule must include every case exactly once per stage."
        )
    obligations = _records(
        value.get("required_owner_actions"), "required_owner_actions"
    )
    if not obligations or any(
        (o.get("case_id"), o.get("stage")) not in scheduled
        or not _text(o.get("owner"))
        or not _text(o.get("operation"))
        or o.get("operation") not in OPERATIONS
        for o in obligations
    ):
        raise ValueError(
            "Required actions must identify scheduled owners and operations."
        )
    keys = [(o["case_id"], o["stage"], o["owner"], o["operation"]) for o in obligations]
    if len(set(keys)) != len(keys) or any(
        not any(case_index[o["case_id"]]["split"] == split for o in obligations)
        for split in SPLITS
    ):
        raise ValueError("Required actions must be unique and present in both splits.")
    return case_index, schedule, obligations


def _totals(
    rows: Sequence[Mapping[str, Any]], obligations: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    counts = Counter(r["label"] for r in rows)
    required = {
        (o["case_id"], o["stage"], o["owner"], o["operation"]) for o in obligations
    }
    covered = {
        (r["case_id"], r["stage"], a["owner"], a["operation"])
        for r in rows
        for a in r["supported_actions"]
    } & required
    return {
        "actionable": counts["actionable"],
        "nonactionable": counts["nonactionable"],
        "unknown": counts["unknown"],
        "denominator": len(rows),
        "fraction": counts["actionable"] / len(rows) if rows else None,
        "required_count": len(required),
        "covered_count": len(covered),
        "coverage": len(covered) / len(required) if required else None,
        "missed": [list(k) for k in sorted(required - covered)],
    }


def _breakdown(
    cases: Mapping[str, Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    obligations: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in ("case_id", "family", "fixture_type"):
        result[name] = {}
        for group in sorted({c[name] for c in cases.values()}):
            selected = {ident for ident, case in cases.items() if case[name] == group}
            result[name][group] = _totals(
                [r for r in rows if r["case_id"] in selected],
                [o for o in obligations if o["case_id"] in selected],
            )
    return result


def _variability(breakdown: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    result = {}
    for name, groups in breakdown.items():
        fractions = [
            v["fraction"] for v in groups.values() if v["fraction"] is not None
        ]
        coverages = [
            v["coverage"] for v in groups.values() if v["coverage"] is not None
        ]
        result[name] = {
            "minimum_fraction": min(fractions) if fractions else None,
            "maximum_fraction": max(fractions) if fractions else None,
            "minimum_coverage": min(coverages) if coverages else None,
            "zero_row_groups": [g for g, v in groups.items() if not v["denominator"]],
        }
    return result


def _diagnostic_evidence(
    capture: dict[str, Any], issues: list[str], rejected: list[dict[str, Any]]
) -> None:
    """Make malformed submissions safe to score without changing stored inputs."""
    response = capture.get("response")
    if isinstance(response, Mapping) and isinstance(response.get("items"), list):
        if any(
            not isinstance(item, Mapping) or not _text(item.get("owner"))
            for item in response["items"]
        ):
            issues.append("invalid-returned-owner")
    capsules, resolutions = capture.get("capsules"), capture.get("resolutions")
    if not isinstance(capsules, Mapping) or not isinstance(resolutions, Mapping):
        return
    safe_resolutions = dict(resolutions)
    for ident, resolution in resolutions.items():
        capsule = capsules.get(ident)
        if not isinstance(capsule, Mapping) or not isinstance(resolution, Mapping):
            continue
        reason = None
        if not _text(capsule.get("owner")):
            reason = "invalid-capsule-owner"
        else:
            try:
                checked = resolve_review(
                    capsule,
                    resolution.get("reviews", []),
                    resolution.get("adjudication"),
                )
                if not checked["valid_reviews"]:
                    reason = "invalid-source-review"
            except (TypeError, ValueError, KeyError, IndexError, AttributeError):
                reason = "malformed-source-review"
        if reason:
            issues.append(reason)
            rejected.append(
                {
                    "case_id": capture.get("case_id"),
                    "stage": capture.get("stage"),
                    "row_id": ident,
                    "reason": reason,
                    "submission_sha256": commitment(resolution),
                }
            )
            safe_resolutions[ident] = {"reviews": []}
    capture["resolutions"] = safe_resolutions


def score_acceptance(
    campaign_ids: Mapping[str, str],
    contract: Mapping[str, Any],
    contract_sha256: str,
    captures: Sequence[Mapping[str, Any]],
    controls: Sequence[Mapping[str, Any]],
    *,
    control_ids: Sequence[str],
    control_ids_sha256: str,
) -> dict[str, Any]:
    """Require both split gates, fresh independent row evidence and all controls.

    Invalid frozen policy inputs or non-record containers raise ``ValueError``.
    Invalid observations return a failed report, preserving every scored
    occurrence. Invalid capture identities are normalized only for diagnostic
    scoring; their original identities are retained in the failed report.
    Controls must carry a nonempty ``evidence`` mapping and its commitment, plus
    ``receipt_sha256`` over the entire receipt excluding that hash itself.
    """
    cases, schedule, obligations = _contract(contract, contract_sha256)
    if set(campaign_ids) != set(SPLITS) or not all(
        _text(campaign_ids[s]) for s in SPLITS
    ):
        raise ValueError("Both original split campaign identities are required.")
    declared = list(control_ids)
    if (
        not declared
        or not all(_text(c) for c in declared)
        or len(set(declared)) != len(declared)
        or commitment(declared) != control_ids_sha256
    ):
        raise ValueError(
            "Unique separately frozen control IDs and commitment are required."
        )
    issues: list[str] = []
    plan_hash = contract["source_plan_sha256"]
    invalid_identities = []
    rejected_evidence: list[dict[str, Any]] = []
    normalized_captures = []
    for index, capture in enumerate(captures):
        if not isinstance(capture, Mapping):
            raise ValueError("Captures must be records.")
        normalized = dict(capture)
        for field in ("case_id", "stage"):
            if not _text(capture.get(field)):
                invalid_identities.append(
                    {"index": index, "field": field, "value": capture.get(field)}
                )
                normalized[field] = f"invalid-capture-{index}-{field}"
                issues.append("invalid-capture-identity")
        _diagnostic_evidence(normalized, issues, rejected_evidence)
        normalized_captures.append(normalized)
    captures = normalized_captures
    submitted_controls = list(controls)
    invalid_controls = []
    normalized_controls = []
    for index, control in enumerate(controls):
        if not isinstance(control, Mapping):
            raise ValueError("Controls must be records.")
        normalized_control = dict(control)
        if not _text(control.get("control_id")):
            invalid_controls.append(
                {"index": index, "value": control.get("control_id")}
            )
            normalized_control["control_id"] = f"invalid-control-{index}"
            issues.append("invalid-control-identity")
        normalized_controls.append(normalized_control)
    controls = normalized_controls
    expected = Counter((s["case_id"], s["stage"]) for s in schedule)
    observed = Counter((c.get("case_id"), c.get("stage")) for c in captures)
    if observed != expected:
        issues.append("incomplete-or-extra-schedule")
    for capture in captures:
        if capture.get("read_only") is not True:
            issues.append("capture-not-read-only")
        if capture.get("error") is not None:
            issues.append("capture-error")
        if type(capture.get("limit")) is not int or capture["limit"] != 100:
            issues.append("wrong-capture-limit")
        response = capture.get("response")
        if not isinstance(response, Mapping) or response.get("advisory") is not True:
            issues.append("non-advisory-response")
        if (
            isinstance(response, Mapping)
            and isinstance(response.get("items"), list)
            and len(response["items"]) > 100
        ):
            issues.append("capture-limit-exceeded")
        if capture.get("contract_sha256") != contract_sha256:
            issues.append("capture-contract-commitment-mismatch")
        if capture.get("source_plan_sha256") != plan_hash:
            issues.append("capture-source-plan-commitment-mismatch")
    splits: dict[str, dict[str, Any]] = {}
    independent = True
    for split in SPLITS:
        selected = {ident for ident, case in cases.items() if case["split"] == split}
        split_captures = [
            c
            for c in captures
            if c.get("case_id") in selected
            or (split == "development" and c.get("case_id") not in cases)
        ]
        result = score_campaign(
            campaign_ids[split],
            [s for s in schedule if s["case_id"] in selected],
            [o for o in obligations if o["case_id"] in selected],
            split_captures,
        )
        for capture in split_captures:
            capsules = capture.get("capsules", {})
            resolutions = capture.get("resolutions", {})
            for row in result["rows"]:
                if (row["case_id"], row["stage"]) != (
                    capture.get("case_id"),
                    capture.get("stage"),
                ):
                    continue
                capsule = (
                    capsules.get(row["row_id"])
                    if isinstance(capsules, Mapping)
                    else None
                )
                resolution = (
                    resolutions.get(row["row_id"])
                    if isinstance(resolutions, Mapping)
                    else None
                )
                checked = None
                if (
                    isinstance(capsule, Mapping)
                    and capsule.get("row_id") == row["row_id"]
                    and capsule.get("case_id") == capture.get("case_id")
                    and capsule.get("stage") == capture.get("stage")
                    and isinstance(resolution, Mapping)
                ):
                    checked = resolve_review(
                        capsule,
                        resolution.get("reviews", []),
                        resolution.get("adjudication"),
                    )
                if (
                    not checked
                    or not checked["valid_reviews"]
                    or not checked["reviewer_independence"]
                ):
                    independent = False
                    issues.append(f"missing-independent-review:{row['row_id']}")
        splits[split] = result
        if not result["passed"]:
            issues.append(f"failed-{split}-gate")
    seen_controls = Counter(c.get("control_id") for c in controls)
    if seen_controls != Counter(declared):
        issues.append("missing-extra-or-duplicate-controls")
    for control in controls:
        ident = control.get("control_id")
        evidence = control.get("evidence")
        payload = {k: v for k, v in control.items() if k != "receipt_sha256"}
        if (
            control.get("passed") is not True
            or control.get("read_only") is not True
            or control.get("invented_authority") is not False
            or control.get("contract_sha256") != contract_sha256
            or control.get("source_plan_sha256") != plan_hash
            or not isinstance(evidence, Mapping)
            or not evidence
            or control.get("evidence_sha256") != commitment(evidence)
            or control.get("receipt_sha256") != commitment(payload)
        ):
            issues.append(f"invalid-control:{ident}")
    rows = [r for s in SPLITS for r in splits[s]["rows"]]
    pooled = _totals(rows, obligations)
    pooled["passed"] = bool(
        pooled["denominator"]
        and pooled["actionable"] * 5 >= pooled["denominator"] * 4
        and pooled["coverage"] == 1.0
        and all(not splits[s]["issues"] for s in SPLITS)
    )
    breakdown = _breakdown(cases, rows, obligations)
    split_breakdown = {
        split: _breakdown(
            {ident: c for ident, c in cases.items() if c["split"] == split},
            splits[split]["rows"],
            [o for o in obligations if cases[o["case_id"]]["split"] == split],
        )
        for split in SPLITS
    }
    stages = []
    zero_rows = []
    for stage in schedule:
        key = (stage["case_id"], stage["stage"])
        totals = _totals(
            [r for r in rows if (r["case_id"], r["stage"]) == key],
            [o for o in obligations if (o["case_id"], o["stage"]) == key],
        )
        stages.append(
            {
                **stage,
                "split": cases[stage["case_id"]]["split"],
                "observed": observed[key] == 1,
                **totals,
            }
        )
        if not totals["denominator"]:
            zero_rows.append(stages[-1])
    return {
        "contract_sha256": contract_sha256,
        "source_plan_sha256": plan_hash,
        "control_ids_sha256": control_ids_sha256,
        "campaign_ids": dict(campaign_ids),
        "splits": splits,
        "pooled": pooled,
        "breakdown": breakdown,
        "split_breakdown": split_breakdown,
        "stages": stages,
        "zero_row_stages": zero_rows,
        "worst_case_variability": _variability(breakdown),
        "split_worst_case_variability": {
            s: _variability(split_breakdown[s]) for s in SPLITS
        },
        "reviewer_independence": independent and bool(rows),
        "controls": submitted_controls,
        "invalid_capture_identities": invalid_identities,
        "invalid_control_identities": invalid_controls,
        "rejected_evidence": rejected_evidence,
        "issues": sorted(set(issues)),
        "passed": not issues and all(splits[s]["passed"] for s in SPLITS),
    }
