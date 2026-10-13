"""New cohort gates retain failures and recompute complete physical text costs."""

from copy import deepcopy

import pytest

from tests.developer_value.compact_experiment import record_sha256
from tests.developer_value.compact_delivery_policy import POLICY_SCHEMA, evaluate_cohort


def fixture():
    policy = {"schema_version": POLICY_SCHEMA, "eligible_cases": 1, "control_cases": 1,
              "allocation_tokens": 4096, "median_saving_min": .20,
              "warm_body_ratio_max": 1.35, "warm_sdk_ratio_max": 1.15,
              "read_ratio_max": 2, "read_overhead_ns_max": 250_000_000}
    def arm(body):
        return {"role": "eligible", "status": "success", "body": body,
                "canonical": "c" * 8000, "sdk": {"content": body}, "setup": {},
                "canonical_sdk": {"content": "c" * 8000}, "canonical_setup": {},
                "unchanged_sdk": {}, "changed_sdk": {"content": body},
                "lost_sdk": {"content": body}, "source_unchanged": True, "read_ns": 100}
    current, old = arm("v" * 4000), arm("o" * 4000)
    control = {"role": "control", "status": "canonical-failure"}
    pairs = [("primary", current, old), ("control", control, deepcopy(control))]
    return policy, pairs


def score(policy, pairs, pins=None):
    if pins is None:
        pins = {name + suffix: record_sha256(value)
                for name, a, b in pairs for suffix, value in ((":v2", a), (":v1", b))}
    return evaluate_cohort(pairs, policy=policy, expected_captures=pins)


def test_new_rule_can_qualify_without_changing_historical_guard_or_defaults():
    policy, pairs = fixture()
    result = score(policy, pairs)
    assert result["qualified"] and result["successful"] == result["total"] == 1
    assert not result["default_adoption"] and not result["model_productivity_claim"]


@pytest.mark.parametrize("status", ["cannot-fit", "unavailable", "uninvoked", "error"])
def test_failed_context_never_improves_size_median_or_denominator(status):
    policy, pairs = fixture()
    pairs[0][1]["status"] = status
    result = score(policy, pairs)
    assert not result["qualified"]
    assert result["total"] == 1 and result["successful"] == 0
    assert result["body_saving_median"] is None and result["sdk_saving_median"] is None
    assert result["rows"][0]["metrics"] is None


@pytest.mark.parametrize("field", ["sdk", "setup"])
def test_transport_and_setup_cannot_be_hidden_by_caller_token_numbers(field):
    policy, pairs = fixture()
    pairs[0][1][field] = {"framing": "x" * 20000}
    pairs[0][1]["tokens"] = {"first_use_sdk": 1}
    result = score(policy, pairs)
    assert not result["qualified"] and not result["rows"][0]["checks"]["sdk_cap"]


def test_tampered_capture_cannot_reuse_a_controller_pin():
    policy, pairs = fixture()
    pins = {name + suffix: record_sha256(value)
            for name, a, b in pairs for suffix, value in ((":v2", a), (":v1", b))}
    pairs[0][1]["read_ns"] += 1
    assert not score(policy, pairs, pins)["qualified"]


def test_duplicate_or_missing_pinned_case_is_not_a_smaller_success_denominator():
    policy, pairs = fixture()
    with pytest.raises(ValueError):
        score(policy, pairs + [pairs[0]])
    pins = {"primary:v2": record_sha256(pairs[0][1])}
    with pytest.raises(ValueError):
        score(policy, pairs, pins)
