"""Tests for commands/trigger_cmd.py (mock-based, no real LLM agent needed)."""

import ast
import inspect
import json
import os
import stat
import subprocess
import textwrap
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from llm_wiki_cli.commands import trigger_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services import circuit_breaker


def _make_args(**kwargs):
    defaults = {
        "agent": "claude",
        "reset_breaker": False,
        "timeout": 10,
        "max_diff_lines": 1000,
        "max_prompt_bytes": None,
        "force": False,
        "wiki_dir": "docs/llm_wiki",
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = [
        stmt
        for stmt in function_node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestTriggerRunStructure:
    def test_run_sync_stays_a_small_coordinator(self):
        assert _body_line_count(trigger_cmd._run_sync) <= 40


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
        assert state["consecutive_failures"] == 1
        assert state["state"] == "closed"


class TestTriggerPromptHandling:
    @patch("llm_wiki_cli.commands.trigger_cmd.subprocess.run")
    def test_skips_prompt_larger_than_cap(
        self, mock_run, tmp_project, monkeypatch, capsys
    ):
        mock_run.return_value = MagicMock(stdout="diff\n", returncode=0)
        monkeypatch.setattr(
            "llm_wiki_cli.commands.extract_cmd.get_inventory_result",
            lambda *a, **k: InventoryResult(
                {
                    "huge.py": {
                        "language": "python",
                        "classes": [{"name": "Huge", "docstring": "x" * 1000}],
                        "functions": [],
                    }
                },
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.commands.extract_cmd.get_call_graph", lambda inv: {}
        )

        trigger_cmd.run(_make_args(max_prompt_bytes=100))

        out = capsys.readouterr().out
        assert "Prompt too large" in out
        assert mock_run.call_count == 1

    def test_claude_prompt_is_streamed_from_file(self, tmp_project, monkeypatch):
        monkeypatch.setattr(
            "llm_wiki_cli.commands.extract_cmd.get_inventory_result",
            lambda *a, **k: InventoryResult(
                {"a.py": {"language": "python", "classes": [], "functions": []}},
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.commands.extract_cmd.get_call_graph", lambda inv: {}
        )
        agent_kwargs = []

        def fake_run(cmd, *args, **kwargs):
            if cmd[:2] == ["git", "diff"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="diff\n", stderr="")
            if cmd[0] == "claude":
                agent_kwargs.append(
                    {
                        "cmd": list(cmd),
                        "keys": set(kwargs),
                        "stdin_readable": kwargs["stdin"].readable(),
                    }
                )
                return subprocess.CompletedProcess(cmd, 0)
            raise AssertionError(f"unexpected command: {cmd}")

        with patch(
            "llm_wiki_cli.commands.trigger_cmd.subprocess.run", side_effect=fake_run
        ):
            trigger_cmd.run(_make_args(agent="claude"))

        assert len(agent_kwargs) == 1
        assert agent_kwargs[0]["cmd"] == ["claude", "-p"]
        assert "--dangerously-skip-permissions" not in agent_kwargs[0]["cmd"]
        assert "input" not in agent_kwargs[0]["keys"]
        assert "capture_output" not in agent_kwargs[0]["keys"]
        assert agent_kwargs[0]["stdin_readable"] is True
        prompt = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert (
            'LLM_WIKI_AUTO_COMMIT=1 git commit -m "docs(wiki): auto-update [bot]"'
            in prompt
        )
        mode = stat.S_IMODE(Path(".git/llm-wiki-prompt.txt").stat().st_mode)
        if os.name == "nt":
            assert Path(".git/llm-wiki-prompt.txt").is_file()
        else:
            assert mode == 0o600

    def test_agent_nonzero_records_failure(self, tmp_project, monkeypatch):
        monkeypatch.setattr(
            "llm_wiki_cli.commands.extract_cmd.get_inventory_result",
            lambda *a, **k: InventoryResult(
                {"a.py": {"language": "python", "classes": [], "functions": []}},
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.commands.extract_cmd.get_call_graph", lambda inv: {}
        )

        def fake_run(cmd, *args, **kwargs):
            if cmd[:2] == ["git", "diff"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="diff\n", stderr="")
            if cmd[0] == "aider":
                return subprocess.CompletedProcess(cmd, 2)
            raise AssertionError(f"unexpected command: {cmd}")

        with patch(
            "llm_wiki_cli.commands.trigger_cmd.subprocess.run", side_effect=fake_run
        ):
            trigger_cmd.run(_make_args(agent="aider"))

        state = circuit_breaker.load_state(tmp_project / ".git")
        assert state["consecutive_failures"] == 1
