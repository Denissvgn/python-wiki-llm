"""Complete scanner evidence is required before applying the HIGH/HIGH gate."""

from copy import deepcopy
import itertools
from pathlib import Path

import pytest

from release import static_checks as checks
from tests.bandit_fixtures import COMMAND, RANKS, RUN_ID, observation, raw, report, source


def evaluate(value=None, *, log=b"", record_changes=None):
    payload = raw(report() if value is None else value)
    record = observation(payload, log, **(record_changes or {}))
    return checks.evaluate_bandit(payload, log, record, run_id=RUN_ID, command=COMMAND, source=source())


@pytest.mark.parametrize("severity,confidence", list(itertools.product(RANKS, repeat=2)))
def test_every_pinned_ranking_pair_preserves_high_high_policy(severity, confidence):
    result = evaluate(report([(severity, confidence)]))
    expected = (severity, confidence) == ("HIGH", "HIGH")
    assert result["decision"]["blocking_findings"] == int(expected)
    assert result["decision"]["passed"] is not expected
    assert result["tool"]["version"] == checks.PINNED_BANDIT


def test_pinned_tool_contract_matches_both_committed_locks():
    root = Path(__file__).parents[1]
    for name in ("requirements.in", "requirements.txt"):
        assert f"bandit=={checks.PINNED_BANDIT}" in (root / "release" / name).read_text()


def test_reordering_findings_preserves_decision_but_rebinds_exact_report_bytes():
    value = report([("LOW", "HIGH"), ("HIGH", "HIGH"), ("UNDEFINED", "LOW")])
    before = evaluate(value)
    value["results"].reverse()
    after = evaluate(value)
    assert before["decision"] == after["decision"]
    assert before["report_sha256"] != after["report_sha256"]
    assert before["execution_sha256"] != after["execution_sha256"]
    assert after == evaluate(value)


@pytest.mark.parametrize("field,value", [
    ("run_id", "2" * 32), ("schema_version", "future"), ("error", "timeout"), ("returncode", None),
    ("returncode", True), ("returncode", 2), ("returncode", 0), ("report_sha256", "0" * 64),
    ("log_sha256", "0" * 64), ("report_bytes", 0), ("elapsed_ns", True), ("elapsed_ns", -1),
    ("tool", {"name": "bandit", "version": "future"}), ("source", {}), ("command", []),
    ("started_at", "2026-09-22T00:00:00"),
])
def test_stale_failed_or_mismatched_execution_is_rejected(field, value):
    with pytest.raises(ValueError):
        evaluate(record_changes={field: value})


def test_incomplete_execution_record_is_not_a_completed_scan():
    payload = raw(report())
    record = observation(payload)
    del record["error"]
    with pytest.raises(ValueError):
        checks.evaluate_bandit(payload, b"", record, run_id=RUN_ID, command=COMMAND, source=source())


@pytest.mark.parametrize("mutation", ["shape", "errors", "timestamp", "missing-field", "unknown-ranking",
    "bool-line", "empty-range", "missing-metric", "bad-total", "bool-count", "truncated-results", "unknown-file", "cwe"])
def test_incomplete_or_inconsistent_full_reports_cannot_pass(mutation):
    value = report()
    if mutation == "shape":
        value["extra"] = "unsupported"
    elif mutation == "errors":
        value["errors"] = [{"reason": "parse failed"}]
    elif mutation == "timestamp":
        value["generated_at"] = "not a timestamp"
    elif mutation == "missing-field":
        del value["results"][0]["issue_confidence"]
    elif mutation == "unknown-ranking":
        value["results"][0]["issue_confidence"] = "CRITICAL"
    elif mutation == "bool-line":
        value["results"][0]["line_number"] = True
    elif mutation == "empty-range":
        value["results"][0]["line_range"] = []
    elif mutation == "missing-metric":
        del value["metrics"]["source.py"]["SEVERITY.LOW"]
    elif mutation == "bad-total":
        value["metrics"]["_totals"]["loc"] = 999
    elif mutation == "bool-count":
        value["metrics"]["_totals"]["loc"] = True
    elif mutation == "truncated-results":
        value["results"] = []
    elif mutation == "unknown-file":
        value["results"][0]["filename"] = "other.py"
    else:
        value["results"][0]["issue_cwe"] = {"id": True, "link": "invalid"}
    with pytest.raises(ValueError):
        evaluate(value)


@pytest.mark.parametrize("payload", [b'{}', b'{"results":[],"results":[]}', b'{"metrics":NaN}', b'not json'])
def test_noncanonical_or_malformed_json_is_rejected(payload):
    with pytest.raises(ValueError):
        checks.validate_bandit_report(payload)


@pytest.mark.parametrize("log", [b"[tester]\tERROR\tBandit internal error running: owned\n", b"[main] CRITICAL stopped\n"])
def test_logged_plugin_failure_cannot_pass_with_exit_zero_and_no_json_errors(log):
    with pytest.raises(ValueError, match="analysis failure"):
        evaluate(report([]), log=log)


def test_valid_but_reduced_scan_scope_is_rejected():
    payload = raw(report([]))
    scope = deepcopy(source())
    scope["files"]["omitted.py"] = "0" * 64
    record = observation(payload, source=scope)
    with pytest.raises(ValueError, match="complete source scope"):
        checks.evaluate_bandit(payload, b"", record, run_id=RUN_ID, command=COMMAND, source=scope)
