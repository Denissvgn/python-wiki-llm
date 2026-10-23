"""Decision and assurance claims must follow captured evidence and policy."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import runpy

import pytest

from llm_wiki_cli.commands import ci_check_cmd
from llm_wiki_cli.services import ci_report, doctor_service, lint_service
from llm_wiki_cli.services import health_summary, knowledge_verification
from llm_wiki_cli.services import verification_contracts as vc
from llm_wiki_cli.services.health_details import capture_health_details
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_observability import KnowledgePhaseDurations
from tests.knowledge_fixtures import fixture_hash
from tests.test_ci_check import _render_summary
from tests.test_health_details import _ci, _doctor, _report
from tests.test_knowledge_maintenance import RELEASE, config, evidence, raw
from tests.test_knowledge_verification_view import _context
from tests.test_knowledge_cmd import _run as _knowledge_command
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_health_refresh import recorded_project as recorded_project


ROOT = Path(__file__).parents[1]
DASHBOARD = runpy.run_path(str(ROOT / "integrations/github-action/render_summary.py"))


def _integrity_summary(payload):
    code = payload.get("command_exit_code", 0 if payload["ok"] else 1)
    return _render_summary(
        payload, result="PASS" if code == 0 else "FAIL", cli_exit=code,
        json_state=f"available (validated {payload['schema_version']})",
    ).decode()


@pytest.mark.parametrize("schema", ["v1", "v2", "v3"])
@pytest.mark.parametrize("scenario,status,exit_code", [
    ("current", "healthy", 0), ("producer-changed", "degraded", 1),
])
def test_integrity_and_advisory_health_remain_separate(tmp_path, schema, scenario, status, exit_code):
    report = _report(tmp_path, scenario)
    payload = _ci(report, schema=schema)
    before = deepcopy(payload)
    text = _integrity_summary(payload)
    assert "Structural integrity: `passed` (strict; blocking)" in text
    assert f"Knowledge health: `{status}` (exit {exit_code}; non-strict; advisory)" in text
    assert "Native drift: `report-only` (advisory)" in text
    assert "Release policy: `unavailable`" in text
    assert "Human review:" in text and "not established" in text
    assert payload == before and payload["ok"] is True
    assert len(text.splitlines()) <= 40 and len(text.encode()) <= 8192


def test_structural_failure_does_not_relabel_healthy_knowledge(tmp_path):
    report = _report(tmp_path)
    report.issues.append(lint_service.LintIssue(category="broken_link", message="Broken link."))
    text = _integrity_summary(_ci(report))
    assert "Structural integrity: `failed` (strict; blocking)" in text
    assert "Knowledge health: `healthy` (exit 0; non-strict; advisory)" in text


@pytest.mark.parametrize("recorded_project", ["current"], indirect=True)
def test_native_report_keeps_its_v4_contract_and_decision_separation(recorded_project):
    report = lint_service.build_report(
        "wiki", "source", strict=True, knowledge_drift_report=True, include_health_details=True,
    )
    payload = _ci(report, schema="v4")
    ci_report.validate_ci_check_payload(payload, cli_exit=0)
    text = _integrity_summary(payload)
    assert payload["knowledge_health"]["schema_version"] == "llm-wiki-doctor/v4"
    assert "Structural integrity: `passed` (strict; blocking)" in text
    assert "Release policy: `unavailable`" in text
    assert len(text.splitlines()) <= 40 and len(text.encode()) <= 8192


@pytest.mark.parametrize("drift", [False, True])
@pytest.mark.parametrize("output_format", ["text", "markdown"])
def test_full_ci_reports_disclose_modes_without_changing_json(tmp_path, drift, output_format):
    report = _report(tmp_path, "producer-changed")
    report.knowledge_drift_report = drift
    wire = ci_check_cmd._render_console(report, "json", report_schema="v1")
    text = ci_check_cmd._render_console(report, output_format)
    assert "Structural integrity: passed (strict; blocking)" in text
    assert "Knowledge health: degraded (exit 1; non-strict; advisory)" in text
    assert f"Native drift: {'report-only (advisory)' if drift else 'disabled'}" in text
    assert "Release policy: unavailable" in text
    assert ci_check_cmd._render_console(report, "json", report_schema="v1") == wire


@pytest.mark.parametrize("strict,status,code", [(False, "degraded", 1), (True, "unhealthy", 2)])
def test_doctor_classification_is_not_release_admission(tmp_path, strict, status, code):
    payload = _doctor(_report(tmp_path, "producer-changed"), strict=strict)
    before = deepcopy(payload)
    text = doctor_service._render_doctor_payload(payload)
    assert f"{status} (exit {code})" in text
    assert f"Health classification: {'strict;' if strict else 'non-strict;'}" in text
    assert "Release policy: unavailable" in text
    summary = DASHBOARD["render_summary"](payload, fail_on="unhealthy")
    assert "| Release policy | `unavailable" in summary
    assert "| Action failure threshold | `unhealthy or absent` |" in summary
    assert "Human review" in summary
    assert "`LLM Wiki integrity`.\n\n| Check | Result |" in summary
    assert "|\n\nEvaluated does not mean current." in summary
    assert len(summary.splitlines()) <= 40 and len(summary.encode()) <= 8192
    assert payload == before


@pytest.mark.parametrize("state,health_status,recorded", [
    ("absent", "healthy", None), ("valid", "healthy", "passed"),
    ("stale", "unhealthy", "passed"), ("failed", "unhealthy", "failed"),
    ("invalid", "unhealthy", None),
])
def test_machine_assurance_uses_real_receipts_and_preserves_validity(tmp_path, state, health_status, recorded):
    report = _report(tmp_path)
    view = report.knowledge_view
    assert view is not None
    if state == "invalid":
        (tmp_path / vc.VERIFICATION_RECEIPT_FILENAME).write_text("invalid receipt")
    elif state != "absent":
        context = _context(
            view, knowledge_hash=fixture_hash("old") if state == "stale" else None,
            artifact_integrity=state != "failed",
            artifact_diagnostics=(vc.VerificationDiagnostic(code="manifest-hash-mismatch", subject="fixture"),)
            if state == "failed" else (),
        )
        vc.verify_and_write_receipt(tmp_path, context, [vc.ARTIFACT_INTEGRITY_CHECKER_ID])
    captured = knowledge_verification.load_machine_verification_read_view(tmp_path, view)
    view = replace(view, machine_verification=captured)
    report.knowledge_view = view
    lint_service._check_verification_receipt(report, view)
    payload = _doctor(report, strict=False)
    assert payload["status"] == health_status
    assert payload["verification_receipt"]["state"] == state
    assert payload["verification_receipt"]["recorded_result"] == recorded
    rows = dict(health_summary.assurance_rows(payload))
    assert state in rows["Machine verification"]
    if recorded:
        assert f"recorded={recorded}" in rows["Machine verification"]
    if state == "stale":
        assert "current_passed=False" in rows["Machine verification"]
    if state == "valid":
        assert "recorded scope/checks only" in rows["Machine verification"]
    assert "not established" in rows["Human review"]
    text = _integrity_summary(_ci(report))
    assert "Human review:" in text and "semantic approval" in text
    if state == "stale":
        for schema in ("v1", "v2", "v3"):
            stale = _ci(report, schema=schema)
            ci_report.validate_ci_check_payload(stale, cli_exit=1)
            assert stale["knowledge_health"]["verification_receipt"]["passed"] is False
            for changes in ({"passed": True}, {"state": "valid"}):
                copied = deepcopy(stale)
                copied["knowledge_health"]["verification_receipt"].update(changes)
                with pytest.raises(ci_report.CiCheckReportError):
                    ci_report.validate_ci_check_payload(copied, cli_exit=1)


@pytest.mark.parametrize("state,expired,reason,status", [
    ("not-present", 0, None, "healthy"),
    ("valid", 0, None, "healthy"),
    ("valid", 1, "review-expired", "degraded"),
    ("invalid", 0, "governance-missing", "unhealthy"),
])
def test_authority_and_review_are_independent_claims(tmp_path, state, expired, reason, status):
    report = _report(tmp_path)
    if state != "not-present":
        _knowledge_command(["init", "--wiki-dir", str(tmp_path), "--bundle-id", "kb_disclosure"])
        if state == "invalid":
            (tmp_path / ".llm-wiki-governance.json").unlink()
        loaded = load_knowledge_state(tmp_path, policy="degraded")
        view = build_knowledge_read_view(
            loaded, live_evaluation=_live_evaluation(loaded.knowledge) if loaded.knowledge else None,
        )
        report.knowledge_view = view
        report.issues.clear()
        report.diagnostics.clear()
        lint_service._check_knowledge_lint(report, lint_service._KnowledgeLintState(enabled=True, view=view))
        lint_service._set_knowledge_summary(report, view, durations=KnowledgePhaseDurations(0, 0, 0))
        report.health_details = capture_health_details(view, wiki_dir=str(tmp_path), src_dir=str(tmp_path))
    if expired:
        # Isolate the presentation of an already captured review-expiry finding;
        # the governance suite independently exercises real review invalidation.
        report.issues.append(lint_service.LintIssue(
            category="knowledge_review",
            message=f"Captured finding [reason={reason}].", reason_code=reason,
        ))
    payload = _doctor(report, strict=False)
    assert payload["status"] == status
    rows = dict(health_summary.assurance_rows(payload))
    if expired:
        assert "expired=1" in rows["Human review"]
    elif state == "invalid":
        assert "governance-missing" in rows["Governance authority"]
    else:
        assert "not established" in rows["Human review"]


@pytest.mark.parametrize("scenario", ["current", "producer-changed"])
@pytest.mark.parametrize("mutation", [None, "missing", "stale", "forged"])
def test_only_matching_release_policy_receipts_admit_the_required_gate(tmp_path, scenario, mutation):
    from llm_wiki_cli.services import health_policy as hp

    _, ci, preflight, binding = evidence(tmp_path / "wiki", scenario)
    receipt = hp.derive_policy(raw(ci), raw(preflight), binding=binding)
    assert receipt["status"] == ("pass" if scenario == "current" else "fail")
    assert hp.verify_policy(receipt, raw(ci), raw(preflight), binding=binding) == receipt
    folder = tmp_path / "evidence"
    folder.mkdir()
    for name, value in (("ci-report.json", ci), ("preflight.json", preflight), ("policy.json", receipt)):
        (folder / name).write_bytes(raw(value))
    identity = {"source": {"sha": binding["candidate_sha"], "tree": binding["candidate_tree"],
                           "archive_sha256": "d" * 64}, "version": binding["candidate_version"]}
    if mutation == "missing":
        (folder / "policy.json").unlink()
    elif mutation == "stale":
        identity["source"]["sha"] = "f" * 40
    elif mutation == "forged":
        receipt["status"], receipt["strict_health"] = "pass", "healthy"
        receipt["reasons"] = []
        receipt["report_sha256"] = "sha256:" + "0" * 64
        (folder / "policy.json").write_bytes(raw(receipt))
    result = RELEASE["admit"](folder, identity, config("required"))
    assert result["status"] == ("pass" if mutation is None and scenario == "current" else "fail")
    # Even a genuine required receipt does not turn ordinary CI into release admission.
    assert "Release policy: `unavailable`" in _integrity_summary(ci)


def test_rendering_is_read_only_and_never_runs_assurance_operations(tmp_path, monkeypatch):
    from llm_wiki_cli.services import extraction_service, knowledge_governance

    report = _report(tmp_path)
    ci, doctor = _ci(report), _doctor(report)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    def reject(*args, **kwargs):
        pytest.fail("reporting must not extract, verify, adopt or write authority")
    monkeypatch.setattr(extraction_service, "get_inventory_result", reject)
    monkeypatch.setattr(vc, "verify", reject)
    monkeypatch.setattr(knowledge_governance, "save_governance", reject)
    monkeypatch.setattr(knowledge_governance, "add_review_event", reject)
    monkeypatch.setattr(vc, "verify_and_write_receipt", reject)
    import subprocess
    monkeypatch.setattr(subprocess, "run", reject)
    _integrity_summary(ci)
    DASHBOARD["render_summary"](doctor)
    doctor_service._render_doctor_payload(doctor)
    ci_check_cmd._render_console(report, "markdown")
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert json.loads(json.dumps(ci)) == ci
