"""Tests for commands/trigger_cmd.py (mock-based, no real LLM agent needed)."""
import json
import subprocess
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from llm_wiki_cli.commands import trigger_cmd
from llm_wiki_cli.services import circuit_breaker


def _make_args(**kwargs):
    defaults = {
        "agent": "claude",
        "reset_breaker": False,
        "timeout": 10,
        "max_diff_lines": 1000,
        "force": False,
        "wiki_dir": "docs/llm_wiki",
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestTriggerUIAgent:
    def test_rejects_ide_agent(self, capsys):
        for agent in ["copilot", "cursor", "generic"]:
            with pytest.raises(SystemExit):
                trigger_cmd.run(_make_args(agent=agent))
            out = capsys.readouterr().out
            assert "UI-based" in out


class TestTriggerResetBreaker:
    def test_reset_breaker(self, tmp_project, capsys):
        git_dir = tmp_project / ".git"
        state = {"consecutive_failures": 5, "state": "open", "last_failure_ts": None}
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))

        trigger_cmd.run(_make_args(reset_breaker=True))
        out = capsys.readouterr().out
        assert "reset" in out.lower() or "re-enabled" in out.lower()

        loaded = circuit_breaker.load_state(git_dir)
        assert loaded["state"] == "closed"
        assert loaded["consecutive_failures"] == 0


class TestTriggerBreakerOpen:
    def test_aborts_when_breaker_open(self, tmp_project, capsys):
        git_dir = tmp_project / ".git"
        state = {"consecutive_failures": 3, "state": "open", "last_failure_ts": None}
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))

        trigger_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "OPEN" in out


class TestTriggerDiffGuard:
    @patch("llm_wiki_cli.commands.trigger_cmd.subprocess.run")
    def test_skips_large_diff(self, mock_run, tmp_project, capsys):
        mock_run.return_value = MagicMock(
            stdout="\n".join([f"line {i}" for i in range(2000)]),
            returncode=0,
        )
        trigger_cmd.run(_make_args(max_diff_lines=100))
        out = capsys.readouterr().out
        assert "too large" in out.lower() or "Diff too large" in out


class TestTriggerGitFailure:
    @patch("llm_wiki_cli.commands.trigger_cmd.subprocess.run")
    def test_records_failure_on_git_error(self, mock_run, tmp_project):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git diff")
        git_dir = tmp_project / ".git"

        trigger_cmd.run(_make_args())
        state = circuit_breaker.load_state(git_dir)
        assert state["consecutive_failures"] >= 1
