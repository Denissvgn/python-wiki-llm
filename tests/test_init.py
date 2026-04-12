"""Tests for commands/init_cmd.py"""
import os
import types
from pathlib import Path

from llm_wiki_cli.commands import init_cmd


def _make_args(**kwargs):
    defaults = {"agent": "generic", "wiki_dir": "docs/llm_wiki"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestInitCreatesStructure:
    def test_directories_created(self, tmp_project):
        args = _make_args()
        init_cmd.run(args)

        base = Path("docs/llm_wiki")
        assert base.exists()
        assert (base / "entities").exists()
        assert (base / "modules").exists()
        assert (base / "workflows").exists()

    def test_core_files_created(self, tmp_project):
        args = _make_args()
        init_cmd.run(args)

        base = Path("docs/llm_wiki")
        assert (base / "index.md").exists()
        assert (base / "log.md").exists()
        assert "Index" in (base / "index.md").read_text()


class TestInitAgentSchemas:
    def test_claude_agent(self, tmp_project):
        args = _make_args(agent="claude")
        init_cmd.run(args)
        assert Path("CLAUDE.md").exists()
        content = Path("CLAUDE.md").read_text()
        assert "LLM Wiki Maintainer Constraints" in content

    def test_cursor_agent(self, tmp_project):
        args = _make_args(agent="cursor")
        init_cmd.run(args)
        assert Path(".cursorrules").exists()

    def test_copilot_agent(self, tmp_project):
        args = _make_args(agent="copilot")
        init_cmd.run(args)
        assert Path(".github/copilot-instructions.md").exists()

    def test_generic_agent(self, tmp_project):
        args = _make_args(agent="generic")
        init_cmd.run(args)
        assert Path(".agents.md").exists()


class TestInitPreservesContent:
    def test_appends_to_existing(self, tmp_project):
        Path("CLAUDE.md").write_text("# My Custom Rules\n\nDo good things.\n")
        args = _make_args(agent="claude")
        init_cmd.run(args)

        content = Path("CLAUDE.md").read_text()
        assert "My Custom Rules" in content
        assert "LLM Wiki Maintainer Constraints" in content

    def test_does_not_duplicate(self, tmp_project):
        args = _make_args(agent="claude")
        init_cmd.run(args)
        init_cmd.run(args)  # run twice

        content = Path("CLAUDE.md").read_text()
        assert content.count("LLM Wiki Maintainer Constraints") == 1

    def test_idempotent_structure(self, tmp_project):
        args = _make_args()
        init_cmd.run(args)
        init_cmd.run(args)

        base = Path("docs/llm_wiki")
        assert (base / "index.md").exists()


class TestInitCustomWikiDir:
    def test_custom_wiki_dir_created(self, tmp_project):
        args = _make_args(agent="claude", wiki_dir="my_docs/wiki")
        init_cmd.run(args)

        assert Path("my_docs/wiki").exists()
        assert Path("my_docs/wiki/index.md").exists()

    def test_agent_file_uses_custom_path(self, tmp_project):
        args = _make_args(agent="claude", wiki_dir="my_docs/wiki")
        init_cmd.run(args)

        content = Path("CLAUDE.md").read_text()
        assert "my_docs/wiki" in content
        assert "docs/llm_wiki" not in content


class TestInitAgentInstallCheck:
    def test_no_warning_for_schema_only_agents(self, tmp_project, capsys):
        """cursor/copilot/generic have no CLI — no warning expected."""
        for agent in ("cursor", "copilot", "generic"):
            args = _make_args(agent=agent)
            init_cmd.run(args)
            out = capsys.readouterr().out
            assert "not installed" not in out

    def test_warning_when_cli_agent_missing(self, tmp_project, capsys, monkeypatch):
        """If 'claude' binary is absent, user sees a clear warning."""
        monkeypatch.setattr("shutil.which", lambda _: None)
        args = _make_args(agent="claude")
        init_cmd.run(args)
        out = capsys.readouterr().out
        assert "not installed" in out
        assert "claude" in out
        # Schema file is still created despite the warning
        assert Path("CLAUDE.md").exists()

    def test_no_warning_when_cli_agent_present(self, tmp_project, capsys, monkeypatch):
        """No warning when the executable is found on PATH."""
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        args = _make_args(agent="claude")
        init_cmd.run(args)
        out = capsys.readouterr().out
        assert "not installed" not in out


class TestInitPersistsAgentConfig:
    def test_agent_config_written(self, tmp_project):
        """init writes .llm-wiki-agent with the chosen agent name."""
        args = _make_args(agent="claude")
        init_cmd.run(args)
        config = Path(".git/.llm-wiki-agent")
        assert config.exists()
        assert config.read_text().strip() == "claude"

    def test_agent_config_reflects_chosen_agent(self, tmp_project):
        """The config file stores whichever agent was passed."""
        for agent in ("aider", "cursor", "copilot", "generic"):
            args = _make_args(agent=agent)
            init_cmd.run(args)
            config = Path(".git/.llm-wiki-agent")
            assert config.read_text().strip() == agent

    def test_agent_config_custom_wiki_dir(self, tmp_project):
        """Config is written to .git/ regardless of which wiki dir is used."""
        args = _make_args(agent="opencode", wiki_dir="my_docs/wiki")
        init_cmd.run(args)
        assert (Path(".git/.llm-wiki-agent")).read_text().strip() == "opencode"
        assert not (Path("my_docs/wiki/.llm-wiki-agent")).exists()
