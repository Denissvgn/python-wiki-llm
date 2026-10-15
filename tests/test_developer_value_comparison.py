"""Comparison failures and missing capability never become successful evidence."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.developer_value import compare_cases, evaluate, runtime
from tests.developer_value.oracles import verify_corpus

ROOT = Path(__file__).resolve().parents[1]


def test_missing_attempts_stay_in_complete_denominator():
    summary = compare_cases.summarize([{"id": "A", "status": "passed"}, {"id": "B", "status": "error"}], ["A", "B", "C", "D"])
    assert summary == {"planned": 4, "observed": 2, "states": {"passed": 1, "error": 1, "not-run": 2}, "passed_fraction": 0.25}
    with pytest.raises(ValueError, match="duplicate"):
        compare_cases.summarize([{"id": "A", "status": "passed"}] * 2, ["A"])
    with pytest.raises(ValueError, match="unexpected"):
        compare_cases.summarize([{"id": "extra", "status": "passed"}], ["A"])


def test_direct_source_reads_keep_authored_information_and_native_gaps(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/logic.py").write_text('raise RuntimeError("must never run")\n')
    before = runtime.tree_hashes(tmp_path)
    result = compare_cases.direct_read(tmp_path, {"guide": "Author explains logic."}, "before")
    assert result["source"] == {"logic.py": 'raise RuntimeError("must never run")\n'}
    assert result["authored"] == {"guide": "Author explains logic."}
    assert result["source_executed"] is False
    assert result["native_guarantees"] == "unavailable" and result["task_solved"] == "unmeasured"
    assert runtime.tree_hashes(tmp_path) == before


@pytest.mark.parametrize("observed,state", [(None, "unavailable"), ("unchanged", "failed"), ("changed", "passed")])
def test_candidate_implementation_uses_actual_provider_evidence(tmp_path, observed, state):
    spec = deepcopy(verify_corpus()["cases"][0])
    implementation = {} if observed is None else {"state": observed, "limitations": ["dependencies-and-runtime-behavior-not-evaluated"]}
    case = compare_cases.ComparisonCase(SimpleNamespace(), spec, tmp_path)
    concept = {"implementation": implementation, "freshness": {"state": "nonsemantic-source-change"}}
    case.events = [{"step": {"stage": "after", "api": "inspect_concept"}, "outcome": "ok", "result": {"concept": {"concept": concept}}}]
    result = next(row for row in compare_cases.assess(case) if row["id"] == "provider-implementation-comparison")
    assert result["observed"] == observed and result["state"] == state
    assert evaluate._assess(case)[1]["state"] == "unavailable"  # original baseline adapter unchanged


@pytest.mark.parametrize("identity", ["L01", "L04", "S02", "S05", "S06"])
def test_current_provider_adapter_exercises_frozen_cases(tmp_path, identity):
    api = runtime.load_provider(ROOT)
    spec = next(case for case in verify_corpus()["cases"] if case["id"] == identity)
    runtime.prepare_workspace(spec["project"], tmp_path)
    result = compare_cases.observe(api, spec, tmp_path)
    assert result["status"] == "passed", result
    assert result["direct_source"]["required_provider_behavior"] == "unavailable"
    assert all(row["state"] == "passed" for row in result["checks"])
    if identity == "L01":
        review = next(row for row in result["checks"] if row["id"] == "changed-prose-review-pending")
        assert review["observed"] == "pending"


def test_unchecked_scheduled_error_cannot_be_a_pass(tmp_path):
    spec = next(case for case in verify_corpus()["cases"] if case["id"] == "L06")
    case = compare_cases.ComparisonCase(SimpleNamespace(), spec, tmp_path)
    case.events = [{"step": deepcopy(step), "outcome": "error", "error": {"type": "RuntimeError"}} for step in spec["observation_steps"]]
    row = next(row for row in compare_cases.assess(case) if row["id"] == "scheduled-observations-complete")
    assert row["state"] == "failed"


def test_only_expected_corruption_rejection_is_admitted(tmp_path):
    spec = next(case for case in verify_corpus()["cases"] if case["id"] == "S07")
    case = compare_cases.ComparisonCase(SimpleNamespace(), spec, tmp_path)
    case.events = [{"step": deepcopy(step), "outcome": "ok"} for step in spec["observation_steps"]]
    rejection = next(event for event in case.events if event["step"].get("api") == "build_task_context" and event["step"]["stage"] == "after")
    rejection.update(outcome="error", error={"type": "RuntimeError"})
    assert next(row for row in compare_cases.assess(case) if row["id"] == "scheduled-observations-complete")["state"] == "failed"
    rejection["error"] = {"type": "InvalidRequestError", "message": "root: invalid knowledge root"}
    assert next(row for row in compare_cases.assess(case) if row["id"] == "scheduled-observations-complete")["state"] == "passed"


def test_comparison_rejects_information_mismatch_and_preserves_missing_cases():
    from tests.developer_value.oracles import corpus_identity
    report = {"schema_version": compare_cases.SCHEMA, "corpus_identity": corpus_identity(),
              "provider_unchanged": True, "harness_unchanged": True, "harness_before": {},
              "heldout_retrieval_replayed": False, "cases": [{"id": "L01", "status": "passed",
              "direct_source": {"reads": [{"stage": "before", "source_hashes": {"policy.py": "one"}, "authored_hashes": {"guide": "same"}}]}}]}
    candidate = deepcopy(report)
    result = compare_cases.compare_reports(report, candidate)
    assert result["summaries"]["candidate"]["states"] == {"passed": 1, "not-run": 19}
    assert result["information_parity_verified"] == 1
    assert result["direct_source_provider_success_fraction"] == "unavailable"
    candidate["cases"][0]["direct_source"]["reads"][0]["authored_hashes"]["guide"] = "changed"
    with pytest.raises(ValueError, match="information differs"):
        compare_cases.compare_reports(report, candidate)
