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
