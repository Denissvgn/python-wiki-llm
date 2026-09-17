"""Falsifiable owned task inputs, claim scoring and patch oracle controls."""

from pathlib import Path
import shutil

import pytest

from tests.native_workflow.oracles import (
    observe_owned_retry_patch, score_claims, source_facts, summarize_attempts, verify_corpus,
)

ROOT = Path(__file__).parent / "native_workflow"


def test_frozen_inputs_cover_all_twelve_families_without_oracle_leakage():
    manifest = verify_corpus(ROOT)
    assert {task["language"] for task in manifest["tasks"]} == {
        "python", "typescript", "go", "rust", "haskell"}
    assert all(task["runtime"]["admitted"] is False for task in manifest["tasks"])


def test_source_observer_preserves_owner_default_order_and_never_imports(tmp_path):
    path = tmp_path / "source.py"
    path.write_text('raise RuntimeError("must not execute")\nclass Owner:\n'
                    '    def limit(self, amount: int = 3, *, force=False):\n        return amount\n'
                    'class Other:\n    def limit(self, amount=9):\n        return amount\n')
    facts = source_facts(path)
    methods = [fact for fact in facts["declarations"] if fact["kind"] == "method"]
    assert [(fact["owner"], fact["line"]) for fact in methods] == [("Owner", 3), ("Other", 6)]
    assert [p["name"] for p in methods[0]["params"]] == ["self", "amount", "force"]
    assert methods[0]["params"][1]["default"] == "3"
    assert methods[0]["params"][2]["kind"] == "keyword_only"


@pytest.mark.parametrize("mutation", ["owner", "default", "citation", "missing", "stale", "unsupported"])
def test_wrong_or_missing_evidence_fails_its_fact(mutation):
    truth = {"limit": {"value": {"owner": "Owner", "default": 3},
                       "citation": {"path": "source.py", "line": 3}}}
    claim = {"id": "limit", "status": "supported", "value": dict(truth["limit"]["value"]),
             "citation": dict(truth["limit"]["citation"])}
    assert score_claims(truth, [claim, claim])["present"] == ["limit"]
    if mutation in {"owner", "default"}:
        claim["value"][mutation] = "Other" if mutation == "owner" else 9
    elif mutation == "citation":
        claim["citation"]["line"] = 6
    elif mutation == "stale":
        claim["freshness"] = "stale"
    elif mutation == "unsupported":
        claim["status"] = "unsupported"
    result = score_claims(truth, [] if mutation == "missing" else [claim])
    assert result["present"] == [] and result["missing"] == ["limit"]
    assert result["coverage"] == 0


def test_unsupported_unknown_cannot_become_fact_and_conflict_is_retained():
    truth = {"cpp": {"state": "unsupported"}}
    unknown = {"id": "cpp", "status": "unsupported"}
    assert score_claims(truth, [unknown])["qualified_unknowns"] == ["cpp"]
    false_claim = {"id": "cpp", "status": "supported", "value": "evaluated"}
    assert score_claims(truth, [false_claim])["wrong_claims"] == 1


def test_owned_patch_oracle_separates_compilation_process_and_correctness(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(ROOT / "fixtures/T01/project", project)
    baseline = observe_owned_retry_patch(project)
    assert baseline["compiled"] and baseline["process_exit"] == 0
    assert baseline["oracle_passed"] is False
    source = (project / "retry.py").read_text()
    (project / "retry.py").write_text(source.replace("attempts: int = 3", "attempts: int = 4"))
    wrong_patch = observe_owned_retry_patch(project)
    assert wrong_patch["compiled"] and wrong_patch["process_exit"] == 0
    assert wrong_patch["oracle_passed"] is False
    (project / "retry.py").write_text(source.replace("range(attempts - 1)", "range(attempts)")
                                      .replace("attempt == attempts - 2", "attempt == attempts - 1"))
    assert observe_owned_retry_patch(project)["oracle_passed"] is True


def test_failed_cancelled_unavailable_attempts_stay_in_denominator():
    attempts = [{"id": str(i), "status": status} for i, status in enumerate(
        ("passed", "failed", "cancelled", "timed-out", "unsupported", "unavailable", "integration-failed"))]
    result = summarize_attempts(attempts)
    assert result["attempts"] == 7 and set(result["categories"].values()) == {1}
    assert result["model_execution_established"] is False
    with pytest.raises(ValueError):
        summarize_attempts([attempts[0], attempts[0]])
