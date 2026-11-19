"""Lint runs from a typed request for the API and embedding engines."""

from __future__ import annotations

import argparse
import io
import os
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.cli_declarations import _build_parser
from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.engine import Engine, LintRequest, LintRequestError, NoProcessHost

BILLING = "class Invoice:\n    total: int\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "billing.py").write_text(BILLING, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path.parent))
    api.bootstrap_wiki("src", "wiki")
    return tmp_path


def test_api_lint_returns_the_report_without_console_output(project: Path, capsys) -> None:
    capsys.readouterr()

    clean = api.lint_wiki("src", "wiki", strict=True)
    (project / "wiki" / "index.md").write_text("[gone](missing-page.md)\n", encoding="utf-8")
    broken = api.lint_wiki("src", "wiki")

    assert clean["ok"] and clean["issue_count"] == 0 and clean["strict"]
    assert not broken["ok"]
    assert any(issue["category"] == "broken_links" for issue in broken["issues"])
    assert capsys.readouterr() == ("", "")


def test_api_lint_rejects_paths_outside_the_workspace(project: Path) -> None:
    with pytest.raises(api.InvalidRequestError):
        api.lint_wiki("../elsewhere", "wiki")


def test_engine_lint_returns_a_report_and_starts_no_process(project: Path, monkeypatch) -> None:
    def forbidden(args, *rest, **kwargs):
        raise AssertionError("no process may start")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    engine = Engine(host=NoProcessHost(stdout=io.StringIO(), stderr=io.StringIO()))

    report = engine.lint(LintRequest(wiki_root="wiki", source_root="src", strict=True, plugins=False))

    assert report.passed and report.strict
    with pytest.raises(LintRequestError):
        engine.lint(LintRequest(wiki_root="wiki", source_root="../elsewhere"))
    with pytest.raises(TypeError):
        engine.lint({"wiki_root": "wiki"})  # type: ignore[arg-type]


def test_cli_lint_still_exits_with_the_command_status(project: Path, capsys) -> None:
    (project / "wiki" / "index.md").write_text("[gone](missing-page.md)\n", encoding="utf-8")
    args = _build_parser().parse_args(["lint", "--wiki-dir", "wiki", "--src-dir", "src"])

    with pytest.raises(SystemExit) as stopped:
        lint_cmd.run(args)

    assert stopped.value.code == 1
    assert "missing-page.md" in capsys.readouterr().out


def test_request_translation_keeps_cli_defaults() -> None:
    parsed = _build_parser().parse_args(["lint", "--no-cache", "--jobs", "3", "--strict"])

    request = lint_cmd.lint_request_from_args(parsed)

    assert (request.strict, request.cache, request.plugins, request.jobs) == (True, False, True, 3)
    assert lint_cmd.lint_request_from_args(argparse.Namespace()) == LintRequest()
