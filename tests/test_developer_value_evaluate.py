"""Provider observations remain distinct from missing future capabilities."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.developer_value import evaluate, runtime
from tests.developer_value.oracles import verify_corpus


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def prepared(tmp_path):
    api = runtime.load_provider(ROOT)

    def make(identity):
        spec = next(case for case in verify_corpus()["cases"] if case["id"] == identity)
        root = tmp_path / identity
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            runtime.prepare_workspace(spec["project"], root)
        return api, spec, root

    return make


def check_by_id(result, identity):
    return next(check for check in result["checks"] if check["id"] == identity)


def test_corrupt_required_native_read_is_rejected_without_repair(prepared):
    api, spec, root = prepared("S07")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "passed"
    assert check_by_id(result, "native-before-corruption")["state"] == "passed"
    assert check_by_id(result, "corrupt-required-read-rejected")["state"] == "passed"
    assert check_by_id(result, "corrupt-read-no-repair")["state"] == "passed"
    after = next(event for event in result["events"] if event["step"].get("api") == "build_task_context"
                 and event["step"]["stage"] == "after")
    assert after["outcome"] == "error" and after["error"]["message"]
    assert (root / "wiki/.llm-wiki-knowledge.json").read_text() == "{broken"
    assert result["model_execution_established"] is result["field_evidence_established"] is False


def test_source_only_budget_gap_keeps_actual_missing_evidence(prepared):
    api, spec, root = prepared("L08")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "passed"
    assert not (root / "wiki").exists()
    assert (root / "retained-unused-wiki").is_dir()
    assert check_by_id(result, "native-mode-off")["observed"] == "off"
    assert check_by_id(result, "tiny-budget-explicit-gap")["observed"] == "cannot-fit"
    before = next(event["result"] for event in result["events"] if event["step"].get("api") == "build_task_context"
                  and event["step"]["stage"] == "before")
    assert before["canonical_validation"] == "passed"
    coverage = {row["requirement_id"]: row for row in before["payload"]["coverage"]}
    assert coverage["contract"]["satisfied"] is True
    assert coverage["behavior"]["state"] == "unsupported" and not coverage["behavior"]["satisfied"]
    assert coverage["callers"]["satisfied"] is False


def test_resumed_context_invalidates_source_and_agrees_with_cold_read(prepared):
    api, spec, root = prepared("G02")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "passed"
    assert check_by_id(result, "source-mutation-invalidates-identity")["observed"] is True
    assert check_by_id(result, "cold-session-equivalence")["observed"] is True
    assert check_by_id(result, "stale-render-not-reused")["observed"] is False
    assert all(check["state"] == "passed" for check in result["checks"])


def test_future_implementation_comparison_is_unavailable_despite_independent_behavior(prepared):
    api, spec, root = prepared("L01")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "unavailable"
    implementation = check_by_id(result, "provider-implementation-comparison")
    assert implementation["state"] == "unavailable" and implementation["observed"] is None
    assert check_by_id(result, "owned-behavior-before")["observed"] is True
    assert check_by_id(result, "owned-behavior-after")["observed"] is False
    after = next(event["result"] for event in result["events"] if event["step"].get("api") == "inspect_concept"
                 and event["step"]["stage"] == "after")
    concept = evaluate._inspection_concept(after)
    assert concept["freshness"]["state"] == "nonsemantic-source-change"


def test_ordinary_acknowledgment_never_simulates_success_or_human_approval(prepared):
    api, spec, root = prepared("S06")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "unavailable"
    probes = [event for event in result["events"] if "acknowledgment" in event["step"].get("action", "")]
    assert len(probes) == 4
    assert all(event["outcome"] == "unavailable" and event["result"]["attempted_mutation"] is False for event in probes)
    assert all(event["result"]["human_approval"] == "not-observed" for event in probes)
    assert check_by_id(result, "authored-prose-preserved")["state"] == "passed"


def test_bounded_inventory_has_explicit_policy_and_partial_coverage(prepared):
    api, spec, root = prepared("G01")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "passed"
    assert check_by_id(result, "selected-one-file")["observed"] == 1
    assert check_by_id(result, "full-inventory-file-count")["observed"] == 102
    assert check_by_id(result, "bounded-graph-partial")["observed"] == "partial"
    assert check_by_id(result, "bounded-complete-graph-unsatisfied")["observed"] is False


def test_restart_uses_real_fresh_provider_process_but_cannot_prove_missing_review(prepared):
    api, spec, root = prepared("S05")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "unavailable"
    assert check_by_id(result, "fresh-process-observed")["state"] == "passed"
    event = next(event for event in result["events"] if event["step"].get("fresh_process"))
    assert event["result"]["fresh_process"]["exit_code"] == 0
    assert event["result"]["payload"]["schema_version"] == "llm-wiki-maintenance-queue/v1"
    assert check_by_id(result, "ordinary-durable-review")["state"] == "unavailable"


def test_failed_search_query_keeps_raw_error_and_denominator():
    manifest = verify_corpus()
    api = SimpleNamespace(search_wiki=lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("owned search failure")))
    rows, observations = evaluate._queries(api, manifest, {"E1"})
    assert len(rows) == 1 and rows[0]["outcome"] == "error"
    assert rows[0]["error"]["message"] == "owned search failure"
    assert observations == {}
    score = evaluate.score_retrieval(manifest, observations)
    assert score["answerable"]["expected_targets"] == 33
    assert score["answerable"]["recovered_targets"] == 0
    assert len(score["missing_observations"]) == 40
    assert score["unanswerable"]["definitive_claims"] is None


def test_search_keeps_raw_bounds_and_does_not_invent_answer_claims():
    manifest = verify_corpus()
    raw = {"results": [{"path": "modules/policy.md"}, {"path": "entities/Batch.md"}],
           "returned": 2, "total": 8, "truncated": True, "mode": "ranked"}
    api = SimpleNamespace(search_wiki=lambda *args, **kwargs: raw)
    rows, observations = evaluate._queries(api, manifest, {"E1"})
    assert rows[0]["result"] == raw
    assert observations == {"E1": raw["results"]}
    score = evaluate.score_retrieval(manifest, observations)
    assert score["queries"][0]["targets_at_five"] == ["source:policy.py"]
    assert score["unanswerable"]["definitive_claims"] is None


def test_malformed_search_rows_are_retained_as_errors_without_scoring_success():
    raw = {"results": [{}], "total": 1, "returned": 1}
    api = SimpleNamespace(search_wiki=lambda *args, **kwargs: raw)
    rows, observations = evaluate._queries(api, verify_corpus(), {"E1"})
    assert rows[0]["outcome"] == "error"
    assert rows[0]["result"] == raw
    assert "lacks a target" in rows[0]["error"]["message"]
    assert observations == {}


def test_workspace_failures_keep_all_scheduled_cases_and_query_denominators(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise ValueError("owned preparation failure")

    monkeypatch.setattr(runtime, "prepare_workspace", unavailable)
    output = tmp_path / "evaluation.json"
    result = evaluate.run(ROOT, output)
    assert result["case_counts"] == {"error": 20}
    assert result["query_counts"] == {"error": 40}
    assert len(result["cases"]) == 20 and len(result["queries"]) == 40
    assert result["retrieval"]["all"]["answerable"]["expected_targets"] == 33
    assert result["retrieval"]["all"]["answerable"]["recovered_targets"] == 0
    assert len(result["retrieval"]["all"]["missing_observations"]) == 40
    assert result["retrieval"]["all"]["unanswerable"]["definitive_claims"] is None
    assert result["provider_unchanged"] is True
    assert result["model_execution_established"] is result["field_evidence_established"] is False
    assert json.loads(output.read_bytes()) == result


def test_cli_requires_both_provider_and_output_before_execution(monkeypatch):
    monkeypatch.setattr(evaluate, "run", lambda *args: pytest.fail("invalid CLI started evaluation"))
    with pytest.raises(SystemExit) as failure:
        evaluate.main(["--output", "unused.json"])
    assert failure.value.code == 2


def test_prose_case_observes_real_owning_sync_and_validates_protected_artifacts(prepared):
    api, spec, root = prepared("G03")
    result = evaluate.observe_case(api, spec, root)
    assert result["status"] == "passed"
    assert check_by_id(result, "description-prose-preserved")["observed"] is True
    assert check_by_id(result, "second-sync-idempotent")["observed"] is True
    assert check_by_id(result, "protected-artifacts-validated")["observed"] is True
    assert json.dumps(result, sort_keys=True)


@pytest.mark.parametrize("defect", ["missing-selected", "degraded", "unsupported", "unavailable-coverage", "wrong-selected", "unavailable-result"])
def test_nonempty_integrity_diagnostic_cannot_pass_prose_case(prepared, defect):
    api, spec, root = prepared("G03")
    with evaluate._cwd(root):
        ready = api.inspect_concept(spec["selector"], src_dir="src", wiki_dir="wiki")
    diagnostic = deepcopy(ready)
    if defect == "missing-selected":
        diagnostic["concept"]["found"] = False
        diagnostic["concept"]["concept"] = None
    elif defect in {"degraded", "unsupported"}:
        diagnostic["concept"]["knowledge"]["availability"] = defect
    elif defect == "unavailable-coverage":
        diagnostic["coverage"]["availability"] = "absent"
    elif defect == "wrong-selected":
        diagnostic["concept"]["concept"]["canonical_path"] = "modules/other.md"
    else:
        diagnostic["status"] = "unavailable"
    controlled = SimpleNamespace(inspect_concept=lambda *args, **kwargs: diagnostic)
    result = evaluate.observe_case(controlled, spec, root)
    observed = check_by_id(result, "protected-artifacts-validated")
    assert observed["state"] == "failed" and observed["observed"] is False
    assert result["status"] == "failed"
    raw = next(event for event in result["events"] if event["step"].get("action") == "validate-protected-artifacts")
    assert raw["result"] == diagnostic


def test_missing_integrity_response_remains_unavailable():
    assert evaluate._selected_integrity_ready(None, "modules/search.md") is None
