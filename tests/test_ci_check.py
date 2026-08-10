"""Tests for ci-check command integration."""

from __future__ import annotations

import json
import os
import sys
import types
from copy import deepcopy
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import ci_check_cmd
from llm_wiki_cli.commands.lint_cmd import (
    KnowledgeLintSummary,
    LintIssue,
    LintReport,
)
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.services import ci_report, plugins
from llm_wiki_cli.services.contracts import (
    CI_CHECK_SCHEMA_VERSION,
    DOCTOR_SCHEMA_VERSION,
    PROTOCOL_VERSIONS,
)
from llm_wiki_cli.services.extraction_jobs import ExtractionJobPlan
from llm_wiki_cli.services.lint_service import report_to_dict


def _empty_execution_payload() -> dict:
    return {
        "extractor_jobs": {
            "requested_jobs": 1,
            "resolved_jobs": 1,
            "eligible_parallel_plans": 0,
            "effective_workers": 0,
            "parallel_plan_ids": [],
            "sequential_plan_ids": [],
            "cache_elided_plan_ids": [],
        }
    }


def _assert_versioned_ci_payload(payload: dict) -> dict:
    assert payload["schema_version"] == CI_CHECK_SCHEMA_VERSION
    health = payload["knowledge_health"]
    assert health["schema_version"] == DOCTOR_SCHEMA_VERSION
    assert health["strict"] is False
    assert health["wiki_dir"] == payload["wiki_dir"]
    assert health["src_dir"] == payload["src_dir"]
    ci_report.validate_ci_check_payload(
        payload,
        cli_exit=0 if payload["ok"] else 1,
    )
    return health


def test_ci_check_schema_is_registered_and_generic_lint_shape_is_unchanged(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    report = LintReport(wiki_dir="wiki", src_dir=".", strict=True)

    generic = report_to_dict(report, include_execution=True)
    payload = ci_report.build_ci_check_payload(report)

    assert CI_CHECK_SCHEMA_VERSION in PROTOCOL_VERSIONS
    assert "schema_version" not in generic
    assert "knowledge_health" not in generic
    assert {key: payload[key] for key in generic} == generic
    health = _assert_versioned_ci_payload(payload)
    assert health["status"] == "absent"
    assert ci_report.validate_ci_check_payload(payload, cli_exit=0) is payload


def test_readme_documents_the_versioned_ci_health_envelope() -> None:
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    section = readme.split("### `lint` and `ci-check`", 1)[1].split(
        "\n### `doctor`", 1
    )[0]

    assert "llm-wiki-ci-check/v1" in section
    assert "knowledge_health" in section
    assert "llm-wiki-doctor/v1" in section
    assert "same lint report, not a second source scan" in section
    assert "authoritative blocking integrity" in section


def test_ci_check_validator_recomputes_nested_health_classification() -> None:
    report = LintReport(wiki_dir="missing-wiki", src_dir=".", strict=True)
    payload = ci_report.build_ci_check_payload(report)
    health = payload["knowledge_health"]
    assert isinstance(health, dict)
    health["status"] = "healthy"
    health["exit_code"] = 0

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="status does not match its sections",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_payload_composes_health_from_the_same_report_without_strict_drift(
    monkeypatch,
):
    report = LintReport(wiki_dir="wiki", src_dir="source", strict=True)
    seen = {}

    class _Health:
        def to_payload(self):
            return {"schema_version": DOCTOR_SCHEMA_VERSION}

    def fake_compose(lint, **kwargs):
        seen.update(lint=lint, **kwargs)
        return _Health()

    monkeypatch.setattr(ci_report, "compose_doctor_report", fake_compose)

    payload = ci_report.build_ci_check_payload(report)

    assert payload["knowledge_health"] == {"schema_version": DOCTOR_SCHEMA_VERSION}
    assert seen == {
        "lint": report,
        "strict": False,
        "wiki_dir": "wiki",
        "src_dir": "source",
    }


def _ready_knowledge_summary() -> KnowledgeLintSummary:
    freshness = {
        "basis-incompatible": 0,
        "current": 3,
        "nonsemantic-source-change": 0,
        "source-changed": 0,
        "source-missing": 0,
        "unknown": 3,
    }
    return KnowledgeLintSummary(
        availability="ready",
        reason="all-projection-commitments-match",
        concepts_evaluated=6,
        freshness_counts=freshness,
        evidence_issue_counts={"invalid": 0, "missing": 0, "unknown": 1},
        degraded_reason=None,
        phase_durations_ms={"load": 1, "evaluate": 2, "check": 3},
        freshness_evaluated=True,
        concepts_total=6,
        concepts_by_kind={"code-entity": 6},
        evidence_by_state={"present": 3},
        freshness_by_state=freshness,
    )


def _ready_ci_payload() -> dict:
    report = LintReport(wiki_dir="wiki", src_dir=".", strict=True)
    report.knowledge_summary = _ready_knowledge_summary()
    payload = ci_report.build_ci_check_payload(report)
    summary = report.knowledge_summary
    assert summary is not None
    counts = dict(summary.freshness_counts or {})
    payload["knowledge_health"] = {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "status": "healthy",
        "exit_code": 0,
        "strict": False,
        "wiki_dir": "wiki",
        "src_dir": ".",
        "availability": {
            "state": summary.availability,
            "reason": summary.reason,
            "usable": True,
        },
        "freshness": {
            "evaluated": True,
            "disclosure": summary.freshness,
            "concepts": summary.concepts_evaluated,
            "counts_by_state": dict(counts),
        },
        "snapshot_parity": {"state": "valid", "issue_count": 0, "reasons": []},
        "governance": {
            "state": "not-present",
            "ledger": "not-present",
            "projection": "not-present",
            "expired_reviews": 0,
            "issue_count": 0,
            "reasons": [],
        },
        "drift": {
            "state": "current",
            "confirmed_stale": 0,
            "indeterminate": 0,
            "nonsemantic_changes": 0,
            "counts_by_state": dict(counts),
            "diagnostic_count": 0,
            "reasons": [],
        },
        "verification_receipt": {
            "state": "absent",
            "reason": "verification-receipt-not-present",
            "recorded_result": None,
            "passed": None,
        },
        "degraded_reasons": [],
        "unhealthy_reasons": [],
    }
    ci_report.validate_ci_check_payload(payload, cli_exit=0)
    return payload


def test_ci_validator_binds_summary_and_health_to_one_evaluation() -> None:
    payload = _ready_ci_payload()
    payload["knowledge_health"]["freshness"]["disclosure"] = (
        "evaluated (999 concepts)"
    )

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="knowledge_summary.freshness does not match",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_validator_binds_freshness_and_drift_counts() -> None:
    payload = _ready_ci_payload()
    payload["knowledge_health"]["drift"]["counts_by_state"].update(
        {"current": 2, "unknown": 4}
    )

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="counts_by_state does not match freshness",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_validator_binds_health_diagnostics_to_top_level_findings() -> None:
    payload = _ready_ci_payload()
    payload["knowledge_health"]["drift"].update(
        {"diagnostic_count": 1, "reasons": ["freshness-result-missing"]}
    )

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="diagnostic_count does not match report.diagnostics",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_validator_rejects_absent_health_with_evaluated_sections() -> None:
    payload = ci_report.build_ci_check_payload(
        LintReport(wiki_dir="missing-wiki", src_dir=".", strict=True)
    )
    forged = deepcopy(payload)
    forged["knowledge_health"]["snapshot_parity"]["state"] = "mixed"

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="snapshot_parity.state does not match availability",
    ):
        ci_report.validate_ci_check_payload(forged, cli_exit=0)


def test_ci_check_uses_inventory_cache_options(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    seen = {}
    events = []
    real_reporter = ci_check_cmd.print_extraction_job_plan

    def recording_reporter(plan):
        events.append("report")
        real_reporter(plan)

    monkeypatch.setattr(ci_check_cmd, "print_extraction_job_plan", recording_reporter)

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        seen["cache_options"] = kwargs["cache_options"]
        seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
        seen["include_tests"] = kwargs["include_tests"]
        seen["parallel_jobs"] = kwargs["parallel_jobs"]
        seen["job_request"] = kwargs["job_request"]
        seen["knowledge_drift_report"] = kwargs["knowledge_drift_report"]
        seen["include_plugins"] = kwargs["include_plugins"]
        kwargs["plan_reporter"](ExtractionJobPlan())
        events.append("work")
        return LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
            knowledge_drift_report=kwargs["knowledge_drift_report"],
            extraction_job_plan=ExtractionJobPlan(),
        )

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="json",
            report=".git/llm-wiki-ci-report.md",
            helper_cache_dir=str(tmp_path / "helper-cache"),
            include_tests=["go"],
        )
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    _assert_versioned_ci_payload(payload)
    assert payload["ok"] is True
    assert seen["cache_options"].enabled is True
    assert seen["cache_options"].stats_enabled is False
    assert seen["helper_cache_dir"] == str(tmp_path / "helper-cache")
    assert seen["include_tests"] == ["go"]
    assert seen["parallel_jobs"] == 1
    assert seen["job_request"].requested_jobs == 1
    assert seen["knowledge_drift_report"] is False
    assert seen["include_plugins"] is True
    assert events == ["report", "work"]
    assert payload["knowledge_drift_gate"] is False
    assert payload["knowledge_drift_report"] is False
    assert payload["execution"] == _empty_execution_payload()
    assert captured.err.count("Extractor plan:") == 1


def test_ci_check_no_plugins_never_imports_target_plugin_code(
    tmp_path,
    monkeypatch,
    capsys,
):
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    (project / "app.py").write_text("VALUE = 1\n", encoding="utf-8")

    wiki = project / "docs" / "llm_wiki"
    for directory in ("entities", "modules", "workflows"):
        (wiki / directory).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# LLM Wiki Index\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Architectural Log\n", encoding="utf-8")

    marker = tmp_path / "target-plugin-executed"
    monkeypatch.setenv("TARGET_PLUGIN_EXECUTION_MARKER", str(marker))
    plugin_source = project / "vendor" / "hostile-ci-plugin"
    plugin_source.mkdir(parents=True)
    (plugin_source / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "hostile-ci-plugin",
                "version": "0.1.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "lint_rule",
                        "id": "marker",
                        "entry_point": "hostile_ci_plugin:check",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (plugin_source / "hostile_ci_plugin.py").write_text(
        "import os\n"
        "from pathlib import Path\n"
        "Path(os.environ['TARGET_PLUGIN_EXECUTION_MARKER']).write_text(\n"
        "    'executed\\n', encoding='utf-8'\n"
        ")\n"
        "def check(*_args):\n"
        "    return []\n",
        encoding="utf-8",
    )
    plugins.install_plugin(str(plugin_source), yes=True)
    real_build_report = ci_check_cmd.build_report
    seen = {}

    def recording_build_report(wiki_dir, src_dir, **kwargs):
        seen["include_plugins"] = kwargs["include_plugins"]
        return real_build_report(wiki_dir, src_dir, **kwargs)

    monkeypatch.setattr(ci_check_cmd, "build_report", recording_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    args = cli._build_parser().parse_args(
        [
            "ci-check",
            "--src-dir",
            ".",
            "--wiki-dir",
            "docs/llm_wiki",
            "--report",
            str(tmp_path / "report.md"),
            "--no-plugins",
        ]
    )
    assert args.no_plugins is True

    with pytest.raises(SystemExit) as exc_info:
        ci_check_cmd.run(args)

    assert exc_info.value.code == 1
    assert seen["include_plugins"] is False
    assert not marker.exists()
    assert "hostile_ci_plugin" not in sys.modules
    capsys.readouterr()


def test_ci_check_passes_explicit_native_drift_report_mode(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    seen = {}

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        seen["knowledge_drift_report"] = kwargs["knowledge_drift_report"]
        return LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=True,
            knowledge_drift_report=kwargs["knowledge_drift_report"],
        )

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    args = cli._build_parser().parse_args(
        [
            "ci-check",
            "--wiki-dir",
            "wiki",
            "--report",
            "report.md",
            "--knowledge-drift-report",
        ]
    )
    ci_check_cmd.run(args)

    assert seen["knowledge_drift_report"] is True
    assert "Lint passed" in capsys.readouterr().out


def test_ci_check_passes_jobs_to_build_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    seen = {}

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        seen["parallel_jobs"] = kwargs["parallel_jobs"]
        return LintReport(
            wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"]
        )

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="json",
            report=".git/llm-wiki-ci-report.md",
            jobs=2,
        )
    )

    json.loads(capsys.readouterr().out)
    assert seen["parallel_jobs"] == 2


def test_cli_ci_check_jobs_auto_resolves_positive_count(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.os, "cpu_count", lambda: 6)
    monkeypatch.setattr(
        cli.ci_check_cmd, "run", lambda args: seen.setdefault("jobs", args.jobs)
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", "ci-check", "--jobs", "auto"])

    cli.main()

    assert seen["jobs"] == 6


def test_cli_ci_check_jobs_parses_integer(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.ci_check_cmd,
        "run",
        lambda args: seen.update(jobs=args.jobs, requested_jobs=args.requested_jobs),
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", "ci-check", "--jobs", "2"])

    cli.main()

    assert seen == {"jobs": 2, "requested_jobs": 2}


def test_cli_ci_check_allow_external_src_parses_with_jobs_auto(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.os, "cpu_count", lambda: 4)
    monkeypatch.setattr(
        cli.ci_check_cmd,
        "run",
        lambda args: seen.update(
            allow_external_src=args.allow_external_src,
            jobs=args.jobs,
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["llm-wiki", "ci-check", "--allow-external-src", "--jobs", "auto"],
    )

    cli.main()

    assert seen == {"allow_external_src": True, "jobs": 4}


def test_ci_check_report_allows_absolute_output_path(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    report_path = tmp_path.parent / f"{tmp_path.name}-artifacts" / "report.md"

    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda wiki_dir, src_dir, **kwargs: LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
        ),
    )
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="json",
            report=str(report_path),
        )
    )

    assert report_path.exists()
    assert "# LLM Wiki Validation Report" in report_path.read_text(encoding="utf-8")
    payload = json.loads(capsys.readouterr().out)
    _assert_versioned_ci_payload(payload)
    assert payload["ok"] is True


def test_ci_check_report_allows_relative_output_outside_project(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "wiki").mkdir()
    monkeypatch.chdir(project)

    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda wiki_dir, src_dir, **kwargs: LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
        ),
    )
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="text",
            report="../artifacts/report.md",
        )
    )

    assert (tmp_path / "artifacts" / "report.md").exists()


def test_ci_check_allow_external_src_reaches_report_build(
    tmp_path, monkeypatch, capsys
):
    runner = tmp_path / "runner"
    external = tmp_path / "external"
    wiki_dir = runner / "wiki"
    runner.mkdir()
    external.mkdir()
    wiki_dir.mkdir()
    monkeypatch.chdir(runner)
    seen = {}

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        seen["wiki_dir"] = wiki_dir
        seen["src_dir"] = src_dir
        return LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
        )

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=os.path.relpath(external, runner),
            wiki_dir="wiki",
            format="json",
            report="report.md",
            allow_external_src=True,
        )
    )

    payload = json.loads(capsys.readouterr().out)
    _assert_versioned_ci_payload(payload)
    assert payload["ok"] is True
    assert Path(seen["src_dir"]) == external.resolve()
    assert seen["wiki_dir"] == "wiki"
    assert (runner / "report.md").exists()


def test_ci_check_external_source_without_opt_in_still_fails_closed(
    tmp_path, monkeypatch
):
    runner = tmp_path / "runner"
    external = tmp_path / "external"
    runner.mkdir()
    external.mkdir()
    (runner / "wiki").mkdir()
    monkeypatch.chdir(runner)
    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda *a, **k: pytest.fail("path validation should run before build_report"),
    )

    with pytest.raises(PathValidationError) as exc_info:
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=os.path.relpath(external, runner),
                wiki_dir="wiki",
                format="json",
                report="report.md",
            )
        )

    message = str(exc_info.value)
    assert "--src-dir" in message
    assert "outside the project root" in message


def test_ci_check_still_validates_wiki_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda *a, **k: pytest.fail("path validation should run before build_report"),
    )

    with pytest.raises(PathValidationError) as exc_info:
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir=str(outside),
                format="json",
                report="report.md",
            )
        )

    message = str(exc_info.value)
    assert "--wiki-dir" in message
    assert "outside the project root" in message


def test_ci_check_fails_on_stale_flow(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "api.py").write_text(
        '__all__ = ["run"]\n\n\ndef run():\n    return 1\n'
    )
    wiki = tmp_path / "wiki"
    for d in ["entities", "modules", "workflows", "flows"]:
        (wiki / d).mkdir(parents=True)
    (wiki / "modules" / "api.md").write_text("# api\n")
    (wiki / "flows" / "api-ghost.md").write_text("# api-ghost\n")
    (wiki / "index.md").write_text(
        "# Index\n- [api](modules/api.md)\n- [api-ghost](flows/api-ghost.md)\n"
    )
    (wiki / "log.md").write_text("# Log\n")

    with pytest.raises(SystemExit) as exc:
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir="wiki",
                format="markdown",
                report="ci-report.md",
            )
        )

    assert exc.value.code == 1
    report_text = (tmp_path / "ci-report.md").read_text(encoding="utf-8")
    assert "api-ghost" in report_text


def test_ci_check_json_output_adds_execution_and_exits_nonzero(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        report = LintReport(
            wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"]
        )
        report.issues.append(LintIssue("broken_links", "Broken link"))
        return report

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    with pytest.raises(SystemExit) as exc:
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir="wiki",
                format="json",
                report="report.md",
            )
        )

    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    health = _assert_versioned_ci_payload(payload)
    assert health["status"] == "absent"
    assert payload.pop("execution") == _empty_execution_payload()
    payload.pop("schema_version")
    payload.pop("knowledge_health")
    assert payload == {
        "diagnostics": [],
        "issue_count": 1,
        "issues": [
            {
                "category": "broken_links",
                "message": "Broken link",
                "path": None,
                "severity": "error",
                "target": None,
            }
        ],
        "knowledge_drift_gate": False,
        "knowledge_drift_report": False,
        "ok": False,
        "src_dir": ".",
        "strict": True,
        "wiki_dir": "wiki",
    }


def test_ci_check_reports_missing_haskell_helper_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    app_dir = tmp_path / "hls-analysis" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "Main.hs").write_text("module Main where\n", encoding="utf-8")
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    with pytest.raises(SystemExit) as exc:
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir="wiki",
                format="json",
                report="report.md",
            )
        )

    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["diagnostics"] == []
    assert payload["issues"][0]["category"] == "extractor_failure"
    assert payload["issues"][0]["target"] == "haskell"
    assert "prepare-extractors --language haskell" in payload["issues"][0]["message"]
    report_text = Path("report.md").read_text(encoding="utf-8")
    assert "haskell extraction failed" in report_text
    assert "Unsupported sources detected" not in report_text


def test_ci_check_diagnostic_only_report_exits_zero_with_additive_execution(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        report = LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
        )
        report.diagnostics.append(
            LintIssue(
                "dependency_cycles",
                "Import cycle: a.py ⇄ b.py",
                severity="warning",
            )
        )
        return report

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="json",
            report="report.md",
        )
    )

    payload = json.loads(capsys.readouterr().out)
    health = _assert_versioned_ci_payload(payload)
    assert health["status"] == "absent"
    assert payload.pop("execution") == _empty_execution_payload()
    payload.pop("schema_version")
    payload.pop("knowledge_health")
    assert payload == {
        "diagnostics": [
            {
                "category": "dependency_cycles",
                "message": "Import cycle: a.py ⇄ b.py",
                "path": None,
                "severity": "warning",
                "target": None,
            }
        ],
        "issue_count": 0,
        "issues": [],
        "knowledge_drift_gate": False,
        "knowledge_drift_report": False,
        "ok": True,
        "src_dir": ".",
        "strict": True,
        "wiki_dir": "wiki",
    }
    report_text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "## Diagnostics" in report_text
    assert "dependency_cycles" in report_text
    assert "Import cycle: a.py ⇄ b.py" in report_text


def test_ci_check_markdown_output_includes_diagnostics(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        report = LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
        )
        report.diagnostics.append(
            LintIssue(
                "undeclared_dependencies",
                "Undeclared python dependency (imported, not declared): pydantic",
                severity="warning",
                target="pydantic",
            )
        )
        return report

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="markdown",
            report="report.md",
        )
    )

    out = capsys.readouterr().out
    assert "## Diagnostics" in out
    assert "undeclared_dependencies" in out
    assert "pydantic" in out


def test_ci_check_metrics_receive_only_safe_aggregate_knowledge(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    report = LintReport(wiki_dir="wiki", src_dir=".", strict=True)
    report.knowledge_summary = _ready_knowledge_summary()
    recorded = []

    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda wiki_dir, src_dir, **kwargs: report,
    )
    monkeypatch.setattr(
        ci_check_cmd,
        "record_validation_event",
        lambda **kwargs: recorded.append(kwargs),
    )

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="json",
            report="report.md",
        )
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert len(recorded) == 1
    assert recorded[0]["knowledge_summary"] == (
        report.knowledge_summary.aggregate_payload()
    )
    assert {
        "concepts_total",
        "concepts_by_kind",
        "evidence_by_state",
        "freshness_by_state",
    }.isdisjoint(recorded[0]["knowledge_summary"])
    assert Path("report.md").exists()


@pytest.mark.parametrize(
    "metrics_error",
    [
        OSError("read-only"),
        TypeError("not serializable"),
        ValueError("invalid metrics payload"),
        RuntimeError("metrics unavailable"),
    ],
)
def test_ci_check_metrics_failures_do_not_fail_passing_report(
    tmp_path,
    monkeypatch,
    capsys,
    metrics_error,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()

    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda wiki_dir, src_dir, **kwargs: LintReport(
            wiki_dir=str(wiki_dir),
            src_dir=src_dir,
            strict=kwargs["strict"],
        ),
    )

    def fail_metrics(**_kwargs):
        raise metrics_error

    monkeypatch.setattr(ci_check_cmd, "record_validation_event", fail_metrics)

    ci_check_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="wiki",
            format="json",
            report="report.md",
        )
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert Path("report.md").exists()


@pytest.mark.parametrize(
    "metrics_error",
    [
        OSError("read-only"),
        TypeError("not serializable"),
        ValueError("invalid metrics payload"),
        RuntimeError("metrics unavailable"),
    ],
)
def test_ci_check_metrics_failures_preserve_validation_failure(
    tmp_path,
    monkeypatch,
    capsys,
    metrics_error,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        report = LintReport(
            wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"]
        )
        report.issues.append(LintIssue("broken_links", "Broken link"))
        return report

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)

    def fail_metrics(**_kwargs):
        raise metrics_error

    monkeypatch.setattr(ci_check_cmd, "record_validation_event", fail_metrics)

    with pytest.raises(SystemExit) as exc:
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir="wiki",
                format="json",
                report="report.md",
            )
        )

    assert exc.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert Path("report.md").exists()
