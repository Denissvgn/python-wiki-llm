"""Tests for ci-check command integration."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.commands import ci_check_cmd
from llm_wiki_cli.commands.lint_cmd import LintIssue, LintReport


def test_ci_check_uses_inventory_cache_options(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    seen = {}

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        seen["cache_options"] = kwargs["cache_options"]
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
        )
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert seen["cache_options"].enabled is True
    assert seen["cache_options"].stats_enabled is False
    assert seen["parallel_jobs"] == 1


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
        cli.ci_check_cmd, "run", lambda args: seen.setdefault("jobs", args.jobs)
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", "ci-check", "--jobs", "2"])

    cli.main()

    assert seen["jobs"] == 2


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


def test_ci_check_still_validates_src_and_wiki_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    monkeypatch.setattr(
        ci_check_cmd,
        "build_report",
        lambda *a, **k: pytest.fail("path validation should run before build_report"),
    )

    with pytest.raises(PathValidationError):
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=str(outside),
                wiki_dir="wiki",
                format="json",
                report="report.md",
            )
        )

    with pytest.raises(PathValidationError):
        ci_check_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                wiki_dir=str(outside),
                format="json",
                report="report.md",
            )
        )


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


def test_ci_check_json_output_unchanged_and_exits_nonzero(
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
    assert payload == {
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
        "ok": False,
        "src_dir": ".",
        "strict": True,
        "wiki_dir": "wiki",
    }


def test_ci_check_diagnostic_only_report_exits_zero_and_keeps_json_shape(
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
    assert payload == {
        "issue_count": 0,
        "issues": [],
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


def test_ci_check_metrics_oserror_does_not_fail_passing_report(
    tmp_path, monkeypatch, capsys
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
    monkeypatch.setattr(
        ci_check_cmd,
        "record_validation_event",
        lambda **kwargs: (_ for _ in ()).throw(OSError("read-only")),
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
    assert Path("report.md").exists()


def test_ci_check_metrics_oserror_preserves_validation_failure(
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
    monkeypatch.setattr(
        ci_check_cmd,
        "record_validation_event",
        lambda **kwargs: (_ for _ in ()).throw(OSError("read-only")),
    )

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
