"""Tests for commands/hook_cmd.py"""
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import hook_cmd


def _make_args(**kwargs):
    defaults = {"enable_versioning": False, "wiki_dir": "docs/llm_wiki", "agent": None}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_agent_config(wiki_dir: str, agent: str):
    p = Path(wiki_dir)
    p.mkdir(parents=True, exist_ok=True)
    (p / ".llm-wiki-agent").write_text(agent)


class TestHookReadsAgentConfig:
    def test_hook_bakes_agent_from_config(self, tmp_project):
        """post-commit hook contains --agent from .llm-wiki-agent."""
        _write_agent_config("docs/llm_wiki", "aider")
        args = _make_args()
        hook_cmd.run(args)


        hook_text = (Path(".git/hooks/post-commit")).read_text()
        assert "--agent aider" in hook_text

    def test_hook_bakes_agent_from_cli_override(self, tmp_project):
        """--agent CLI flag takes precedence over config file."""
        _write_agent_config("docs/llm_wiki", "aider")
        args = _make_args(agent="opencode")
        hook_cmd.run(args)

        hook_text = (Path(".git/hooks/post-commit")).read_text()
        assert "--agent opencode" in hook_text
        assert "--agent aider" not in hook_text

    def test_hook_defaults_to_claude_when_no_config(self, tmp_project, capsys):
        """Falls back to 'claude' with a warning when no config file exists."""
        args = _make_args()  # no config file, no --agent
        hook_cmd.run(args)

        out = capsys.readouterr().out
        assert "warning" in out.lower() or "Warning" in out

        hook_text = (Path(".git/hooks/post-commit")).read_text()
        assert "--agent claude" in hook_text


class TestHookIDEAgentInstallsPromptHook:
    """IDE agents get a prompt-generation hook, not a headless sync hook."""

    def test_post_commit_installed_for_copilot(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)

        hook_path = Path(".git/hooks/post-commit")
        assert hook_path.exists()
        hook_text = hook_path.read_text()
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text

    def test_post_commit_installed_for_cursor(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "cursor")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text()
        assert "generate-prompt" in hook_text

    def test_post_commit_installed_for_generic(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "generic")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text()
        assert "generate-prompt" in hook_text

    def test_ide_hook_contains_wiki_dir(self, tmp_project):
        _write_agent_config("my_docs/wiki", "copilot")
        args = _make_args(wiki_dir="my_docs/wiki")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text()
        assert "my_docs/wiki" in hook_text

    def test_agent_override_bypasses_ui_restriction(self, tmp_project, capsys):
        """Passing --agent claude explicitly still installs the headless hook even if config says copilot."""
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args(agent="claude")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text()
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

        hook_text = (Path(".git/hooks/post-commit")).read_text()
        assert "--agent aider" in hook_text
