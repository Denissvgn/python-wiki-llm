"""Provider labels cannot substitute for occurrence-specific source review."""

from copy import deepcopy
from hashlib import sha256

import pytest

from tests.developer_value.triage_oracle import (
    commitment,
    occurrence_id,
    resolve_review,
    review_valid,
    score_campaign,
)


def packet(row_id, stage="after-edit", owner="entities/Policy.md:Policy"):
    texts = {
        "before.py": ("source", "return values[:3]\n"),
        "after.py": ("source", "return values[-3:]\n"),
        "page.md": ("prose", "Return the first three values.\n"),
        "ownership.json": ("ownership", owner + "\n"),
        "task.txt": ("task", "Correct the claim after the source edit.\n"),
    }
    return {
        "row_id": row_id,
        "case_id": "owned",
        "stage": stage,
        "owner": owner,
        "artifacts": {
            p: {"kind": kind, "text": text, "sha256": sha256(text.encode()).hexdigest()}
            for p, (kind, text) in texts.items()
        },
    }


def judgment(capsule, label="actionable", role="reviewer-a"):
    return {
        "row_id": capsule["row_id"],
        "capsule_manifest_sha256": commitment(capsule),
        "actor": {
            "agent_id": "same-root",
            "session_id": "same-informed-session",
            "role": role,
            "fresh_no_fork": False,
        },
        "visibility": {
            "provider_labels_seen": False,
            "prior_reviews_seen": role != "reviewer-a",
            "oracle_results_seen": False,
        },
        "label": label,
        "proposed_action": "Replace the first-three claim with last-three selection.",
        "completion_condition": "The description agrees with the cited slicing operation.",
        "disconfirming_condition": "A different stage/source slice or owner would reject this conclusion.",
        "rationale": "The unchanged basis is adequate for this negative control.",
        "uncertainty_reason": "Required stage evidence is missing."
        if label == "unknown"
        else None,
        "supported_actions": [{"owner": capsule["owner"], "operation": "revise-claim"}]
        if label == "actionable"
        else [],
        "evidence_citations": [
            {
                "artifact": p,
                "sha256": a["sha256"],
                "first_line": 1,
                "last_line": len(a["text"].splitlines()),
                "quote": a["text"].rstrip("\n"),
            }
            for p, a in capsule["artifacts"].items()
        ],
        "limitations": ["Same-agent informed review; no reviewer independence."],
    }


def capture(labels=("actionable",), stage="after-edit", items=None):
    response = {
        "items": items
        or [
            {"owner": "entities/Policy.md:Policy", "provider_label": "actionable"}
            for _ in labels
        ],
        "total": len(labels),
        "returned": len(labels),
        "omitted": 0,
        "truncated": False,
    }
    h = commitment(response)
    value = {
        "case_id": "owned",
        "stage": stage,
        "response": response,
        "response_sha256": h,
        "capsules": {},
        "resolutions": {},
    }
    for index, label in enumerate(labels):
        ident = occurrence_id("trial", "owned", stage, h, index)
        capsule = packet(ident, stage, response["items"][index]["owner"])
        value["capsules"][ident] = capsule
        value["resolutions"][ident] = {
            "reviews": [
                judgment(capsule, label),
                judgment(capsule, label, "reviewer-b"),
            ]
        }
    return value


def score(captures, obligations=None, schedule=None):
    return score_campaign(
        "trial",
        schedule or [{"case_id": "owned", "stage": "after-edit"}],
        obligations
        if obligations is not None
        else [
            {
                "case_id": "owned",
                "stage": "after-edit",
                "owner": "entities/Policy.md:Policy",
                "operation": "revise-claim",
            }
        ],
        captures,
    )


def test_supported_reviews_pass_without_claiming_reviewer_independence():
    c = capture()
    result = score([c])
    assert result["passed"] and result["denominator"] == result["covered_count"] == 1
    capsule = next(iter(c["capsules"].values()))
    resolved = resolve_review(capsule, next(iter(c["resolutions"].values()))["reviews"])
    assert not resolved["reviewer_independence"] and resolved["agreement"]


@pytest.mark.parametrize("labels", [("nonactionable",) * 3, ("unknown",) * 3])
def test_all_informational_or_unavailable_rows_stay_in_denominator(labels):
    result = score([capture(labels)])
    assert (
        result["denominator"] == 3
        and result["actionable"] == 0
        and not result["passed"]
    )


def test_provider_self_labels_without_source_reviews_earn_no_credit():
    c = capture()
    c["resolutions"] = {}
    result = score([c])
    assert (
        result["unknown"] == 1 and result["covered_count"] == 0 and not result["passed"]
    )


def test_exact_owner_action_required_not_just_high_fraction_or_same_page():
    result = score(
        [capture()],
        obligations=[
            {
                "case_id": "owned",
                "stage": "after-edit",
                "owner": "entities/Policy.md:Policy",
                "operation": "inspect-pending-mapping",
            }
        ],
    )
    assert (
        result["fraction"] == 1
        and result["covered_count"] == 0
        and not result["passed"]
    )


def test_duplicate_occurrences_are_counted_with_only_first_action_credited():
    result = score([capture(("actionable", "actionable"))])
    assert (
        result["denominator"] == 2
        and result["actionable"] == result["nonactionable"] == 1
    )
    assert not result["passed"]
    assert len({r["row_id"] for r in result["rows"]}) == 2


def test_pending_action_across_stages_is_not_deduplicated():
    stages = ["after-edit", "after-sync", "after-restart"]
    schedule = [{"case_id": "owned", "stage": s} for s in stages]
    obligations = [
        {**s, "owner": "entities/Policy.md:Policy", "operation": "revise-claim"}
        for s in schedule
    ]
    result = score([capture(stage=s) for s in stages], obligations, schedule)
    assert (
        result["denominator"] == result["actionable"] == result["covered_count"] == 3
        and result["passed"]
    )


def test_acknowledged_unchanged_stage_cannot_borrow_earlier_label():
    result = score(
        [capture(stage="after-edit"), capture(("nonactionable",), "after-sync")],
        schedule=[
            {"case_id": "owned", "stage": s} for s in ("after-edit", "after-sync")
        ],
    )
    assert (
        result["denominator"] == 2
        and result["fraction"] == 0.5
        and not result["passed"]
    )


@pytest.mark.parametrize("kind", ["truncated", "count", "commitment", "missing-stage"])
def test_incomplete_capture_cannot_pass_by_shrinking_denominator(kind):
    c = capture()
    if kind == "truncated":
        c["response"].update(total=2, omitted=1, truncated=True)
    elif kind == "count":
        c["response"]["returned"] = 0
    elif kind == "commitment":
        c["response_sha256"] = "wrong"
    result = score([] if kind == "missing-stage" else [c])
    assert result["issues"] and not result["passed"]


def test_all_empty_output_has_null_fraction_and_cannot_pass():
    result = score([capture(())], obligations=[])
    assert (
        result["denominator"] == 0
        and result["fraction"] is None
        and not result["passed"]
    )


@pytest.mark.parametrize(
    "field", ["sha256", "quote", "first_line", "owner", "completion", "provider"]
)
def test_invalid_review_support_degrades_to_unknown(field):
    c = capture()
    record = next(iter(c["resolutions"].values()))["reviews"][0]
    if field in {"sha256", "quote", "first_line"}:
        record["evidence_citations"][0][field] = "bad"
    elif field == "owner":
        record["supported_actions"][0]["owner"] = "another-owner"
    elif field == "completion":
        record["completion_condition"] = ""
    else:
        record["visibility"]["provider_labels_seen"] = True
    result = score([c])
    assert result["unknown"] == 1 and not result["passed"]


def test_disagreement_requires_cited_hash_bound_adjudication():
    c = capture()
    capsule = next(iter(c["capsules"].values()))
    records = next(iter(c["resolutions"].values()))
    records["reviews"][1] = judgment(capsule, "nonactionable", "reviewer-b")
    assert score([c])["unknown"] == 1
    adjudication = judgment(capsule, role="adjudicator")
    adjudication["adjudication"] = {
        "review_a_sha256": commitment(records["reviews"][0]),
        "review_b_sha256": commitment(records["reviews"][1]),
        "resolution_reason": "The changed slicing operation contradicts the exact owner claim.",
    }
    records["adjudication"] = adjudication
    assert score([c])["passed"]
    adjudication["adjudication"]["review_a_sha256"] = "wrong"
    assert score([c])["unknown"] == 1


def test_case_stage_and_response_binding_prevents_review_replay():
    c = capture()
    other = deepcopy(c)
    other["stage"] = "after-sync"
    result = score(
        [other],
        obligations=[
            {
                "case_id": "owned",
                "stage": "after-sync",
                "owner": "entities/Policy.md:Policy",
                "operation": "revise-claim",
            }
        ],
        schedule=[{"case_id": "owned", "stage": "after-sync"}],
    )
    assert result["unknown"] == 1 and not result["passed"]


def test_nonactionable_review_requires_retained_evidence():
    capsule = packet("row")
    record = judgment(capsule, "nonactionable")
    record["evidence_citations"] = []
    assert not review_valid(capsule, record)


def test_unplanned_repeated_invocation_retains_every_row_without_review_replay():
    c = capture()
    result = score([c, deepcopy(c)])
    assert result["denominator"] == 2 and result["unknown"] == 1
    assert len({r["row_id"] for r in result["rows"]}) == 2
    assert not result["passed"] and result["issues"]


def test_malformed_returned_row_is_unknown_not_silently_removed():
    c = capture()
    c["response"]["items"] = [None]
    c["response_sha256"] = commitment(c["response"])
    result = score([c])
    assert result["denominator"] == result["unknown"] == 1 and not result["passed"]


def test_empty_correct_negative_stage_does_not_fail_an_otherwise_complete_campaign():
    c = capture((), "before")
    result = score(
        [c, capture()],
        schedule=[{"case_id": "owned", "stage": s} for s in ("before", "after-edit")],
    )
    assert result["passed"] and result["denominator"] == 1


@pytest.mark.parametrize(
    "reviews", [None, [None, None], "missing", {"label": "actionable"}]
)
def test_malformed_or_null_review_submission_retains_unknown_row(reviews):
    c = capture()
    next(iter(c["resolutions"].values()))["reviews"] = reviews
    result = score([c])
    assert result["denominator"] == result["unknown"] == 1 and not result["passed"]
