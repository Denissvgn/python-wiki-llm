"""Tests for commands/bootstrap_cmd.py"""
import types
import textwrap
from pathlib import Path

from llm_wiki_cli.commands import bootstrap_cmd


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestBootstrapEntityPages:
    def test_creates_entity_per_class(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        assert (wiki_dir / "entities" / "User.md").exists()
        assert (wiki_dir / "entities" / "Item.md").exists()

    def test_entity_content(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "entities" / "User.md").read_text()
        assert "# User" in content
        assert "name" in content
        assert "email" in content


class TestBootstrapModulePages:
    def test_creates_module_per_file(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        assert (wiki_dir / "modules" / "models.md").exists()
        assert (wiki_dir / "modules" / "main.md").exists()

    def test_module_content(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "modules" / "models.md").read_text()
        assert "# models Module" in content


class TestBootstrapIndex:
    def test_creates_index(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        index = (wiki_dir / "index.md").read_text()
        assert "User" in index
        assert "Item" in index
        assert "models" in index


class TestBootstrapLog:
    def test_appends_log(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        log = (wiki_dir / "log.md").read_text()
        assert "bootstrap" in log.lower()


class TestBootstrapOverwrite:
    def test_skip_existing_without_flag(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        # Modify a page
        user_page = wiki_dir / "entities" / "User.md"
        user_page.write_text("CUSTOM CONTENT")

        # Run again without --overwrite
        bootstrap_cmd.run(args)
        assert user_page.read_text() == "CUSTOM CONTENT"

    def test_overwrite_flag(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        user_page = wiki_dir / "entities" / "User.md"
        user_page.write_text("CUSTOM CONTENT")

        args_ow = _make_args(src_dir=".", wiki_dir=str(wiki_dir), overwrite=True)
        bootstrap_cmd.run(args_ow)
        assert user_page.read_text() != "CUSTOM CONTENT"
        assert "# User" in user_page.read_text()


class TestBootstrapShallow:
    def test_shallow_depth(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir), depth="shallow")
        bootstrap_cmd.run(args)

        # Pages created but minimal content
        assert (wiki_dir / "entities" / "User.md").exists()


class TestBootstrapSkipWorkflows:
    def test_skip_workflows_flag(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir), skip_workflows=True)
        bootstrap_cmd.run(args)

        workflows_dir = wiki_dir / "workflows"
        workflow_files = list(workflows_dir.glob("*.md"))
        assert len(workflow_files) == 0


class TestBootstrapUpdatesAgentConstraints:
    def test_updates_path_in_constraint_block(self, tmp_project, capsys):
        from llm_wiki_cli.commands import init_cmd
        import types

        init_cmd.run(types.SimpleNamespace(agent="claude", wiki_dir="docs/llm_wiki"))
        assert "docs/llm_wiki" in Path("CLAUDE.md").read_text()

        # Bootstrap to a different wiki dir
        wiki_dir = tmp_project / "my_docs" / "wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = Path("CLAUDE.md").read_text()
        # Verify the constraint block was updated (preamble outside the block is unchanged)
        start = content.index("# --- LLM Wiki Maintainer Constraints ---")
        end = content.index("# --- End LLM Wiki Constraints ---") + len("# --- End LLM Wiki Constraints ---")
        block = content[start:end]
        assert str(wiki_dir) in block
        assert "docs/llm_wiki" not in block

    def test_no_change_when_default_path(self, tmp_project, capsys):
        from llm_wiki_cli.commands import init_cmd
        import types

        init_cmd.run(types.SimpleNamespace(agent="claude", wiki_dir="docs/llm_wiki"))
        original = Path("CLAUDE.md").read_text()

        # Bootstrap with the default path — file should be unchanged
        args = _make_args(src_dir=".", wiki_dir="docs/llm_wiki")
        bootstrap_cmd.run(args)

        assert Path("CLAUDE.md").read_text() == original
