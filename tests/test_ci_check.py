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


def _set_nested(mapping: dict, path: str, value: object) -> None:
    """Replace one field in a JSON-shaped test payload."""

    parts = path.split(".")
    cursor = mapping
    for part in parts[:-1]:
        nested = cursor[part]
        assert isinstance(nested, dict)
        cursor = nested
    cursor[parts[-1]] = value


def _summary_arguments(**overrides: object) -> dict[str, object]:
    arguments: dict[str, object] = {
        "result": "PASS",
        "cli_exit": 0,
        "json_state": "available (validated llm-wiki-ci-check/v1)",
        "markdown_state": "available",
        "tree_state": "clean",
        "status_records": [],
        "status_count": 0,
        "status_limit": 20,
        "max_lines": 40,
        "max_bytes": 8192,
    }
    arguments.update(overrides)
    return arguments


def _render_summary(
    report: dict | None,
    **overrides: object,
) -> bytes:
    return ci_report.render_ci_summary(
        report,
        **_summary_arguments(**overrides),  # pyright: ignore[reportArgumentType]
    )


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


def test_ci_report_builder_rejects_non_lint_reports() -> None:
    with pytest.raises(TypeError, match="report must be a LintReport"):
        ci_report.build_ci_check_payload({})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ([], "report must be an object"),
        ({}, "report.diagnostics is required"),
    ],
)
def test_ci_report_validator_rejects_incomplete_envelopes(
    value: object,
    message: str,
) -> None:
    with pytest.raises(ci_report.CiCheckReportError, match=message):
        ci_report.validate_ci_check_payload(value, cli_exit=0)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        ("schema_version", "future", "schema_version must be"),
        ("wiki_dir", " ", "wiki_dir must be a non-empty string"),
        ("strict", False, "strict must be true"),
        ("knowledge_drift_gate", True, "knowledge_drift_gate must be false"),
        (
            "knowledge_drift_report",
            "false",
            "knowledge_drift_report must be a boolean",
        ),
        ("issue_count", -1, "issue_count must be a non-negative integer"),
        ("issues", {}, "issues must be an array"),
        ("knowledge_health.status", "future", "status is unsupported"),
        (
            "knowledge_health.verification_receipt.passed",
            "yes",
            "passed must be a boolean",
        ),
    ],
)
def test_ci_report_validator_rejects_invalid_scalar_contracts(
    path: str,
    value: object,
    message: str,
) -> None:
    payload = _ready_ci_payload()
    _set_nested(payload, path, value)

    with pytest.raises(ci_report.CiCheckReportError, match=message):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_report_validator_rejects_unknown_top_level_fields() -> None:
    payload = _ready_ci_payload()
    payload["extension"] = True

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="report contains an unsupported field",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_report_validator_checks_optional_finding_fields() -> None:
    payload = _ready_ci_payload()
    payload.update(ok=False, issue_count=1)
    payload["issues"] = [
        {
            "category": "broken_links",
            "message": "broken",
            "severity": "error",
            "path": "wiki/index.md",
            "target": "missing.md",
            "reason_code": 7,
        }
    ]

    with pytest.raises(
        ci_report.CiCheckReportError,
        match=r"issues\[0\]\.reason_code must be a non-empty string",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=1)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        (
            {"requested_jobs": 0, "resolved_jobs": 0},
            "requested_jobs must be greater than zero",
        ),
        (
            {"requested_jobs": 2, "resolved_jobs": 1},
            "requested_jobs must equal resolved_jobs",
        ),
        (
            {"parallel_plan_ids": ["b", "a"], "eligible_parallel_plans": 2},
            "parallel_plan_ids must be unique and sorted",
        ),
        (
            {"parallel_plan_ids": ["a"], "eligible_parallel_plans": 0},
            "eligible_parallel_plans must equal the parallel plan count",
        ),
        (
            {
                "parallel_plan_ids": ["a"],
                "sequential_plan_ids": ["a"],
                "eligible_parallel_plans": 1,
                "effective_workers": 1,
            },
            "plan identifiers must be disjoint",
        ),
        (
            {
                "requested_jobs": "auto",
                "resolved_jobs": 2,
                "parallel_plan_ids": ["a", "b"],
                "eligible_parallel_plans": 2,
                "effective_workers": 1,
            },
            "effective_workers does not match",
        ),
        (
            {"sequential_plan_ids": ["a"], "effective_workers": 0},
            "effective_workers does not match",
        ),
    ],
)
def test_ci_report_validator_enforces_extraction_plan_consistency(
    changes: dict[str, object],
    message: str,
) -> None:
    payload = _ready_ci_payload()
    jobs = payload["execution"]["extractor_jobs"]
    assert isinstance(jobs, dict)
    jobs.update(changes)

    with pytest.raises(ci_report.CiCheckReportError, match=message):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_report_validator_accepts_auto_parallel_execution() -> None:
    payload = _ready_ci_payload()
    payload["execution"]["extractor_jobs"] = {
        "requested_jobs": "auto",
        "resolved_jobs": 4,
        "eligible_parallel_plans": 2,
        "effective_workers": 2,
        "parallel_plan_ids": ["go", "rust"],
        "sequential_plan_ids": ["python"],
        "cache_elided_plan_ids": ["typescript"],
    }

    assert ci_report.validate_ci_check_payload(payload, cli_exit=0) is payload


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda summary, _health: summary.update(availability="future"),
            "knowledge_summary is inconsistent",
        ),
        (
            lambda summary, _health: summary.update(freshness="wrong"),
            "knowledge_summary.freshness is inconsistent",
        ),
        (
            lambda summary, _health: summary.update(concepts_total=7),
            "concepts_by_kind does not match concepts_total",
        ),
        (
            lambda summary, _health: summary.update(freshness_by_state={}),
            "freshness_by_state does not match freshness_counts",
        ),
        (
            lambda _summary, health: health["availability"].update(state="degraded"),
            "availability does not match report.knowledge_health",
        ),
        (
            lambda _summary, health: health["availability"].update(reason="other"),
            "reason does not match report.knowledge_health",
        ),
        (
            lambda _summary, health: health["freshness"].update(evaluated=False),
            "freshness_evaluated does not match report.knowledge_health",
        ),
        (
            lambda _summary, health: health["freshness"].update(
                disclosure="other"
            ),
            "freshness does not match report.knowledge_health",
        ),
        (
            lambda _summary, health: health["freshness"].update(concepts=7),
            "concepts_evaluated does not match report.knowledge_health",
        ),
        (
            lambda _summary, health: health["freshness"].update(
                counts_by_state=None
            ),
            "freshness_counts does not match report.knowledge_health",
        ),
    ],
)
def test_knowledge_summary_validator_binds_every_health_projection(
    mutate,
    message: str,
) -> None:
    payload = _ready_ci_payload()
    summary = deepcopy(payload["knowledge_summary"])
    health = deepcopy(payload["knowledge_health"])
    assert isinstance(summary, dict)
    assert isinstance(health, dict)
    mutate(summary, health)

    with pytest.raises(ci_report.CiCheckReportError, match=message):
        ci_report._validate_knowledge_summary(summary, health=health)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {
                "strict": False,
                "source_selection_mismatch": True,
                "availability_state": "absent",
                "freshness_evaluated": False,
                "snapshot_state": "not-available",
                "governance_state": "not-present",
                "expired_reviews": 0,
                "drift_state": "not-evaluated",
                "verification_state": "absent",
            },
            ("unhealthy", [], ["source-selection-mismatch"]),
        ),
        (
            {
                "strict": False,
                "source_selection_mismatch": True,
                "availability_state": "unsupported",
                "freshness_evaluated": False,
                "snapshot_state": "not-available",
                "governance_state": "invalid",
                "expired_reviews": 2,
                "drift_state": "stale-confirmed",
                "verification_state": "invalid",
            },
            (
                "unhealthy",
                ["freshness-unevaluated", "expired-reviews"],
                [
                    "source-selection-mismatch",
                    "knowledge-unsupported",
                    "invalid-governance",
                    "stale-confirmed",
                    "verification-invalid",
                ],
            ),
        ),
        (
            {
                "strict": False,
                "source_selection_mismatch": False,
                "availability_state": "degraded",
                "freshness_evaluated": True,
                "snapshot_state": "invalid",
                "governance_state": "not-present",
                "expired_reviews": 0,
                "drift_state": "indeterminate",
                "verification_state": "absent",
            },
            ("degraded", ["knowledge-degraded", "freshness-indeterminate"], []),
        ),
        (
            {
                "strict": True,
                "source_selection_mismatch": False,
                "availability_state": "ready",
                "freshness_evaluated": True,
                "snapshot_state": "valid",
                "governance_state": "valid",
                "expired_reviews": 0,
                "drift_state": "nonsemantic-change",
                "verification_state": "valid",
            },
            ("unhealthy", [], ["nonsemantic-source-change"]),
        ),
    ],
)
def test_doctor_classification_covers_closed_health_states(
    kwargs: dict[str, object],
    expected: tuple[str, list[str], list[str]],
) -> None:
    assert ci_report._expected_health_classification(**kwargs) == expected  # type: ignore[arg-type]


def test_standalone_doctor_contract_allows_additive_fields_only_when_requested() -> None:
    health = deepcopy(_ready_ci_payload()["knowledge_health"])
    health["extension"] = {"future": True}
    health["availability"]["extension"] = "value"

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="knowledge_health contains an unsupported field",
    ):
        ci_report.validate_doctor_payload(health, expected_strict=False)

    assert (
        ci_report.validate_doctor_payload(
            health,
            expected_strict=False,
            allow_additive=True,
        )
        is health
    )


def test_standalone_doctor_contract_reports_missing_nested_fields() -> None:
    health = deepcopy(_ready_ci_payload()["knowledge_health"])
    del health["availability"]["reason"]

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="knowledge_health.availability.reason is required",
    ):
        ci_report.validate_doctor_payload(health, expected_strict=False)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        (
            {"knowledge_health.schema_version": "future"},
            "knowledge_health.schema_version must be",
        ),
        (
            {"knowledge_health.exit_code": 1},
            "exit_code does not match status",
        ),
        (
            {"knowledge_health.strict": True},
            "strict does not match the requested mode",
        ),
        (
            {"knowledge_health.wiki_dir": "other"},
            "wiki_dir does not match report.wiki_dir",
        ),
        (
            {"knowledge_health.src_dir": "source"},
            "src_dir does not match report.src_dir",
        ),
        (
            {"knowledge_health.availability.usable": False},
            "availability.usable does not match state",
        ),
        (
            {"knowledge_health.freshness.counts_by_state": None},
            "freshness.counts_by_state does not match evaluated",
        ),
        (
            {"knowledge_health.freshness.concepts": 7},
            "freshness.concepts does not match counts",
        ),
        (
            {
                "knowledge_health.snapshot_parity.issue_count": 2,
                "knowledge_health.snapshot_parity.reasons": ["same", "same"],
            },
            "snapshot_parity.reasons must be unique and sorted",
        ),
        (
            {"knowledge_health.snapshot_parity.issue_count": 1},
            "snapshot_parity issue count and reasons must agree",
        ),
        (
            {"knowledge_health.governance.state": "invalid"},
            "governance.state does not match issue_count",
        ),
        (
            {
                "knowledge_health.governance.state": "invalid",
                "knowledge_health.governance.ledger": "invalid",
                "knowledge_health.governance.projection": "invalid",
                "knowledge_health.governance.issue_count": 1,
            },
            "governance issue count and reasons must agree",
        ),
        (
            {
                "knowledge_health.governance.state": "invalid",
                "knowledge_health.governance.ledger": "valid",
                "knowledge_health.governance.projection": "valid",
                "knowledge_health.governance.issue_count": 1,
                "knowledge_health.governance.reasons": ["invalid-ledger"],
            },
            "governance component states do not match state",
        ),
        (
            {
                "knowledge_health.governance.state": "valid",
                "knowledge_health.governance.ledger": "not-present",
                "knowledge_health.governance.projection": "not-present",
            },
            "governance valid state has no valid component",
        ),
        (
            {
                "knowledge_health.governance.ledger": "valid",
                "knowledge_health.governance.projection": "not-present",
            },
            "governance not-present state is inconsistent",
        ),
        (
            {"knowledge_health.drift.state": "not-evaluated"},
            "drift.counts_by_state does not match state",
        ),
        (
            {"knowledge_health.drift.counts_by_state.current": 2},
            "drift.counts_by_state does not match freshness",
        ),
        (
            {"knowledge_health.drift.confirmed_stale": 1},
            "drift.confirmed_stale does not match counts",
        ),
        (
            {"knowledge_health.drift.state": "indeterminate"},
            "drift.state does not match its counts",
        ),
        (
            {
                "knowledge_health.drift.state": "indeterminate",
                "knowledge_health.drift.indeterminate": 2,
                "knowledge_health.drift.diagnostic_count": 1,
                "knowledge_health.drift.reasons": ["basis-incompatible"],
            },
            "drift diagnostic subsets exceed total",
        ),
        (
            {
                "knowledge_health.drift.state": "indeterminate",
                "knowledge_health.drift.indeterminate": 1,
                "knowledge_health.drift.diagnostic_count": 1,
            },
            "drift diagnostic count and reasons must agree",
        ),
        (
            {
                "knowledge_health.verification_receipt.recorded_result": "passed",
                "knowledge_health.verification_receipt.passed": True,
            },
            "unrecorded state must not carry a result",
        ),
        (
            {
                "knowledge_health.verification_receipt.state": "invalid",
                "knowledge_health.verification_receipt.recorded_result": "passed",
            },
            "result fields disagree",
        ),
        (
            {
                "knowledge_health.verification_receipt.state": "invalid",
                "knowledge_health.verification_receipt.recorded_result": "passed",
                "knowledge_health.verification_receipt.passed": False,
            },
            "recorded result disagrees",
        ),
        (
            {
                "knowledge_health.verification_receipt.state": "invalid",
                "knowledge_health.verification_receipt.recorded_result": "failed",
                "knowledge_health.verification_receipt.passed": True,
            },
            "recorded result disagrees",
        ),
        (
            {"knowledge_health.verification_receipt.state": "failed"},
            "failed state is inconsistent",
        ),
        (
            {"knowledge_health.verification_receipt.state": "valid"},
            "valid state is inconsistent",
        ),
        (
            {
                "knowledge_health.verification_receipt.state": "stale",
                "knowledge_health.verification_receipt.recorded_result": "passed",
                "knowledge_health.verification_receipt.passed": True,
            },
            "stale state is inconsistent",
        ),
        (
            {"knowledge_health.availability.state": "degraded"},
            "snapshot_parity.state does not match availability",
        ),
        (
            {"knowledge_health.degraded_reasons": ["unexpected"]},
            "degraded_reasons do not match its sections",
        ),
        (
            {"knowledge_health.unhealthy_reasons": ["unexpected"]},
            "unhealthy_reasons do not match its sections",
        ),
    ],
)
def test_ci_report_validator_rejects_incoherent_doctor_sections(
    changes: dict[str, object],
    message: str,
) -> None:
    payload = _ready_ci_payload()
    for path, value in changes.items():
        _set_nested(payload, path, value)

    with pytest.raises(ci_report.CiCheckReportError, match=message):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_doctor_validator_rejects_evaluated_absent_knowledge() -> None:
    payload = ci_report.build_ci_check_payload(
        LintReport(wiki_dir="missing-wiki", src_dir=".", strict=True)
    )
    health = payload["knowledge_health"]
    assert isinstance(health, dict)
    freshness = health["freshness"]
    drift = health["drift"]
    assert isinstance(freshness, dict)
    assert isinstance(drift, dict)
    freshness.update(
        evaluated=True,
        concepts=0,
        counts_by_state={state: 0 for state in ci_report._FRESHNESS_STATES},
    )
    drift.update(
        state="current",
        counts_by_state={state: 0 for state in ci_report._FRESHNESS_STATES},
    )

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="unavailable knowledge has evaluated freshness",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_doctor_validator_rejects_absent_section_contradictions() -> None:
    payload = ci_report.build_ci_check_payload(
        LintReport(wiki_dir="missing-wiki", src_dir=".", strict=True)
    )
    health = payload["knowledge_health"]
    assert isinstance(health, dict)
    governance = health["governance"]
    assert isinstance(governance, dict)
    governance.update(
        state="valid",
        ledger="valid",
        projection="not-present",
    )

    with pytest.raises(
        ci_report.CiCheckReportError,
        match="absent availability contradicts its sections",
    ):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)


def test_ci_report_strict_loader_accepts_only_regular_canonical_json(
    tmp_path: Path,
) -> None:
    payload = _ready_ci_payload()
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    assert ci_report.load_ci_check_payload(report_path, cli_exit=0) == payload

    invalid_path = tmp_path / "not-a-file"
    invalid_path.mkdir()
    with pytest.raises(
        ci_report.CiCheckReportError,
        match="report path must be a regular file",
    ):
        ci_report.load_ci_check_payload(invalid_path, cli_exit=0)

    invalid_utf8 = tmp_path / "invalid-utf8.json"
    invalid_utf8.write_bytes(b"\xff")
    with pytest.raises(
        ci_report.CiCheckReportError,
        match="report is not strict UTF-8 JSON",
    ):
        ci_report.load_ci_check_payload(invalid_utf8, cli_exit=0)

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(
        ci_report.CiCheckReportError,
        match="report is not strict UTF-8 JSON",
    ):
        ci_report.load_ci_check_payload(malformed, cli_exit=0)


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ('{"duplicate": 1, "duplicate": 2}', "duplicate object key"),
        ('{"value": NaN}', "non-finite JSON number"),
    ],
)
def test_ci_report_strict_loader_rejects_ambiguous_json(
    tmp_path: Path,
    raw: str,
    message: str,
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(raw, encoding="utf-8")

    with pytest.raises(ci_report.CiCheckReportError, match=message):
        ci_report.load_ci_check_payload(report_path, cli_exit=0)


def test_ci_summary_renders_validated_health_and_bounded_dirty_paths() -> None:
    payload = _ready_ci_payload()
    summary = _render_summary(payload).decode("utf-8")

    assert "- Result: **PASS**" in summary
    assert "- Knowledge health: `healthy`" in summary
    assert "- Freshness: `evaluated (6 concepts)`" in summary
    assert "- Snapshot / governance: `valid` / `not-present`" in summary
    assert "- Drift: `current` (confirmed=0, indeterminate=0)" in summary

    long_record = ("a" * 236 + "€" * 3).encode()
    failure = _render_summary(
        None,
        result="FAIL",
        cli_exit=1,
        json_state="unavailable (no output)",
        markdown_state="unavailable",
        tree_state="dirty (3 status records)",
        status_records=[b"M path`with-mark\xff", long_record, b"third"],
        status_count=3,
        status_limit=2,
    ).decode("utf-8")

    assert "Original `ci-check` exit: `1`" in failure
    assert "Knowledge health: `unavailable`" in failure
    assert r"path\x60with-mark\xff" in failure
    assert "... 1 additional status records omitted" in failure
    assert "a" * 100 in failure


@pytest.mark.parametrize(
    ("report", "changes", "message"),
    [
        (None, {"result": "NOPE"}, "result must be PASS or FAIL"),
        (None, {"cli_exit": True}, "cli_exit must be a non-negative integer"),
        (None, {"json_state": "unknown"}, "json_state is unsupported"),
        (None, {"markdown_state": "missing"}, "markdown_state is unsupported"),
        (
            None,
            {"tree_state": "dirty (1 status records)"},
            "tree_state does not match status_count",
        ),
        (
            None,
            {
                "tree_state": "unavailable",
                "status_count": 1,
                "status_records": [b"M file"],
            },
            "unavailable tree state must not carry records",
        ),
        (None, {"status_limit": 21}, "status_limit exceeds the frozen bound"),
        (None, {"max_lines": 41}, "summary bounds exceed the frozen limits"),
        (
            None,
            {"status_count": 1, "tree_state": "dirty (1 status records)"},
            "status_count does not match the status records",
        ),
        (
            "ready",
            {"cli_exit": 0, "result": "FAIL"},
            "validated report and JSON evidence state disagree",
        ),
        (None, {"result": "PASS"}, "result does not match the validated evidence"),
        (None, {"max_lines": 1}, "bounded summary invariant failed"),
    ],
)
def test_ci_summary_rejects_incoherent_or_unbounded_evidence(
    report: str | None,
    changes: dict[str, object],
    message: str,
) -> None:
    resolved_report = _ready_ci_payload() if report == "ready" else None
    defaults = {
        "result": "FAIL",
        "cli_exit": 1,
        "json_state": "unavailable (no output)",
        "markdown_state": "unavailable",
        "tree_state": "clean",
    }
    defaults.update(changes)

    with pytest.raises(ci_report.CiCheckReportError, match=message):
        _render_summary(resolved_report, **defaults)


def test_ci_report_internal_cli_validates_and_renders_summary(tmp_path: Path) -> None:
    payload = _ready_ci_payload()
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    status_path = tmp_path / "status"
    status_path.write_bytes(b"")
    output_path = tmp_path / "summary.md"

    assert (
        ci_report.main(
            [
                "validate",
                "--report",
                str(report_path),
                "--cli-exit",
                "0",
            ]
        )
        == 0
    )
    assert (
        ci_report.main(
            [
                "render-summary",
                "--report",
                str(report_path),
                "--cli-exit",
                "0",
                "--result",
                "PASS",
                "--json-state",
                "available (validated llm-wiki-ci-check/v1)",
                "--markdown-state",
                "available",
                "--tree-state",
                "clean",
                "--status-path",
                str(status_path),
                "--status-count",
                "0",
                "--status-limit",
                "20",
                "--max-lines",
                "40",
                "--max-bytes",
                "8192",
                "--output",
                str(output_path),
            ]
        )
        == 0
    )
    assert "Result: **PASS**" in output_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("unsafe_target", ["status", "output"])
def test_ci_report_internal_cli_rejects_unsafe_paths(
    tmp_path: Path,
    unsafe_target: str,
) -> None:
    status_path = tmp_path / "status"
    if unsafe_target == "output":
        status_path.write_bytes(b"")
    output_path = (
        tmp_path / "missing-parent" / "summary.md"
        if unsafe_target == "output"
        else tmp_path / "summary.md"
    )

    with pytest.raises(SystemExit, match=f"{unsafe_target} path"):
        ci_report.main(
            [
                "render-summary",
                "--cli-exit",
                "1",
                "--result",
                "FAIL",
                "--json-state",
                "unavailable (no output)",
                "--markdown-state",
                "unavailable",
                "--tree-state",
                "clean" if unsafe_target == "output" else "unavailable",
                "--status-path",
                str(status_path),
                "--status-count",
                "0",
                "--status-limit",
                "20",
                "--max-lines",
                "40",
                "--max-bytes",
                "8192",
                "--output",
                str(output_path),
            ]
        )
