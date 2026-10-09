"""Boundary and capture-integrity guards for the frozen AF16 size gate."""
from __future__ import annotations

from dataclasses import replace
import json
from typing import Any

import pytest

from llm_wiki_cli.services.token_counting import EstimatedCounter
from tests.developer_value.compact_experiment import (
    ESTIMATOR_ID,
    PRIMARY_CASE,
    REQUIRED_CAPTURE_CHECKS,
    REQUIRED_CONTROLS,
    REQUIRED_MINIMUM_CHECKS,
    MetricBindings,
    check_comparison,
    inspect_measurement,
    record_sha256,
    size_gate,
    text_sha256,
)


def body(tokens: int, *, ok: bool = True) -> str:
    value = json.dumps({"ok": ok, "content": "", "accounting": {}, "view_id": "view"}, separators=(",", ":"))
    # The complete body, including framing and metadata, occupies exactly this
    # many UTF-8 bytes. Padding is fixture content, not an excluded scope.
    return value.replace('"content":""', '"content":"' + "x" * (4 * tokens - len(value)) + '"')


def accounting(text: str) -> dict[str, Any]:
    return {"tokens": (len(text.encode()) + 3) // 4, "bytes": len(text.encode()),
            "counter": ESTIMATOR_ID, "exact": False}


def sample(*, canonical_tokens: int = 2000, compact_tokens: int = 1000,
           budget: int = 1000, status: str = "success") -> tuple[dict[str, Any], MetricBindings]:
    canonical = body(canonical_tokens)
    compact = body(compact_tokens, ok=status == "success")
    identities: dict[str, Any] = {
        "source_id": "frozen-source", "case_id": PRIMARY_CASE,
        "request_sha256": "request-pin", "view_options_sha256": "options-pin",
        "canonical_sha256": text_sha256(canonical), "profile_sha256": "profile-pin",
        "policy_sha256": "policy-pin", "counter_identity": ESTIMATOR_ID,
        "counter_exact": False, "frame_identity": "actual-cli-framing/v1",
        "input_sha256": "frozen-238-byte-two-fact-input", "provider_id": "source-provider",
        "receipt_provider_id": "receiving-provider", "candidate_id": "frozen-candidate",
        "budget_tokens": budget, "canonical_ceiling_tokens": 3000,
    }
    receipt = json.dumps({key: identities[key] for key in (
        "source_id", "case_id", "request_sha256", "canonical_sha256", "profile_sha256",
        "policy_sha256", "input_sha256", "provider_id", "receipt_provider_id")}, sort_keys=True)
    metadata = {**identities, "status": status, "canonical_ok": True, "view_ok": status == "success",
                "canonical_accounting": accounting(canonical), "view_accounting": accounting(compact),
                "canonical_wire_text": canonical + "\n", "wire_text": compact + "\n",
                "canonical_wire_encoding": "verbatim", "wire_encoding": "verbatim",
                "receipt_artifact": receipt, "followup_texts": [], "wall_ns": 10,
                "controls": dict.fromkeys(REQUIRED_CONTROLS, True)}
    minimum_sha = None
    if status == "cannot-fit":
        minimum = body(budget + 1)
        metadata.update(minimum_success_text=minimum, minimum_success_accounting=accounting(minimum))
        minimum_sha = text_sha256(minimum)
    record = {"canonical_text": canonical, "view_text": compact, "metadata": metadata}
    pins = MetricBindings(**identities, record_sha256=record_sha256(record), receipt_sha256=text_sha256(receipt),
                          candidate_ids=("frozen-candidate",), minimum_success_sha256=minimum_sha)
    return record, pins


def repin_record(record: dict[str, Any], pins: MetricBindings) -> MetricBindings:
    """Allow a changed physical capture without changing independent bindings."""
    return replace(pins, record_sha256=record_sha256(record))


def decision(record: dict[str, Any], pins: MetricBindings):
    return check_comparison(record, expectedpins=pins, counter=EstimatedCounter())


def test_full_emitted_body_boundary_and_separate_host_frame_are_counted() -> None:
    record, pins = sample()
    scored = decision(record, pins)
    assert scored.eligible and scored.body_size_win
    measured = scored.measurement
    assert measured is not None
    assert measured.compact_body.estimated_tokens == 1000
    assert measured.compact_wire.estimated_tokens == 1001
    assert measured.canonical_body.bytes == 8000
    assert measured.compact_body.bytes == 4000
    assert not scored.default_adoption and not scored.implementation_adopted
    assert not scored.workflow_cost_claim
    assert scored.cases_count == scored.successful_cases == 1


@pytest.mark.parametrize(("canonical_tokens", "compact_tokens", "passes"), [
    (2000, 1000, True), (2002, 1001, False), (1000, 499, True),
    (1000, 500, True), (999, 500, False), (2001, 1000, True),
])
def test_integer_boundaries_do_not_round_half_or_1000_thresholds(
        canonical_tokens: int, compact_tokens: int, passes: bool) -> None:
    record, pins = sample(canonical_tokens=canonical_tokens, compact_tokens=compact_tokens, budget=2000)
    assert decision(record, pins).eligible is passes


@pytest.mark.parametrize("name", REQUIRED_CONTROLS)
@pytest.mark.parametrize("value", [False, None, "true", 1])
def test_missing_false_and_nonboolean_controls_cannot_establish_equivalence(name: str, value: Any) -> None:
    record, pins = sample()
    record["metadata"]["controls"][name] = value
    scored = decision(record, repin_record(record, pins))
    assert not scored.eligible and name in scored.reasons
    assert scored.cases_count == 1


def test_omitted_controls_and_accounting_remain_negative_cases() -> None:
    record, pins = sample()
    record["metadata"]["controls"] = {}
    del record["metadata"]["view_accounting"]
    scored = decision(record, repin_record(record, pins))
    assert not scored.eligible
    assert set(REQUIRED_CONTROLS) <= set(scored.reasons)
    assert "view_accounting" in scored.reasons


@pytest.mark.parametrize("field", ["tokens", "bytes", "counter", "exact"])
def test_falsified_accounting_cannot_shrink_physical_output(field: str) -> None:
    record, pins = sample(compact_tokens=1001)
    wrong = {"tokens": 1, "bytes": 4, "counter": "other-counter", "exact": True}
    record["metadata"]["view_accounting"][field] = wrong[field]
    scored = decision(record, repin_record(record, pins))
    assert not scored.eligible and "view_accounting" in scored.reasons
    assert scored.measurement is not None and scored.measurement.compact_body.estimated_tokens == 1001


@pytest.mark.parametrize("field", ["source_id", "case_id", "request_sha256", "view_options_sha256",
                                    "canonical_sha256", "profile_sha256", "policy_sha256", "input_sha256",
                                    "counter_identity", "frame_identity", "provider_id", "receipt_provider_id",
                                    "candidate_id", "budget_tokens", "canonical_ceiling_tokens"])
def test_independent_bindings_reject_rehashed_mixed_capture(field: str) -> None:
    record, pins = sample()
    record["metadata"][field] = 999 if isinstance(record["metadata"][field], int) else "substituted"
    scored = decision(record, repin_record(record, pins))
    assert not scored.eligible and f"binding_{field}" in scored.reasons


def test_physical_artifacts_cannot_be_altered_without_external_pin_change() -> None:
    record, pins = sample()
    record["metadata"]["wall_ns"] = 20
    assert "physical_capture_pin" in decision(record, pins).reasons
    record["canonical_text"] = record["canonical_text"].replace("x", "y", 1)
    scored = decision(record, repin_record(record, pins))
    assert "canonical_text_pin" in scored.reasons
    assert "canonical_body_in_wire" in scored.reasons


def test_receipt_pin_and_provider_binding_require_physical_custody() -> None:
    record, pins = sample()
    receipt = json.loads(record["metadata"]["receipt_artifact"])
    receipt["receipt_provider_id"] = "different-receiver"
    record["metadata"]["receipt_artifact"] = json.dumps(receipt)
    scored = decision(record, repin_record(record, pins))
    assert "receipt_pin" in scored.reasons and "receipt_binding" in scored.reasons


def test_external_pins_are_not_inferred_from_record_claims() -> None:
    record, _ = sample()
    scored = check_comparison(record, counter=EstimatedCounter())
    assert not scored.eligible and scored.cases_count == 1
    assert scored.reasons == ("external_pins",)


@pytest.mark.parametrize("status", ["error", "unavailable", "cannot-fit"])
def test_unknown_failed_and_cannot_fit_slots_stay_in_denominator(status: str) -> None:
    record, pins = sample(status=status)
    scored = decision(record, pins)
    assert not scored.eligible and not scored.body_size_win
    assert scored.cases_count == 1 and scored.successful_cases == 0
    assert "successful_projection" in scored.reasons


def test_canonical_failure_cannot_produce_successful_paired_gain() -> None:
    record, pins = sample()
    record["metadata"]["canonical_ok"] = False
    assert "canonical_success" in decision(record, repin_record(record, pins)).reasons


def test_honest_cannot_fit_distinguishes_diagnostic_from_minimum_projection() -> None:
    record, pins = sample(compact_tokens=200, status="cannot-fit")
    scored = decision(record, pins)
    assert not scored.eligible
    measured = scored.measurement
    assert measured is not None and measured.minimum_success is not None
    assert measured.compact_body.estimated_tokens == 200
    assert measured.minimum_success.estimated_tokens == 1001
    assert measured.checks["truthful_budget_diagnostic"]
    assert measured.checks["minimum_success_pin"] and measured.checks["minimum_success_accounting"]


def test_cannot_fit_claim_requires_pinned_minimum_larger_than_budget() -> None:
    record, pins = sample(status="cannot-fit")
    minimum = body(1000)
    record["metadata"]["minimum_success_text"] = minimum
    record["metadata"]["minimum_success_accounting"] = accounting(minimum)
    pins = replace(repin_record(record, pins), minimum_success_sha256=text_sha256(minimum))
    assert "truthful_budget_diagnostic" in decision(record, pins).reasons


@pytest.mark.parametrize("which", ["wire_text", "canonical_wire_text", "receipt_artifact", "followup_texts"])
def test_host_transport_and_receipt_are_required_actual_capture_fields(which: str) -> None:
    record, pins = sample()
    del record["metadata"][which]
    with pytest.raises(ValueError):
        decision(record, repin_record(record, pins))


def test_host_framing_omission_cannot_fake_a_complete_transport() -> None:
    record, pins = sample()
    record["metadata"]["wire_text"] = "host prefix only"
    scored = decision(record, repin_record(record, pins))
    assert "compact_body_in_wire" in scored.reasons


def test_receipt_followups_are_counted_separately_without_workflow_win() -> None:
    record, pins = sample()
    record["metadata"]["followup_texts"] = ["é" * 10000, "followup host frame"]
    scored = decision(record, repin_record(record, pins))
    assert scored.eligible and not scored.workflow_cost_claim
    measured = scored.measurement
    assert measured is not None
    assert measured.receipt_followup[0].bytes == 20000
    assert measured.receipt_followup[0].estimated_tokens == 5000
    assert measured.compact_body.estimated_tokens == 1000


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_invalid_counters_cannot_return_zero_boolean_negative_or_scoped_values(bad: Any) -> None:
    class BadCounter:
        identity = ESTIMATOR_ID
        exact = False

        def count(self, text: str) -> Any:
            return bad

    record, pins = sample()
    with pytest.raises(ValueError, match="counter returned"):
        check_comparison(record, expectedpins=pins, counter=BadCounter())


def test_counter_that_scopes_to_content_only_is_rejected() -> None:
    class ScopedCounter:
        identity = ESTIMATOR_ID
        exact = False

        def count(self, text: str) -> int:
            return (len(json.loads(text)["content"].encode()) + 3) // 4

    record, pins = sample()
    with pytest.raises(ValueError, match="scoped"):
        check_comparison(record, expectedpins=pins, counter=ScopedCounter())


def test_counter_mutation_during_count_is_detected() -> None:
    class MutableCounter:
        identity = ESTIMATOR_ID
        exact = False

        def count(self, text: str) -> int:
            self.exact = True
            return (len(text.encode()) + 3) // 4

    record, pins = sample()
    with pytest.raises(ValueError, match="changed"):
        check_comparison(record, expectedpins=pins, counter=MutableCounter())


@pytest.mark.parametrize("field", ["budget_tokens", "canonical_ceiling_tokens"])
@pytest.mark.parametrize("bad", [0, -1, True, 1.1])
def test_nonpositive_and_boolean_frozen_budgets_reject(field: str, bad: Any) -> None:
    record, pins = sample()
    with pytest.raises(ValueError, match="positive integer"):
        decision(record, replace(pins, **{field: bad}))


def test_requested_budget_must_narrow_external_canonical_ceiling() -> None:
    record, pins = sample()
    with pytest.raises(ValueError, match="cannot widen"):
        decision(record, replace(pins, canonical_ceiling_tokens=999))


@pytest.mark.parametrize("field", ["workflow_budget_tokens", "total_budget_tokens", "receipt_budget_tokens", "wall_ns"])
def test_negative_total_budget_and_wall_fields_reject(field: str) -> None:
    record, pins = sample()
    record["metadata"][field] = -1
    with pytest.raises(ValueError):
        decision(record, repin_record(record, pins))


@pytest.mark.parametrize("ids", [(), ("a", "b", "c"), ("frozen-candidate", "frozen-candidate"), ("other",)])
def test_frozen_controller_limits_candidates_before_measurement(ids: tuple[str, ...]) -> None:
    record, pins = sample()
    with pytest.raises(ValueError, match="candidate"):
        decision(record, replace(pins, candidate_ids=ids))


def test_an_alternate_tiny_case_cannot_replace_the_frozen_primary() -> None:
    record, pins = sample(compact_tokens=100)
    record["metadata"]["case_id"] = "favorable-alternate-tiny"
    receipt = json.loads(record["metadata"]["receipt_artifact"])
    receipt["case_id"] = "favorable-alternate-tiny"
    record["metadata"]["receipt_artifact"] = json.dumps(receipt)
    pins = replace(repin_record(record, pins), case_id="favorable-alternate-tiny",
                   receipt_sha256=text_sha256(record["metadata"]["receipt_artifact"]))
    assert "frozen_primary_case" in decision(record, pins).reasons


def test_direct_inspection_and_gate_report_estimated_text_not_actual_model_tokens() -> None:
    record, pins = sample()
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    output = size_gate(measured).to_dict()
    assert output["measurement"]["compact_body"]["counter_identity"] == ESTIMATOR_ID
    assert output["measurement"]["compact_body"]["exact"] is False
    assert "model_tokens" not in output and "money" not in output


def test_actual_mcp_json_transport_counts_escaped_text_and_structured_metadata() -> None:
    record, pins = sample()
    for body_field, wire_field in (("canonical_text", "canonical_wire_text"), ("view_text", "wire_text")):
        record["metadata"][wire_field] = json.dumps({
            "content": [{"type": "text", "text": record[body_field]}],
            "structuredContent": {"session_id": "session", "state": "current"},
        })
    record["metadata"].update(canonical_wire_encoding="mcp-calltoolresult-jsontext",
                              wire_encoding="mcp-calltoolresult-jsontext")
    scored = decision(record, repin_record(record, pins))
    assert scored.eligible
    measured = scored.measurement
    assert measured is not None
    assert measured.compact_wire.bytes == len(record["metadata"]["wire_text"].encode())
    assert measured.compact_wire.bytes > measured.compact_body.bytes
    assert measured.checks["compact_body_in_wire"]


@pytest.mark.parametrize("where", ["notes", "structuredContent", "wrong-content-text", "wrong-content-type"])
def test_mcp_body_only_in_notes_or_metadata_cannot_impersonate_emitted_text(where: str) -> None:
    record, pins = sample()
    payload: dict[str, Any] = {"content": [{"type": "text", "text": "different body"}]}
    if where in ("notes", "structuredContent"):
        payload[where] = {"text": record["view_text"]}
    elif where == "wrong-content-text":
        payload["content"][0]["text"] = record["view_text"].replace("x", "y", 1)
    else:
        payload["content"][0] = {"type": "image", "text": record["view_text"]}
    record["metadata"]["wire_text"] = json.dumps(payload)
    record["metadata"]["wire_encoding"] = "mcp-calltoolresult-jsontext"
    assert "compact_body_in_wire" in decision(record, repin_record(record, pins)).reasons


@pytest.mark.parametrize("encoding", [None, "guessed", True])
def test_wire_encoding_must_be_explicit_and_known(encoding: Any) -> None:
    record, pins = sample()
    record["metadata"]["wire_encoding"] = encoding
    with pytest.raises(ValueError, match="encoding"):
        decision(record, repin_record(record, pins))


def test_direct_size_gate_rejects_a_measurement_with_only_equivalence_controls() -> None:
    record, pins = sample()
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    forged = replace(measured, checks=dict.fromkeys(REQUIRED_CONTROLS, True))
    scored = size_gate(forged)
    assert not scored.eligible and not scored.body_size_win
    assert set(REQUIRED_CAPTURE_CHECKS) <= set(scored.reasons)
    assert scored.cases_count == 1 and scored.successful_cases == 0


@pytest.mark.parametrize("name", REQUIRED_CAPTURE_CHECKS)
@pytest.mark.parametrize("replacement", ["missing", False, None, 1, "true"])
def test_direct_size_gate_requires_every_foundational_capture_check(name: str, replacement: Any) -> None:
    record, pins = sample()
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    changed: dict[str, Any] = dict(measured.checks)
    if replacement == "missing":
        del changed[name]
    else:
        changed[name] = replacement
    scored = size_gate(replace(measured, checks=changed))
    assert not scored.eligible and not scored.body_size_win
    assert name in scored.reasons and scored.checks[name] is False


@pytest.mark.parametrize("name", REQUIRED_MINIMUM_CHECKS)
def test_direct_cannot_fit_gate_requires_minimum_projection_custody_checks(name: str) -> None:
    record, pins = sample(status="cannot-fit", compact_tokens=200)
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    changed = dict(measured.checks)
    del changed[name]
    scored = size_gate(replace(measured, checks=changed))
    assert name in scored.reasons and scored.checks[name] is False
    assert not scored.eligible and not scored.body_size_win
    assert scored.cases_count == 1


@pytest.mark.parametrize("field", ["bytes", "estimated_tokens", "sha256", "counter_identity", "exact"])
def test_gate_rederives_each_size_field_from_the_pinned_physical_body(field: str) -> None:
    record, pins = sample(canonical_tokens=1684, compact_tokens=893, budget=3200)
    pins = replace(pins, canonical_ceiling_tokens=3200)
    record["metadata"]["canonical_ceiling_tokens"] = 3200
    pins = repin_record(record, pins)
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    assert not size_gate(measured).body_size_win
    edits = {"bytes": 3200, "estimated_tokens": 800, "sha256": text_sha256(body(800)),
             "counter_identity": "other-counter", "exact": True}
    forged = replace(measured, compact_body=replace(measured.compact_body, **{field: edits[field]}))
    assert forged.binding == pins
    assert "derived_measurement_custody" in size_gate(forged).reasons
    assert not size_gate(forged).body_size_win


@pytest.mark.parametrize("field", ["canonical_body", "compact_body", "canonical_wire", "compact_wire",
                                   "receipt_followup", "minimum_success", "status", "wall_ns", "capture_json"])
def test_even_plausible_derived_measurement_edits_do_not_preserve_custody(field: str) -> None:
    record, pins = sample()
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    assert size_gate(measured).eligible
    if field in ("canonical_body", "compact_body", "canonical_wire", "compact_wire"):
        # Coordinate a plausible byte/count/hash trio, rather than only making
        # estimator arithmetic internally inconsistent.
        part = getattr(measured, field)
        edited_text = body(900)
        changed: Any = replace(part, bytes=len(edited_text.encode()), estimated_tokens=900,
                               sha256=text_sha256(edited_text))
    else:
        changed = {"receipt_followup": (measured.compact_body,),
                   "minimum_success": measured.compact_body, "status": "cannot-fit",
                   "wall_ns": 11, "capture_json": None}[field]
    assert not size_gate(replace(measured, **{field: changed})).eligible


def test_gate_authenticates_checks_and_immutable_receipt_capture() -> None:
    record, pins = sample()
    record["metadata"]["controls"]["decisive_facts"] = False
    pins = repin_record(record, pins)
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    assert isinstance(measured.checks, dict)
    measured.checks["decisive_facts"] = True
    assert not size_gate(measured).eligible
    assert "derived_measurement_custody" in size_gate(measured).reasons
    assert isinstance(measured.capture_json, str)
    raw = json.loads(measured.capture_json)
    raw["metadata"]["controls"]["decisive_facts"] = True
    raw["metadata"]["receipt_artifact"] = "{}"
    assert not size_gate(replace(measured, capture_json=json.dumps(raw))).eligible


def test_inspection_keeps_no_mutable_alias_to_the_raw_controller_record() -> None:
    record, pins = sample()
    measured = inspect_measurement(record["canonical_text"], record["view_text"], record["metadata"],
                                   expected=pins, counter=EstimatedCounter())
    record["metadata"]["controls"].clear()
    record["metadata"]["receipt_artifact"] = "{}"
    assert size_gate(measured).eligible
    assert "capture_json" not in measured.to_dict()
    assert "capture_json" not in size_gate(measured).to_dict()["measurement"]
