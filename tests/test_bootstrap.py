"""Tests for commands/bootstrap_cmd.py"""
import os
import shutil
import subprocess
import textwrap
import types
from pathlib import Path

import pytest
from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult

# True when git is on PATH; used to guard git-dependent fixture steps.
_GIT_AVAILABLE = shutil.which("git") is not None


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
    if _GIT_AVAILABLE:
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(proj), "config", "user.email", "t@t.com"], capture_output=True, check=True)
        subprocess.run(["git", "-C", str(proj), "config", "user.name", "T"], capture_output=True, check=True)
    else:
        (proj / ".git").mkdir(exist_ok=True)

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
        """When two files define the same class name, both get qualified pages."""
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        entity_pages = list((wiki_dir / "entities").glob("*.md"))
        entity_names = {p.stem for p in entity_pages}

        # Both qualified entities must exist (one per source file)
        assert len([n for n in entity_names if "Config" in n]) == 2
        # Each qualified name must end with _Config
        for n in entity_names:
            if "Config" in n:
                assert n.endswith("_Config"), n

    def test_entity_page_contains_valid_source(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        entity_pages = list((wiki_dir / "entities").glob("*Config*.md"))
        assert len(entity_pages) >= 1
        for ep in entity_pages:
            content = ep.read_text(encoding="utf-8")
            # Page must reference one of the two source files
            assert "config.py" in content

    def test_module_collision_uses_simple_name(self, tmp_collision_project, capsys):
        """When two files share the same stem, both get qualified module pages."""
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        module_pages = list((wiki_dir / "modules").glob("*.md"))
        module_names = {p.stem for p in module_pages}

        # Both qualified modules must exist (one per source file)
        assert len([n for n in module_names if "config" in n]) == 2

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

    def test_same_directory_multilanguage_stem_collision_gets_extension_suffixes(
        self, tmp_path, monkeypatch, capsys,
    ):
        from llm_wiki_cli.commands import lint_cmd

        inventory = {
            "foo.py": {
                "language": "python",
                "classes": [{
                    "name": "Thing", "bases": [], "line": 1, "docstring": "",
                    "decorators": [], "attributes": [], "methods": [],
                }],
                "functions": [],
                "imports": [],
                "module_docstring": "",
            },
            "foo.ts": {
                "language": "typescript",
                "classes": [{
                    "name": "Thing", "bases": [], "line": 1, "docstring": "",
                    "decorators": [], "attributes": [], "methods": [],
                }],
                "functions": [],
                "imports": [],
                "module_docstring": "",
            },
        }
        result = InventoryResult(
            inventory,
            {
                "python": ExtractorStatus("python", "ok", 1),
                "typescript": ExtractorStatus("typescript", "ok", 1),
            },
        )
        monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", lambda *a, **k: result)
        monkeypatch.setattr(bootstrap_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.setattr(lint_cmd, "get_inventory_result", lambda *a, **k: result)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="docs/llm_wiki"))

        assert (wiki_dir / "modules" / "foo_py.md").exists()
        assert (wiki_dir / "modules" / "foo_ts.md").exists()
        assert (wiki_dir / "entities" / "foo_py_Thing.md").exists()
        assert (wiki_dir / "entities" / "foo_ts_Thing.md").exists()

        lint_cmd.run(types.SimpleNamespace(src_dir=".", wiki_dir="docs/llm_wiki"))

    def test_relationship_collision_resolves_by_import_module(self, tmp_path, monkeypatch):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg_a").mkdir()
        (proj / "pkg_b").mkdir()
        (proj / "consumer.py").write_text(
            "from pkg_a.models import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )
        (proj / "pkg_a" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg_b" / "models.py").write_text("class User:\n    pass\n")

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        a_page = (wiki_dir / "entities" / "pkg_a_models_User.md").read_text(encoding="utf-8")
        b_page = (wiki_dir / "entities" / "pkg_b_models_User.md").read_text(encoding="utf-8")
        assert "**used_by**" in a_page
        assert "../modules/consumer.md" in a_page
        assert "**used_by**" not in b_page
        assert "**imported_by**" not in b_page

    def test_relationship_resolves_current_package_relative_import(self, tmp_path, monkeypatch):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg").mkdir()
        (proj / "pkg" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg" / "service.py").write_text(
            "from .models import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        page = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert "**used_by**" in page
        assert "../modules/service.md" in page

    def test_relationship_resolves_parent_package_relative_import(self, tmp_path, monkeypatch):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg" / "sub").mkdir(parents=True)
        (proj / "pkg" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg" / "sub" / "service.py").write_text(
            "from ..models import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        page = (wiki_dir / "entities" / "User.md").read_text(encoding="utf-8")
        assert "**used_by**" in page
        assert "../modules/service.md" in page

    def test_ambiguous_duplicate_relationship_is_skipped(self, tmp_path, monkeypatch):
        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "pkg_a").mkdir()
        (proj / "pkg_b").mkdir()
        (proj / "consumer.py").write_text(
            "from shared import User\n\n"
            "def consume(user: User) -> User:\n"
            "    return user\n"
        )
        (proj / "pkg_a" / "models.py").write_text("class User:\n    pass\n")
        (proj / "pkg_b" / "models.py").write_text("class User:\n    pass\n")

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir=str(wiki_dir)))

        for page in (wiki_dir / "entities").glob("*User.md"):
            content = page.read_text(encoding="utf-8")
            assert "**used_by**" not in content
            assert "**imported_by**" not in content


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


class TestBootstrapCreatesManifest:
    """bootstrap must write a sync manifest so `llm-wiki sync` works afterwards."""

    def test_manifest_created(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        manifest_path = wiki_dir / ".llm-wiki-manifest.json"
        assert manifest_path.exists(), "bootstrap should create the sync manifest"

    def test_manifest_contains_sources(self, tmp_project, capsys):
        import json

        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        data = json.loads((wiki_dir / ".llm-wiki-manifest.json").read_text(encoding="utf-8"))
        assert "sources" in data
        assert len(data["sources"]) > 0
        # Every source entry should have a hash and entities list
        for filepath, entry in data["sources"].items():
            assert "hash" in entry
            assert "entities" in entry

    def test_sync_succeeds_after_bootstrap(self, tmp_project, capsys):
        """After bootstrap, running sync should not fail with 'no manifest'."""
        from llm_wiki_cli.commands import sync_cmd
        import types

        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))
        bootstrap_cmd.run(args)

        sync_args = types.SimpleNamespace(
            src_dir=".", wiki_dir=str(wiki_dir),
        )
        # Should not raise SystemExit
        sync_cmd.run(sync_args)
