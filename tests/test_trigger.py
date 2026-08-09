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

from llm_wiki_cli.commands import generate_prompt_cmd, trigger_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services import circuit_breaker, extraction_service, plugins
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_SCHEMA_VERSION,
    SourceSelectionError,
    resolve_source_selection,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.wiki_git_policy import (
    WikiGitDisposition,
    WikiGitPolicy,
)


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


def test_trigger_rejects_omitted_persisted_explicit_profile_before_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    selected = Path("selected")
    selected.mkdir()
    (selected / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    profile = Path("config/sources.json")
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    policy = resolve_source_selection(tmp_path, "config/sources.json")
    assert policy is not None
    snapshot = build_source_snapshot(tmp_path, selection_policy=policy)
    wiki = Path("docs/llm_wiki")
    wiki.mkdir(parents=True)
    SyncManifest(
        generation_inputs=with_source_selection_generation_input(
            {},
            snapshot.source_selection_identity,
            snapshot.source_selection_inputs,
        )
    ).save(wiki)
    monkeypatch.setattr(trigger_cmd, "_is_breaker_open", lambda: False)
    monkeypatch.setattr(trigger_cmd, "_record_trigger_start", lambda *_args: None)

    def fail_git(*_args, **_kwargs):
        pytest.fail("persisted identity must be checked before reading Git diff")

    monkeypatch.setattr(trigger_cmd, "_fetch_last_commit_diff", fail_git)

    with pytest.raises(SourceSelectionError, match="persisted"):
        trigger_cmd._run_sync(_make_args(src_dir="."))


@pytest.fixture(autouse=True)
def _included_prompt_policy(monkeypatch):
    monkeypatch.setattr(
        generate_prompt_cmd,
        "classify_wiki_git_policy",
        lambda *_args, **_kwargs: WikiGitPolicy(
            disposition=WikiGitDisposition.INCLUDED,
            reason="included",
            repository_root=Path.cwd(),
            wiki_path="docs/llm_wiki",
        ),
    )


class TestTriggerRunStructure:
    def test_run_sync_stays_a_small_coordinator(self):
        assert _body_line_count(trigger_cmd._run_sync) <= 40


class TestTriggerLockWait:
    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [(None, 0.0), ("", 0.0), ("0.25", 0.25), ("2", 2.0)],
    )
    def test_lock_wait_environment_reaches_wiki_lock(
        self, monkeypatch, env_value, expected
    ):
        if env_value is None:
            monkeypatch.delenv("LLM_WIKI_LOCK_WAIT", raising=False)
        else:
            monkeypatch.setenv("LLM_WIKI_LOCK_WAIT", env_value)
        lock_factory = MagicMock()
        monkeypatch.setattr(trigger_cmd, "WikiLock", lock_factory)
        monkeypatch.setattr(trigger_cmd, "_run_sync", MagicMock())

        trigger_cmd.run(_make_args())

        lock_factory.assert_called_once_with(
            trigger_cmd.GIT_DIR,
            wait_seconds=expected,
        )

    @pytest.mark.parametrize("env_value", ["-1", "nan", "inf", "not-a-number"])
    def test_invalid_lock_wait_environment_is_rejected(self, monkeypatch, env_value):
        monkeypatch.setenv("LLM_WIKI_LOCK_WAIT", env_value)

        with pytest.raises(
            ValueError,
            match="LLM_WIKI_LOCK_WAIT must be a finite non-negative number",
        ):
            trigger_cmd.run(_make_args())


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
        state = {
            "consecutive_failures": 3,
            "state": "open",
            "last_failure_ts": "2999-01-01T00:00:00+00:00",
        }
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))

        trigger_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "OPEN" in out
        assert "Automatic recovery retries" in out

    def test_active_half_open_probe_reports_lease_and_recovery(
        self, tmp_project, capsys
    ):
        git_dir = tmp_project / ".git"
        state = {
            "consecutive_failures": 3,
            "state": "half-open",
            "last_failure_ts": "2999-01-01T00:00:00+00:00",
            "probe_started_ts": "2999-01-01T00:00:00+00:00",
        }
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))

        trigger_cmd.run(_make_args())

        out = capsys.readouterr().out
        assert "HALF-OPEN" in out
        assert "recovery probe lease" in out
        assert "Automatic recovery retries" in out


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


class TestTriggerExternalSource:
    def test_opted_in_external_source_reaches_git_inventory_and_prompt(
        self, tmp_project, monkeypatch
    ):
        external = tmp_project.parent / "external-source"
        selected = external / "selected"
        selected.mkdir(parents=True)
        (selected / "app.py").write_text(
            "def external_entry():\n    return 1\n",
            encoding="utf-8",
        )
        profile = external / "selection.json"
        profile.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": ["selected"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        seen = {
            "git_cwd": None,
            "inventory": None,
            "agent_calls": 0,
            "source_snapshot": None,
        }
        real_build_source_snapshot = trigger_cmd.build_source_snapshot
        initial_snapshot = real_build_source_snapshot(
            external,
            source_selection="selection.json",
        )
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                initial_snapshot.source_selection_identity,
                initial_snapshot.source_selection_inputs,
            )
        ).save(wiki)

        def capture_source_snapshot(src_dir, **kwargs):
            snapshot = real_build_source_snapshot(src_dir, **kwargs)
            seen["source_snapshot"] = snapshot
            return snapshot

        def fake_inventory(src_dir, **kwargs):
            seen["inventory"] = (src_dir, kwargs)
            return InventoryResult(
                {
                    "selected/app.py": {
                        "language": "python",
                        "classes": [],
                        "functions": [{"name": "external_entry", "line": 1}],
                    }
                },
                {},
                source_snapshot=kwargs["source_snapshot"],
            )

        def fake_run(cmd, *args, **kwargs):
            if cmd[:2] == ["git", "diff"]:
                seen["git_cwd"] = kwargs.get("cwd")
                diff = (
                    "diff --git a/selected/app.py b/selected/app.py\n"
                    "--- a/selected/app.py\n"
                    "+++ b/selected/app.py\n"
                    "@@ -1 +1 @@\n"
                    "-def old(): pass\n"
                    "+def external_entry(): return 1\n"
                )
                return subprocess.CompletedProcess(cmd, 0, stdout=diff, stderr="")
            if cmd[:3] == ["git", "rev-parse", "--show-toplevel"]:
                return subprocess.CompletedProcess(
                    cmd,
                    0,
                    stdout=f"{external}\n",
                    stderr="",
                )
            if cmd[0] == "claude":
                seen["agent_calls"] += 1
                return subprocess.CompletedProcess(cmd, 0)
            raise AssertionError(f"unexpected command: {cmd}")

        monkeypatch.setattr(
            trigger_cmd,
            "build_source_snapshot",
            capture_source_snapshot,
        )
        monkeypatch.setattr(extraction_service, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(trigger_cmd.subprocess, "run", fake_run)

        trigger_cmd.run(
            _make_args(
                src_dir=str(external),
                allow_external_src=True,
                source_selection="selection.json",
            )
        )

        assert Path(seen["git_cwd"]) == external
        inventory_src, inventory_kwargs = seen["inventory"]
        assert Path(inventory_src) == external
        assert inventory_kwargs["source_snapshot"] is seen["source_snapshot"]
        assert "source_selection" not in inventory_kwargs
        assert seen["agent_calls"] == 1
        prompt = Path(".git/llm-wiki-prompt.txt").read_text(encoding="utf-8")
        assert "selected/app.py" in prompt
        assert str(external) in prompt
        assert "--allow-external-src" in prompt
        assert "--source-selection selection.json" in prompt


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
    def test_prompt_artifact_redacts_credentials(self, tmp_project):
        secret = "ghp_abcdefghijklmnopqrstuvwxyz"

        path = trigger_cmd._write_prompt_file(f"Git diff:\n+TOKEN={secret}\n")

        content = path.read_text(encoding="utf-8")
        assert secret not in content
        assert "[REDACTED:credential]" in content
        assert content.endswith("[1 credential-like values redacted]\n")

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

    def test_invalid_template_records_failure_without_running_agent(
        self, tmp_project, monkeypatch, capsys
    ):
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
        monkeypatch.setattr(
            trigger_cmd,
            "_build_prompt",
            MagicMock(side_effect=plugins.PluginError("reserved Git directive")),
        )
        calls = []

        def fake_run(cmd, *args, **kwargs):
            calls.append(list(cmd))
            if cmd[:2] == ["git", "diff"]:
                return subprocess.CompletedProcess(cmd, 0, stdout="diff\n", stderr="")
            raise AssertionError(f"agent must not run: {cmd}")

        with patch(
            "llm_wiki_cli.commands.trigger_cmd.subprocess.run", side_effect=fake_run
        ):
            trigger_cmd.run(_make_args(agent="claude"))

        assert calls == [["git", "diff", "HEAD~1..HEAD"]]
        assert "Invalid agent prompt configuration" in capsys.readouterr().out
        state = circuit_breaker.load_state(tmp_project / ".git")
        assert state["consecutive_failures"] == 1

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
