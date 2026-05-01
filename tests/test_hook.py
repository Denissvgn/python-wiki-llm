"""Tests for commands/hook_cmd.py"""
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import hook_cmd


def _make_args(**kwargs):
    defaults = {"wiki_dir": "docs/llm_wiki", "agent": None, "force": False}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_agent_config(wiki_dir: str, agent: str):
    git_config = Path(".git") / ".llm-wiki-agent"
    git_config.parent.mkdir(parents=True, exist_ok=True)
    git_config.write_text(agent)


class TestHookReadsAgentConfig:
    def test_hook_bakes_agent_from_config(self, tmp_project):
        """post-commit hook contains --agent from .llm-wiki-agent."""
        _write_agent_config("docs/llm_wiki", "aider")
        args = _make_args()
        hook_cmd.run(args)


        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "--agent aider" in hook_text

    def test_hook_bakes_agent_from_cli_override(self, tmp_project):
        """--agent CLI flag takes precedence over config file."""
        _write_agent_config("docs/llm_wiki", "aider")
        args = _make_args(agent="opencode")
        hook_cmd.run(args)

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "--agent opencode" in hook_text
        assert "--agent aider" not in hook_text

    def test_hook_defaults_to_claude_when_no_config(self, tmp_project, capsys):
        """Falls back to 'claude' with a warning when no config file exists."""
        args = _make_args()  # no config file, no --agent
        hook_cmd.run(args)

        out = capsys.readouterr().out
        assert "warning" in out.lower() or "Warning" in out

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "--agent claude" in hook_text


class TestHookIDEAgentInstallsPromptHook:
    """IDE agents get a prompt-generation hook, not a headless sync hook."""

    def test_post_commit_installed_for_copilot(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)

        hook_path = Path(".git/hooks/post-commit")
        assert hook_path.exists()
        hook_text = hook_path.read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert 'LLM_WIKI_OPEN_PROMPT:-0' in hook_text

    def test_post_commit_installed_for_cursor(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "cursor")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text

    def test_post_commit_installed_for_generic(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "generic")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text

    def test_ide_hook_contains_wiki_dir(self, tmp_project):
        _write_agent_config("my_docs/wiki", "copilot")
        args = _make_args(wiki_dir="my_docs/wiki")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "my_docs/wiki" in hook_text

    def test_agent_override_bypasses_ui_restriction(self, tmp_project, capsys):
        """Passing --agent claude explicitly still installs the headless hook even if config says copilot."""
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args(agent="claude")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "--agent claude" in hook_text
        assert "generate-prompt" not in hook_text

    def test_ide_output_message_mentions_paste(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)

        out = capsys.readouterr().out
        assert "generate-prompt" in out or "paste" in out.lower()


class TestHookReadsCustomWikiDir:
    def test_reads_config_from_custom_wiki_dir(self, tmp_project):
        _write_agent_config("my_docs/wiki", "aider")
        args = _make_args(wiki_dir="my_docs/wiki")
        hook_cmd.run(args)

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "--agent aider" in hook_text


class TestPostCommitAutoCommitGuard:
    """post-commit hooks must skip when LLM_WIKI_AUTO_COMMIT is set."""

    def test_cli_post_commit_has_auto_commit_guard(self, tmp_project):
        _write_agent_config("docs/llm_wiki", "claude")
        args = _make_args()
        hook_cmd.run(args)
        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "LLM_WIKI_AUTO_COMMIT" in hook_text


class TestHookInstallSafety:
    def test_unrelated_existing_hook_is_preserved(self, tmp_project):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            hook_cmd.run(_make_args(agent="claude"))

        assert exc_info.value.code == 1
        assert hook_path.read_text(encoding="utf-8") == "#!/bin/sh\necho custom\n"

    def test_force_replaces_unrelated_existing_hook(self, tmp_project):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")

        hook_cmd.run(_make_args(agent="claude", force=True))

        hook_text = hook_path.read_text(encoding="utf-8")
        assert "LLM Wiki" in hook_text
        assert "echo custom" not in hook_text

    def test_managed_existing_hook_is_replaced(self, tmp_project):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\n# LLM Wiki old hook\n", encoding="utf-8")

        hook_cmd.run(_make_args(agent="aider"))

        hook_text = hook_path.read_text(encoding="utf-8")
        assert "--agent aider" in hook_text

    def test_ide_post_commit_has_auto_commit_guard(self, tmp_project):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)
        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "LLM_WIKI_AUTO_COMMIT" in hook_text
