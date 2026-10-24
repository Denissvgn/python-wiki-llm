"""Bounded human views must retain complete, unchanged diagnostic evidence."""

from copy import deepcopy
import json

import pytest

from llm_wiki_cli.commands import ci_check_cmd
from llm_wiki_cli.services import ci_report, health_summary, lint_service
from tests.test_health_details import _ci, _report


def _gap(kind, index=0):
    return lint_service.LintIssue(
        "data_flow_gaps", f"Data-flow gap in checkout: {kind} entry -> target{index} line 7",
        "warning", target="checkout",
    )


def _mixed():
    return [*(_gap("external_call", n) for n in range(30)),
            _gap("unresolved_call"), _gap("step_limit"), _gap("truncated_flow"),
            lint_service.LintIssue("data_flow_gaps", "external_call is only quoted here", "warning"),
            lint_service.LintIssue("consumer-info", "Unknown consumer advisory", "info"),
            lint_service.LintIssue("knowledge_freshness", "Execution runtime differs", "warning",
                                   hint="Capture on the intended target host.")]


def test_priority_and_kind_counts_reconcile_without_mutating_records():
    report = lint_service.LintReport("wiki", "src", diagnostics=_mixed())
    raw = lint_service.report_to_dict(report)
    before = deepcopy(raw)
    groups = health_summary.diagnostic_groups(raw["diagnostics"])
    counts = {(g["category"], g["kind"]): len(g["records"]) for g in groups}
    assert counts[("data_flow_gaps", "external_call")] == 30
    for kind in ("unresolved_call", "step_limit", "truncated_flow", "unclassified"):
        assert counts[("data_flow_gaps", kind)] == 1
    assert sum(counts.values()) == len(raw["diagnostics"]) == 36
    assert groups[0]["category"] == "knowledge_freshness"
    assert groups[-1]["kind"] == "external_call"
    assert raw == before


def test_markdown_starts_with_actionable_cause_and_retains_every_record():
    report = lint_service.LintReport("wiki", "src", diagnostics=_mixed())
    before = lint_service.report_to_dict(report)
    text = lint_service.render_markdown(report)
    assert text.index("Execution runtime differs") < 4096
    assert text.index("Capture on the intended target host") < 4096
    assert "Complete diagnostic index" in text and "#diagnostic-group-" in text
    assert "every original field.\n\n- `knowledge_freshness`" in text
    assert "emitted diagnostic records" in text and "not scan coverage" in text
    assert "preview" in text and "omitted" in text
    assert "external_call" in text and "unresolved_call" in text
    for finding in report.diagnostics:
        assert finding.message in text
    assert lint_service.report_to_dict(report) == before
    report.diagnostics.reverse()
    assert lint_service.render_markdown(report) == text


def test_text_preview_prioritizes_uncertain_calls_with_exact_kind_totals():
    report = lint_service.LintReport("wiki", "src", diagnostics=_mixed())
    before = lint_service.report_to_dict(report)
    text = lint_service.render_text(report)
    assert "unresolved_call=1" in text and "external_call=30" in text
    assert text.index("unresolved_call entry") < text.index("external_call entry")
    assert "Showing 5 of 34 record(s); 29 omitted" in text
    assert lint_service.report_to_dict(report) == before


@pytest.mark.parametrize("size", [0, 1, 5000])
def test_empty_small_and_large_views_reconcile_exact_preview_bounds(size):
    records = [_gap("external_call", n) for n in range(size)]
    report = lint_service.LintReport("wiki", "src", diagnostics=records)
    raw = lint_service.report_to_dict(report)
    summary = health_summary.diagnostic_preview(raw["diagnostics"])
    assert summary["total"] == size
    assert summary["returned"] + summary["omitted"] == size
    assert summary["returned"] <= 8
    assert len(summary["groups"]) <= 8
    assert report.passed and report.issue_count == 0
    text = lint_service.render_markdown(report)
    assert "No issues found." in text
    assert all(record.message in text for record in records)


def test_blocking_issues_and_unknown_kinds_remain_visible_and_blocking():
    report = lint_service.LintReport("wiki", "src", issues=[
        lint_service.LintIssue("broken_links", "Missing target", path="index.md"),
    ], diagnostics=[_gap("new_unknown_call"), _gap("external_call")])
    text = lint_service.render_markdown(report)
    assert not report.passed and report.issue_count == 1
    assert text.index("Missing target") < text.index("## Diagnostics")
    groups = health_summary.diagnostic_groups(lint_service.report_to_dict(report)["diagnostics"])
    assert groups[0]["kind"] == "new_unknown_call"
    assert groups[-1]["kind"] == "external_call"


@pytest.mark.parametrize("schema", ["v1", "v2", "v3"])
def test_ci_full_report_presents_health_before_routine_rows_and_keeps_wire(tmp_path, schema):
    report = _report(tmp_path, "producer-changed")
    report.diagnostics[:0] = [_gap("external_call", n) for n in range(100)]
    payload = _ci(report, schema=schema)
    before = deepcopy(payload)
    text = ci_report.render_ci_markdown(payload, cli_exit=0)
    assert text.index("Knowledge health: degraded") < 4096
    assert text.index("Next action") < 4096
    assert "Release policy: unavailable" in text and "Human review:" in text
    assert payload == before
    assert "Knowledge health: degraded" in ci_check_cmd._render_console(report, "markdown")[:4096]
    assert json.loads(json.dumps(payload)) == before


def test_summary_falls_back_for_missing_targets_and_keeps_explicit_omissions():
    records = [{"category": f"custom-{n}", "severity": "warning", "message": f"Record {n}"}
               for n in range(20)]
    records += [{"category": "data_flow_gaps", "severity": "warning",
                 "message": "Data-flow gap in checkout: external_call entry -> target", "target": "other"}]
    view = health_summary.diagnostic_preview(records)
    assert view["returned"] == 8 and view["omitted"] == 13
    assert len(view["groups"]) == 8
    groups = health_summary.diagnostic_groups(records)
    assert next(g for g in groups if g["category"] == "data_flow_gaps")["kind"] == "unclassified"


def test_legacy_skip_context_is_unavailable_without_live_reclassification():
    report = lint_service.LintReport("wiki", "src", diagnostics=[
        lint_service.LintIssue("unscanned_manifest_scopes", "Captured manifest scope <none>", "warning"),
    ])
    before = lint_service.report_to_dict(report)
    text = lint_service.render_markdown(report)
    assert "Exact manifest and ownership/cause were not recorded" in text
    assert "unused packages or unprepared helpers" in text
    assert lint_service.report_to_dict(report) == before


def test_captured_full_report_never_reads_source_or_runs_tools(tmp_path, monkeypatch):
    from pathlib import Path
    import subprocess

    payload = _ci(_report(tmp_path, "producer-changed"))
    def reject(*args, **kwargs):
        pytest.fail("captured report rendering must not read source or execute tools")
    monkeypatch.setattr(Path, "read_bytes", reject)
    monkeypatch.setattr(Path, "read_text", reject)
    monkeypatch.setattr(subprocess, "run", reject)
    assert "Complete diagnostic index" in ci_report.render_ci_markdown(payload, cli_exit=0)
