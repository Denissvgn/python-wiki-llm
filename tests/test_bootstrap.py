"""Tests for commands/bootstrap_cmd.py"""
import os
import types
import textwrap
from pathlib import Path

import pytest
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


@pytest.fixture
def tmp_collision_project(tmp_path):
    """Project with the same class/module name in two different service directories."""
    proj = tmp_path / "project"
    proj.mkdir()

    import subprocess
    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(proj), "config", "user.email", "t@t.com"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(proj), "config", "user.name", "T"], capture_output=True, check=True)

    (proj / "pyproject.toml").write_text('[project]\nname = "sample"\nversion = "0.1.0"\n')

    # Two services each with a config.py that defines a Config class
    svc_a = proj / "services" / "auth-service" / "src"
    svc_a.mkdir(parents=True)
    (svc_a / "config.py").write_text(textwrap.dedent("""\
        class Config:
            \"\"\"Auth service config.\"\"\"
            secret: str = "s3cr3t"
    """))

    svc_b = proj / "services" / "order-service" / "src"
    svc_b.mkdir(parents=True)
    (svc_b / "config.py").write_text(textwrap.dedent("""\
        class Config:
            \"\"\"Order service config.\"\"\"
            db_url: str = "sqlite://"
    """))

    old_cwd = os.getcwd()
    os.chdir(proj)
    yield proj
    os.chdir(old_cwd)


class TestBootstrapCollisions:
    def test_entity_collision_uses_simple_name(self, tmp_collision_project, capsys):
        """When two files define the same class name, only one page is created (last-writer-wins)."""
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        entity_pages = list((wiki_dir / "entities").glob("*.md"))
        entity_names = {p.stem for p in entity_pages}

        # Simple unqualified page must exist — no qualifier prefixes
        assert "Config" in entity_names
        # No qualifier-prefixed pages should exist
        assert not any("__" in n for n in entity_names), entity_names

    def test_entity_page_contains_valid_source(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = (wiki_dir / "entities" / "Config.md").read_text(encoding="utf-8")
        # Page must reference one of the two source files
        assert "config.py" in content

    def test_module_collision_uses_simple_name(self, tmp_collision_project, capsys):
        """When two files share the same stem, only one module page is created (last-writer-wins)."""
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        module_pages = list((wiki_dir / "modules").glob("*.md"))
        module_names = {p.stem for p in module_pages}

        # Simple unqualified page must exist
        assert "config" in module_names
        # No qualifier-prefixed pages should exist
        assert not any("__" in n for n in module_names), module_names

    def test_index_has_no_duplicate_entries(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        lines = (wiki_dir / "index.md").read_text(encoding="utf-8").splitlines()
        link_lines = [l for l in lines if l.startswith("- [")]
        seen = set()
        for line in link_lines:
            assert line not in seen, f"Duplicate index entry: {line}"
            seen.add(line)

    def test_no_collision_keeps_short_name(self, tmp_project, capsys):
        """Single-definition classes/modules must keep their plain short name."""
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        assert (wiki_dir / "entities" / "User.md").exists()
        assert (wiki_dir / "modules" / "models.md").exists()


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

        content = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
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

        content = (wiki_dir / "modules" / "models.md").read_text(encoding="utf-8")
        assert "# models Module" in content


class TestBootstrapIndex:
    def test_creates_index(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        index = (wiki_dir / "index.md").read_text(encoding="utf-8")
        assert "User" in index
        assert "Item" in index
        assert "models" in index


class TestBootstrapLog:
    def test_appends_log(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        log = (wiki_dir / "log.md").read_text(encoding="utf-8")
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
        assert user_page.read_text(encoding="utf-8") == "CUSTOM CONTENT"

    def test_overwrite_flag(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        user_page = wiki_dir / "entities" / "User.md"
        user_page.write_text("CUSTOM CONTENT")

        args_ow = _make_args(src_dir=".", wiki_dir=str(wiki_dir), overwrite=True)
        bootstrap_cmd.run(args_ow)
        assert user_page.read_text(encoding="utf-8") != "CUSTOM CONTENT"
        assert "# User" in user_page.read_text(encoding="utf-8")


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
        assert "docs/llm_wiki" in Path("CLAUDE.md").read_text(encoding="utf-8")

        # Bootstrap to a different wiki dir
        wiki_dir = tmp_project / "my_docs" / "wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
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
        original = Path("CLAUDE.md").read_text(encoding="utf-8")

        # Bootstrap with the default path — file should be unchanged
        args = _make_args(src_dir=".", wiki_dir="docs/llm_wiki")
        bootstrap_cmd.run(args)

        assert Path("CLAUDE.md").read_text(encoding="utf-8") == original
