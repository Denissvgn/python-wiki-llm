"""Upgrade runs from a typed request for embedding engines."""

from __future__ import annotations

import argparse
import io
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.cli_declarations import _build_parser
from llm_wiki_cli.commands import upgrade_cmd
from llm_wiki_cli.engine import Engine, Host, UpgradeError, UpgradeRequest, UpgradeRequestError


def _git_project(root: Path) -> Path:
    subprocess.run(["git", "init", str(root)], capture_output=True, check=True)
    return root


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    from llm_wiki_cli.commands import init_cmd

    root = _git_project(tmp_path / "proj")
    monkeypatch.chdir(root)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path))
    init_cmd.run(SimpleNamespace(agent="copilot", wiki_dir="docs/llm_wiki", no_skills=False, issue_reporting=None))
    return root


def _engine() -> tuple[Engine, io.StringIO, io.StringIO]:
    out, err = io.StringIO(), io.StringIO()
    return Engine(host=Host(stdout=out, stderr=err)), out, err


def test_engine_upgrade_refreshes_the_configured_agent(project: Path, capsys) -> None:
    engine, out, _ = _engine()
    capsys.readouterr()

    outcome = engine.upgrade(UpgradeRequest())

    assert outcome.status == "complete" and outcome.agent == "copilot"
    assert outcome.previous_agent is None and outcome.schema_file
    assert (project / outcome.schema_file).is_file()
    assert "Upgrade complete." in out.getvalue()
    assert capsys.readouterr() == ("", "")
    assert outcome.to_dict()["agent"] == "copilot"


def test_engine_upgrade_reports_an_agent_switch(project: Path) -> None:
    engine, _, _ = _engine()

    outcome = engine.upgrade(UpgradeRequest(agent="cursor"))

    assert (outcome.agent, outcome.previous_agent) == ("cursor", "copilot")


def test_engine_upgrade_raises_typed_errors(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(_git_project(tmp_path / "bare"))
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path))
    engine, _, err = _engine()

    with pytest.raises(UpgradeError) as unknown:
        engine.upgrade(UpgradeRequest())
    with pytest.raises(UpgradeRequestError):
        engine.upgrade(UpgradeRequest(wiki_root="../outside"))

    assert unknown.value.exit_code == 1
    assert str(unknown.value).startswith("Error: Cannot determine agent")
    assert "Cannot determine agent" in err.getvalue()
    with pytest.raises(TypeError):
        engine.upgrade({"agent": "copilot"})  # type: ignore[arg-type]


def test_cli_upgrade_still_exits_with_the_command_status(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(_git_project(tmp_path / "bare"))
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", os.fspath(tmp_path))

    with pytest.raises(SystemExit) as stopped:
        upgrade_cmd.run(_build_parser().parse_args(["upgrade"]))

    assert stopped.value.code == 1 and isinstance(stopped.value, upgrade_cmd.UpgradeAborted)
    assert "Cannot determine agent" in capsys.readouterr().err


def test_request_translation_keeps_cli_defaults() -> None:
    parsed = _build_parser().parse_args(["upgrade", "--agent", "cursor", "--no-skills", "--quality-hints"])

    request = upgrade_cmd.upgrade_request_from_args(parsed)

    assert (request.agent, request.reference_skill, request.quality_hints) == ("cursor", False, True)
    assert (request.issue_reporting, request.source_root) == (None, None)
    assert upgrade_cmd.upgrade_request_from_args(argparse.Namespace()) == UpgradeRequest()
