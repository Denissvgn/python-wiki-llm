"""A body win must not conceal first-use framing, decoder or follow-up costs."""

from copy import deepcopy
import json

import pytest

from llm_wiki_cli.services.token_counting import EstimatedCounter
from tests.developer_value.compact_experiment import REQUIRED_CONTROLS, record_sha256
from tests.developer_value.compact_first_use import score_first_use


def capture():
    return {"canonical": {"body": "c" * 6400, "messages": ["c" * 6400],
                          "wire_encoding": "verbatim"},
            "compact": {"body": "v" * 3000, "messages": ["v" * 3000],
                        "wire_encoding": "verbatim"},
            "controls": dict.fromkeys(REQUIRED_CONTROLS, True),
            "status": "success", "complete_first_use": True}


def score(value, pin=None):
    return score_first_use(value, expected_sha256=pin or record_sha256(value),
                          counter=EstimatedCounter())


def test_complete_paired_size_win_does_not_authorize_default_or_productivity():
    result = score(capture())
    assert result["eligible"]
    assert not result["default_adoption"] and not result["model_productivity_claim"]


@pytest.mark.parametrize("cost", ["decoder", "followup", "sdk-framing"])
def test_actual_first_use_cost_can_defeat_a_valid_body_win(cost):
    value = capture()
    if cost == "sdk-framing":
        value["compact"]["messages"][0] = json.dumps({
            "content": [{"type": "text", "text": value["compact"]["body"]}],
            "structuredContent": {"metadata": "m" * 2000}})
        value["compact"]["wire_encoding"] = "mcp-calltoolresult-jsontext"
    else:
        value["compact"]["messages"].append("d" * 2000)
    result = score(value)
    assert result["checks"]["body_at_least_half_smaller"]
    assert not result["checks"]["first_use_at_most_1000"]
    assert not result["eligible"]


@pytest.mark.parametrize("field", ["complete_first_use", *REQUIRED_CONTROLS])
def test_missing_decoder_or_receiving_control_never_qualifies(field):
    value = capture()
    if field == "complete_first_use":
        value[field] = False
    else:
        value["controls"].pop(field)
    assert not score(value)["eligible"]


@pytest.mark.parametrize("status", ["cannot-fit", "unavailable", "error"])
def test_small_diagnostic_does_not_count_as_a_successful_context(status):
    value = capture()
    value["status"] = status
    assert not score(value)["eligible"]


def test_changed_capture_cannot_reuse_its_external_pin():
    value = capture()
    pin = record_sha256(value)
    altered = deepcopy(value)
    altered["compact"]["messages"].append("additional emitted text")
    assert not score(altered, pin)["eligible"]


def test_omitted_body_and_duplicate_metadata_are_detected():
    value = capture()
    value["compact"]["messages"][0] = "metadata only"
    assert not score(value)["eligible"]


def test_unicode_and_separate_message_rounding_count_all_bytes():
    value = capture()
    value["compact"]["messages"] += ["λ", "📚", "a", "b"]
    result = score(value)
    assert result["compact"]["total_tokens"] == 750 + 1 + 1 + 1 + 1
    assert [item["bytes"] for item in result["compact"]["messages"]] == [3000, 2, 4, 1, 1]


@pytest.mark.parametrize("canonical_tokens,compact_tokens,eligible", [
    (2000, 1000, True), (2002, 1001, False), (1000, 501, False),
])
def test_both_numeric_gates_use_inclusive_integer_boundaries(
    canonical_tokens, compact_tokens, eligible,
):
    value = capture()
    for arm, count in (("canonical", canonical_tokens), ("compact", compact_tokens)):
        value[arm]["body"] = arm[0] * (count * 4)
        value[arm]["messages"] = [value[arm]["body"]]
    assert score(value)["eligible"] is eligible


@pytest.mark.parametrize("bad", [True, -1, 0, 1.5])
def test_invalid_estimator_count_is_rejected(bad):
    class Counter(EstimatedCounter):
        def count(self, text):
            return bad

    value = capture()
    with pytest.raises(ValueError):
        score_first_use(value, expected_sha256=record_sha256(value), counter=Counter())


def test_changed_estimator_identity_is_rejected():
    class Counter(EstimatedCounter):
        def count(self, text):
            self.identity = "changed"
            return super().count(text)

    value = capture()
    with pytest.raises(ValueError):
        score_first_use(value, expected_sha256=record_sha256(value), counter=Counter())
