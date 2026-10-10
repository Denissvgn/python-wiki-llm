"""Acceptance cannot borrow pooled success or trust unbound control verdicts."""

from copy import deepcopy

import pytest

from tests.developer_value.triage_acceptance import score_acceptance
from tests.developer_value.triage_oracle import commitment, occurrence_id
from tests.test_developer_value_triage_oracle import judgment, packet


CAMPAIGNS = {"development": "candidate-02", "confirmation": "confirmation-01"}
CONTROL_IDS = ["removal", "restart", "authority"]


def contract():
    plan = {
        "candidate_source": "frozen source identity",
        "configuration": "frozen configuration",
    }
    cases = [
        {
            "case_id": "dev",
            "split": "development",
            "family": "changed",
            "fixture_type": "flat",
        },
        {
            "case_id": "confirm",
            "split": "confirmation",
            "family": "changed",
            "fixture_type": "packed",
        },
        {
            "case_id": "negative",
            "split": "confirmation",
            "family": "unchanged",
            "fixture_type": "legacy",
        },
    ]
    schedule = [{"case_id": c["case_id"], "stage": "after-edit"} for c in cases]
    return {
        "schema_version": 1,
        "cases": cases,
        "schedule": schedule,
        "required_owner_actions": [
            {**s, "owner": "entities/Policy.md:Policy", "operation": "revise-claim"}
            for s in schedule[:2]
        ],
        "threshold": 0.8,
        "required_change_coverage": 1.0,
        "limit": 100,
        "source_plan": plan,
        "source_plan_sha256": commitment(plan),
    }


def capture(spec, case, labels=("actionable",), stage="after-edit", advisory=True):
    split = next(c["split"] for c in spec["cases"] if c["case_id"] == case)
    response = {
        "items": [
            {"owner": f"entities/Policy.md:Policy{index}"}
            for index, _ in enumerate(labels)
        ],
        "total": len(labels),
        "returned": len(labels),
        "omitted": 0,
        "truncated": False,
    }
    if advisory is not None:
        response["advisory"] = advisory
    response_hash = commitment(response)
    value = {
        "case_id": case,
        "stage": stage,
        "limit": 100,
        "contract_sha256": commitment(spec),
        "source_plan_sha256": spec["source_plan_sha256"],
        "read_only": True,
        "response": response,
        "response_sha256": response_hash,
        "capsules": {},
        "resolutions": {},
    }
    # Preserve the required owner's exact identity while letting extra rows be
    # distinct supported operations rather than scorer-deduplicated copies.
    if labels:
        response["items"][0]["owner"] = "entities/Policy.md:Policy"
        response_hash = commitment(response)
        value["response_sha256"] = response_hash
    for index, label in enumerate(labels):
        ident = occurrence_id(CAMPAIGNS[split], case, stage, response_hash, index)
        capsule = packet(ident, stage, response["items"][index]["owner"])
        capsule["case_id"] = case
        reviews = [
            judgment(capsule, label, role) for role in ("reviewer-a", "reviewer-b")
        ]
        for role, review in enumerate(reviews):
            review["actor"].update(
                agent_id=f"fresh-agent-{role}",
                session_id=f"fresh-session-{role}",
                fresh_no_fork=True,
            )
            review["visibility"].update(
                prior_reviews_seen=False, oracle_results_seen=False
            )
            review["limitations"] = [
                "Source-grounded agent judgment, not human acceptance."
            ]
        value["capsules"][ident] = capsule
        value["resolutions"][ident] = {"reviews": reviews}
    return value


def bind_receipt(receipt):
    receipt["evidence_sha256"] = commitment(receipt["evidence"])
    receipt["receipt_sha256"] = commitment(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    )
    return receipt


def controls(spec):
    return [
        bind_receipt(
            {
                "control_id": ident,
                "passed": True,
                "read_only": True,
                "invented_authority": False,
                "contract_sha256": commitment(spec),
                "source_plan_sha256": spec["source_plan_sha256"],
                "evidence": {
                    "before": "fixture hash",
                    "after": "fixture hash",
                    "observation": ident,
                },
            }
        )
        for ident in CONTROL_IDS
    ]


def observations(spec):
    return [
        capture(spec, "dev"),
        capture(spec, "confirm"),
        capture(spec, "negative", ()),
    ]


def gate(spec, captures=None, receipts=None, **kwargs):
    return score_acceptance(
        CAMPAIGNS,
        spec,
        kwargs.pop("contract_sha256", commitment(spec)),
        observations(spec) if captures is None else captures,
        controls(spec) if receipts is None else receipts,
        control_ids=kwargs.pop("control_ids", CONTROL_IDS),
        control_ids_sha256=kwargs.pop("control_ids_sha256", commitment(CONTROL_IDS)),
        **kwargs,
    )


def first_review(capture):
    return next(iter(capture["resolutions"].values()))["reviews"][0]


def test_split_identities_micro_totals_breakdowns_and_zero_row_negatives():
    spec = contract()
    result = gate(spec)
    assert result["passed"] and result["reviewer_independence"]
    assert result["pooled"]["actionable"] == result["pooled"]["denominator"] == 2
    assert result["pooled"]["coverage"] == 1.0
    assert result["splits"]["development"]["campaign"] == "candidate-02"
    assert result["splits"]["confirmation"]["campaign"] == "confirmation-01"
    assert result["breakdown"]["case_id"]["negative"]["fraction"] is None
    assert result["breakdown"]["family"]["changed"]["covered_count"] == 2
    assert result["breakdown"]["fixture_type"]["legacy"]["denominator"] == 0
    zero = result["zero_row_stages"][0]
    assert zero["case_id"] == "negative" and zero["split"] == "confirmation"
    assert zero["observed"] and zero["denominator"] == zero["required_count"] == 0
    assert zero["fraction"] is None and zero["coverage"] is None
    assert len(result["stages"]) == 3
    assert result["worst_case_variability"]["case_id"]["zero_row_groups"] == [
        "negative"
    ]


@pytest.mark.parametrize("change", ["source", "case", "obligation", "stage"])
def test_frozen_contract_rejects_plan_case_obligation_or_schedule_drift(change):
    spec = contract()
    frozen = commitment(spec)
    if change == "source":
        spec["source_plan"]["candidate_source"] = "different source"
    elif change == "case":
        spec["cases"].pop()
    elif change == "obligation":
        spec["required_owner_actions"].pop()
    else:
        spec["schedule"][0]["stage"] = "after-sync"
    with pytest.raises(ValueError, match="contract commitment"):
        gate(spec, captures=[], receipts=[], contract_sha256=frozen)


@pytest.mark.parametrize(
    "change",
    [
        "source-hash",
        "missing-case",
        "duplicate-case",
        "unscheduled-case",
        "extra-stage",
        "no-obligations",
        "bad-owner",
        "duplicate-obligation",
        "no-confirmation-obligation",
    ],
)
def test_invalid_frozen_plan_is_rejected_even_when_self_committed(change):
    spec = contract()
    if change == "source-hash":
        spec["source_plan_sha256"] = "wrong"
    elif change == "missing-case":
        spec["cases"].pop()
    elif change == "duplicate-case":
        spec["cases"].append(deepcopy(spec["cases"][0]))
    elif change == "unscheduled-case":
        spec["schedule"].pop()
    elif change == "extra-stage":
        spec["schedule"].append({"case_id": "absent", "stage": "restart"})
    elif change == "no-obligations":
        spec["required_owner_actions"] = []
    elif change == "bad-owner":
        spec["required_owner_actions"][0]["owner"] = ""
    elif change == "duplicate-obligation":
        spec["required_owner_actions"].append(
            deepcopy(spec["required_owner_actions"][0])
        )
    else:
        spec["required_owner_actions"].pop()
    with pytest.raises(ValueError):
        gate(spec, captures=[], receipts=[])


@pytest.mark.parametrize(
    "field,value",
    [
        ("limit", 99),
        ("limit", True),
        ("threshold", 0.7),
        ("required_change_coverage", 0.9),
        ("required_change_coverage", True),
    ],
)
def test_policy_cannot_lower_numeric_gates_or_budget(field, value):
    spec = contract()
    spec[field] = value
    with pytest.raises(ValueError, match="fixed"):
        gate(spec, captures=[], receipts=[])


@pytest.mark.parametrize(
    "change",
    ["drop-case", "drop-negative", "extra-case", "extra-stage", "duplicate-stage"],
)
def test_full_schedule_is_mandatory_and_extra_rows_remain_counted(change):
    spec = contract()
    captures = observations(spec)
    if change == "drop-case":
        captures.pop(1)
    elif change == "drop-negative":
        captures.pop()
    else:
        added = deepcopy(captures[0])
        if change == "extra-case":
            added["case_id"] = "unplanned"
        elif change == "extra-stage":
            added["stage"] = "after-restart"
        captures.append(added)
    result = gate(spec, captures)
    assert not result["passed"] and "incomplete-or-extra-schedule" in result["issues"]
    if change.startswith("extra") or change == "duplicate-stage":
        assert result["pooled"]["denominator"] == 3


@pytest.mark.parametrize("change", ["limit", "contract", "source"])
def test_capture_envelopes_cannot_use_a_different_budget_or_plan(change):
    spec = contract()
    captures = observations(spec)
    field = {
        "limit": "limit",
        "contract": "contract_sha256",
        "source": "source_plan_sha256",
    }[change]
    captures[0][field] = 99 if change == "limit" else "wrong"
    assert not gate(spec, captures)["passed"]


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "invalid",
        "same-agent",
        "same-session",
        "not-fresh",
        "prior-review",
        "oracle-seen",
        "provider-seen",
    ],
)
def test_every_row_requires_valid_independent_fresh_source_grounded_reviews(change):
    spec = contract()
    captures = observations(spec)
    review = first_review(captures[0])
    if change == "missing":
        captures[0]["resolutions"] = {}
    elif change == "invalid":
        review["evidence_citations"][0]["quote"] = "uncited inference"
    elif change == "same-agent":
        review["actor"]["agent_id"] = "fresh-agent-1"
    elif change == "same-session":
        review["actor"]["session_id"] = "fresh-session-1"
    elif change == "not-fresh":
        review["actor"]["fresh_no_fork"] = False
    else:
        field = {
            "prior-review": "prior_reviews_seen",
            "oracle-seen": "oracle_results_seen",
            "provider-seen": "provider_labels_seen",
        }[change]
        review["visibility"][field] = True
    result = gate(spec, captures)
    assert not result["passed"] and not result["reviewer_independence"]


def test_source_plan_freeze_does_not_replace_capsule_evidence_validation():
    spec = contract()
    captures = observations(spec)
    capsule = next(iter(captures[0]["capsules"].values()))
    capsule["artifacts"]["after.py"]["text"] = "return unrelated\n"
    result = gate(spec, captures)
    assert not result["passed"] and result["pooled"]["unknown"] == 1


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "failed",
        "duplicate",
        "extra",
        "write",
        "authority",
        "binding",
        "source",
        "evidence",
        "receipt",
    ],
)
def test_all_separately_frozen_controls_need_passing_hash_bound_read_only_receipts(
    change,
):
    spec = contract()
    receipts = controls(spec)
    if change == "missing":
        receipts.pop()
    elif change == "duplicate":
        receipts.append(deepcopy(receipts[0]))
    elif change == "extra":
        receipts[0]["control_id"] = "undeclared"
    else:
        field, value = {
            "failed": ("passed", False),
            "write": ("read_only", False),
            "authority": ("invented_authority", True),
            "binding": ("contract_sha256", "wrong"),
            "source": ("source_plan_sha256", "wrong"),
            "evidence": ("evidence_sha256", "wrong"),
            "receipt": ("receipt_sha256", "wrong"),
        }[change]
        receipts[0][field] = value
        if change not in {"evidence", "receipt"}:
            bind_receipt(receipts[0])
    result = gate(spec, receipts=receipts)
    assert not result["passed"] and result["pooled"]["denominator"] == 2


def test_control_verdict_tampering_is_detected_by_receipt_commitment():
    spec = contract()
    receipts = controls(spec)
    receipts[0]["passed"] = False
    bind_receipt(receipts[0])
    receipts[0]["passed"] = True
    assert not gate(spec, receipts=receipts)["passed"]


@pytest.mark.parametrize(
    "ids,hash_value",
    [
        ([], commitment([])),
        (["removal", "removal"], commitment(["removal", "removal"])),
        (CONTROL_IDS, "wrong"),
    ],
)
def test_control_id_manifest_is_separate_nonempty_unique_and_frozen(ids, hash_value):
    with pytest.raises(ValueError, match="control IDs"):
        gate(contract(), control_ids=ids, control_ids_sha256=hash_value)


@pytest.mark.parametrize(
    "labels,passed",
    [
        (("actionable",) * 4 + ("unknown",), True),
        (("actionable",) * 3 + ("unknown",) * 2, False),
        (("unknown",) * 5, False),
    ],
)
def test_unknown_independently_reviewed_rows_keep_denominator_and_fixed_threshold(
    labels, passed
):
    spec = contract()
    captures = [capture(spec, "dev", labels), *observations(spec)[1:]]
    result = gate(spec, captures)
    assert result["splits"]["development"]["denominator"] == 5
    assert result["splits"]["development"]["unknown"] == labels.count("unknown")
    assert result["reviewer_independence"] and result["passed"] is passed
    if passed:
        assert result["splits"]["development"]["fraction"] == 0.8
        assert result["pooled"]["coverage"] == 1


def test_all_empty_outputs_have_explicit_null_scores_and_fail():
    spec = contract()
    result = gate(spec, [capture(spec, c["case_id"], ()) for c in spec["cases"]])
    assert not result["passed"] and result["pooled"]["fraction"] is None
    assert result["pooled"]["denominator"] == 0 and len(result["zero_row_stages"]) == 3
    assert result["pooled"]["coverage"] == 0 and not result["reviewer_independence"]


def test_pooled_success_cannot_mask_failed_confirmation_and_reports_variability():
    spec = contract()
    captures = [
        capture(spec, "dev", ("actionable",) * 10),
        capture(spec, "confirm", ("actionable", "nonactionable")),
        capture(spec, "negative", ()),
    ]
    result = gate(spec, captures)
    assert result["pooled"]["passed"] and result["pooled"]["fraction"] == 11 / 12
    assert result["splits"]["development"]["passed"]
    assert not result["splits"]["confirmation"]["passed"] and not result["passed"]
    assert result["worst_case_variability"]["case_id"]["minimum_fraction"] == 0.5
    assert result["worst_case_variability"]["fixture_type"]["minimum_fraction"] == 0.5
    assert (
        result["split_breakdown"]["confirmation"]["family"]["changed"]["fraction"]
        == 0.5
    )
    assert (
        result["split_worst_case_variability"]["confirmation"]["family"][
            "minimum_fraction"
        ]
        == 0.5
    )


def test_micro_gate_is_not_replaced_by_averaged_case_fractions():
    spec = contract()
    result = gate(
        spec,
        [
            capture(spec, "dev", ("actionable", "nonactionable")),
            capture(spec, "confirm", ("actionable",) * 10),
            capture(spec, "negative", ()),
        ],
    )
    assert result["pooled"]["fraction"] == 11 / 12
    assert not result["passed"] and not result["splits"]["development"]["passed"]


def test_required_owner_action_coverage_is_not_replaced_by_actionability():
    spec = contract()
    captures = observations(spec)
    for review in next(iter(captures[1]["resolutions"].values()))["reviews"]:
        review["supported_actions"][0]["operation"] = "inspect-pending-mapping"
    result = gate(spec, captures)
    assert result["pooled"]["fraction"] == 1 and result["pooled"]["coverage"] == 0.5
    assert (
        not result["passed"]
        and result["breakdown"]["case_id"]["confirm"]["coverage"] == 0
    )


@pytest.mark.parametrize("value", [None, {}, {"artifacts": {}}])
def test_missing_or_malformed_capsules_fail_without_erasing_the_row(value):
    spec = contract()
    captures = observations(spec)
    ident = next(iter(captures[0]["capsules"]))
    captures[0]["capsules"][ident] = value
    result = gate(spec, captures)
    assert not result["passed"] and not result["reviewer_independence"]
    assert result["pooled"]["denominator"] == 2 and result["pooled"]["unknown"] == 1


def test_over_budget_output_cannot_be_hidden_by_correct_limit_metadata():
    spec = contract()
    captures = [capture(spec, "dev", ("actionable",) * 101), *observations(spec)[1:]]
    result = gate(spec, captures)
    assert result["pooled"]["denominator"] == 102
    assert result["pooled"]["fraction"] == 1
    assert not result["passed"] and "capture-limit-exceeded" in result["issues"]


def test_malformed_returned_item_stays_in_denominator():
    spec = contract()
    captures = observations(spec)
    captures[0]["response"]["items"] = [None]
    captures[0]["response_sha256"] = commitment(captures[0]["response"])
    result = gate(spec, captures)
    assert not result["passed"] and result["pooled"]["denominator"] == 2
    assert result["pooled"]["unknown"] == 1


def test_truncated_empty_capture_is_not_a_successful_negative():
    spec = contract()
    captures = observations(spec)
    captures[2]["response"].update(total=1, omitted=1, truncated=True)
    captures[2]["response_sha256"] = commitment(captures[2]["response"])
    result = gate(spec, captures)
    assert result["zero_row_stages"][0]["observed"]
    assert not result["passed"]
    assert "truncated-response" in result["splits"]["confirmation"]["issues"]


def test_empty_required_stage_is_a_miss_rather_than_a_negative_pass():
    spec = contract()
    captures = [capture(spec, "dev", ()), *observations(spec)[1:]]
    result = gate(spec, captures)
    empty_required = next(s for s in result["zero_row_stages"] if s["case_id"] == "dev")
    assert empty_required["required_count"] == 1 and empty_required["coverage"] == 0
    assert empty_required["missed"] and not result["passed"]


def test_split_campaign_id_change_cannot_relabel_original_reviewed_occurrences():
    spec = contract()
    result = score_acceptance(
        {"development": "other-candidate", "confirmation": "confirmation-01"},
        spec,
        commitment(spec),
        observations(spec),
        controls(spec),
        control_ids=CONTROL_IDS,
        control_ids_sha256=commitment(CONTROL_IDS),
    )
    assert result["pooled"]["denominator"] == 2 and result["pooled"]["unknown"] == 1
    assert not result["passed"]


def test_nonactionable_row_also_requires_independent_reviews():
    spec = contract()
    captures = [
        capture(spec, "dev", ("actionable",) * 4 + ("nonactionable",)),
        *observations(spec)[1:],
    ]
    records = list(captures[0]["resolutions"].values())
    records[-1]["reviews"][0]["actor"]["agent_id"] = "fresh-agent-1"
    result = gate(spec, captures)
    assert result["splits"]["development"]["passed"]
    assert result["pooled"]["fraction"] > 0.8
    assert not result["reviewer_independence"] and not result["passed"]


@pytest.mark.parametrize("read_only", [False, None])
def test_capture_read_only_authentication_is_mandatory(read_only):
    spec = contract()
    captures = observations(spec)
    if read_only is None:
        captures[0].pop("read_only")
    else:
        captures[0]["read_only"] = read_only
    result = gate(spec, captures)
    assert result["pooled"]["fraction"] == 1
    assert not result["passed"] and "capture-not-read-only" in result["issues"]


@pytest.mark.parametrize("advisory", [False, None])
def test_all_queue_responses_must_be_advisory(advisory):
    spec = contract()
    captures = [capture(spec, "dev", advisory=advisory), *observations(spec)[1:]]
    result = gate(spec, captures)
    assert result["reviewer_independence"] and result["pooled"]["fraction"] == 1
    assert not result["passed"] and "non-advisory-response" in result["issues"]


def test_valid_partial_response_with_error_is_not_a_complete_observation():
    spec = contract()
    captures = observations(spec)
    captures[0]["error"] = {"message": "incomplete snapshot read"}
    result = gate(spec, captures)
    assert result["pooled"]["denominator"] == 2 and result["pooled"]["fraction"] == 1
    assert not result["passed"] and "capture-error" in result["issues"]


@pytest.mark.parametrize(
    "field,value", [("case_id", []), ("stage", {}), ("case_id", None)]
)
def test_malformed_capture_identity_fails_without_discarding_returned_rows(
    field, value
):
    spec = contract()
    captures = observations(spec)
    captures[0][field] = value
    result = gate(spec, captures)
    assert not result["passed"] and "invalid-capture-identity" in result["issues"]
    assert result["pooled"]["denominator"] == 2 and result["pooled"]["unknown"] == 1
    assert result["invalid_capture_identities"] == [
        {"index": 0, "field": field, "value": value}
    ]


@pytest.mark.parametrize("change", ["citation-artifact", "actor-role", "operation"])
def test_malformed_review_values_are_rejected_without_crashing_or_dropping_rows(change):
    spec = contract()
    captures = observations(spec)
    original = deepcopy(captures)
    review = first_review(captures[0])
    if change == "citation-artifact":
        review["evidence_citations"][0]["artifact"] = []
    elif change == "actor-role":
        review["actor"]["role"] = []
    else:
        review["supported_actions"][0]["operation"] = []
    submitted = deepcopy(captures)
    result = gate(spec, captures)
    assert captures == submitted and captures != original
    assert not result["passed"] and result["pooled"]["denominator"] == 2
    assert result["pooled"]["unknown"] == 1
    assert result["rejected_evidence"][0]["reason"] in {
        "malformed-source-review",
        "invalid-source-review",
    }
    assert result["rejected_evidence"][0]["submission_sha256"] == commitment(
        next(iter(captures[0]["resolutions"].values()))
    )


def test_unhashable_control_identity_fails_without_losing_scored_rows():
    spec = contract()
    receipts = controls(spec)
    receipts[0]["control_id"] = []
    original = deepcopy(receipts)
    result = gate(spec, receipts=receipts)
    assert receipts == original and result["controls"] == original
    assert not result["passed"] and result["pooled"]["denominator"] == 2
    assert result["invalid_control_identities"] == [{"index": 0, "value": []}]


def test_nontext_owners_cannot_invent_actionable_occurrences_while_real_coverage_passes():
    spec = contract()
    c = capture(spec, "dev", ("actionable",) * 10)
    old_capsules = list(c["capsules"].values())
    old_resolutions = list(c["resolutions"].values())
    c["response"]["items"][-1]["owner"] = None
    response_hash = commitment(c["response"])
    c["response_sha256"] = response_hash
    c["capsules"], c["resolutions"] = {}, {}
    for index, (capsule, resolution) in enumerate(zip(old_capsules, old_resolutions)):
        ident = occurrence_id(
            CAMPAIGNS["development"], "dev", "after-edit", response_hash, index
        )
        capsule["row_id"] = ident
        capsule["owner"] = c["response"]["items"][index]["owner"]
        for review in resolution["reviews"]:
            review["row_id"] = ident
            review["capsule_manifest_sha256"] = commitment(capsule)
            review["supported_actions"][0]["owner"] = capsule["owner"]
        c["capsules"][ident], c["resolutions"][ident] = capsule, resolution
    captures = [c, *observations(spec)[1:]]
    original = deepcopy(captures)
    result = gate(spec, captures)
    assert captures == original
    assert result["pooled"]["denominator"] == 11 and result["pooled"]["unknown"] == 1
    assert result["pooled"]["fraction"] > 0.8 and result["pooled"]["coverage"] == 1
    assert not result["passed"] and "invalid-returned-owner" in result["issues"]


def test_passing_gate_does_not_mutate_source_captures_or_control_receipts():
    spec = contract()
    captures, receipts = observations(spec), controls(spec)
    original_captures, original_receipts = deepcopy(captures), deepcopy(receipts)
    assert gate(spec, captures, receipts)["passed"]
    assert captures == original_captures and receipts == original_receipts
