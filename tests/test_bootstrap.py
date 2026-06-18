"""Tests for commands/bootstrap_cmd.py"""

import ast
import inspect
import json
import os
import shutil
import subprocess
import textwrap
import types
from pathlib import Path

import pytest
from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.dependencies import analyze_dependencies

# True when git is on PATH; used to guard git-dependent fixture steps.
_GIT_AVAILABLE = shutil.which("git") is not None


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
        "format": "text",
        "source_adapter": False,
        "allow_external_src": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
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
    last_body_line = max(stmt.end_lineno for stmt in body)
    return last_body_line - first_body_line + 1


def test_bootstrap_run_stays_a_short_coordinator():
    assert _body_line_count(bootstrap_cmd.run) <= 40


@pytest.fixture
def tmp_collision_project(tmp_path):
    """Project with the same class/module name in two different service directories."""
    proj = tmp_path / "project"
    proj.mkdir()

    if _GIT_AVAILABLE:
        subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(proj), "config", "user.name", "T"],
            capture_output=True,
            check=True,
        )
    else:
        (proj / ".git").mkdir(exist_ok=True)

    (proj / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n'
    )

    # Two services each with a config.py that defines a Config class
    svc_a = proj / "services" / "auth-service" / "src"
    svc_a.mkdir(parents=True)
    (svc_a / "config.py").write_text(
        textwrap.dedent("""\
        class Config:
            \"\"\"Auth service config.\"\"\"
            secret: str = "s3cr3t"
    """)
    )

    svc_b = proj / "services" / "order-service" / "src"
    svc_b.mkdir(parents=True)
    (svc_b / "config.py").write_text(
        textwrap.dedent("""\
        class Config:
            \"\"\"Order service config.\"\"\"
            db_url: str = "sqlite://"
    """)
    )

    old_cwd = os.getcwd()
    os.chdir(proj)
    yield proj
    os.chdir(old_cwd)


class TestBootstrapCollisions:
    def test_bootstrap_json_summary_is_parseable_stdout(self, tmp_project, capsys):
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        args = _make_args(
            src_dir=".", wiki_dir=str(wiki_dir), format="json", source_adapter=True
        )

        bootstrap_cmd.run(args)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["schema_version"] == "llm-wiki-bootstrap-summary/v1"
        assert data["generated_wiki_path"] == str(wiki_dir).replace("\\", "/")
        assert data["source_files"] >= 3
        assert data["classes"] >= 2
        assert data["manifest_path"].endswith(".llm-wiki-manifest.json")
        assert data["created_files"]
        assert "Bootstrapping wiki" in captured.err

    def test_bootstrap_prints_long_phase_progress(self, tmp_collision_project, capsys):
        wiki_dir = tmp_collision_project / "docs" / "llm_wiki"
        args = _make_args(src_dir=".", wiki_dir=str(wiki_dir))

        bootstrap_cmd.run(args)

        out = capsys.readouterr().out
        assert "Extracting source inventory..." in out
        assert "Building cross-reference relationships..." in out
        assert "Generating entity and module pages..." in out
        assert "Writing sync manifest..." in out

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
        link_lines = [line for line in lines if line.startswith("- [")]
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
        self,
        tmp_path,
        monkeypatch,
        capsys,
    ):
        from llm_wiki_cli.commands import lint_cmd

        inventory = {
            "foo.py": {
                "language": "python",
                "classes": [
                    {
                        "name": "Thing",
                        "bases": [],
                        "line": 1,
                        "docstring": "",
                        "decorators": [],
                        "attributes": [],
                        "methods": [],
                    }
                ],
                "functions": [],
                "imports": [],
                "module_docstring": "",
            },
            "foo.ts": {
                "language": "typescript",
                "classes": [
                    {
                        "name": "Thing",
                        "bases": [],
                        "line": 1,
                        "docstring": "",
                        "decorators": [],
                        "attributes": [],
                        "methods": [],
                    }
                ],
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
        monkeypatch.setattr(
            bootstrap_cmd, "get_inventory_result", lambda *a, **k: result
        )
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

    def test_relationship_collision_resolves_by_import_module(
        self, tmp_path, monkeypatch
    ):
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

        a_page = (wiki_dir / "entities" / "pkg_a_models_User.md").read_text(
            encoding="utf-8"
        )
        b_page = (wiki_dir / "entities" / "pkg_b_models_User.md").read_text(
            encoding="utf-8"
        )
        assert "**used_by**" in a_page
        assert "../modules/consumer.md" in a_page
        assert "**used_by**" not in b_page
        assert "**imported_by**" not in b_page

    def test_relationship_resolves_current_package_relative_import(
        self, tmp_path, monkeypatch
    ):
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

    def test_relationship_resolves_parent_package_relative_import(
        self, tmp_path, monkeypatch
    ):
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

    def test_workflow_links_use_collision_aware_module_pages(
        self, tmp_path, monkeypatch, capsys
    ):
        from llm_wiki_cli.commands import lint_cmd

        proj = tmp_path / "project"
        proj.mkdir()
        (proj / "models").mkdir()
        (proj / "schemas").mkdir()
        (proj / "routers").mkdir()
        (proj / "models" / "task.py").write_text("class Task:\n    pass\n")
        (proj / "schemas" / "task.py").write_text("class TaskCreate:\n    pass\n")
        (proj / "schemas" / "common.py").write_text(
            "class MessageResponse:\n    pass\n"
        )
        (proj / "routers" / "tasks.py").write_text(
            textwrap.dedent("""\
            from models.task import Task
            from schemas.task import TaskCreate as CreateSchema
            from schemas.common import MessageResponse

            def create_task(task: Task, data: CreateSchema) -> MessageResponse:
                return MessageResponse()
        """)
        )

        monkeypatch.chdir(proj)
        wiki_dir = proj / "docs" / "llm_wiki"
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir=str(wiki_dir), skip_workflows=False)
        )

        workflow = (wiki_dir / "workflows" / "create_task.md").read_text(
            encoding="utf-8"
        )
        assert "../modules/task.md" not in workflow
        assert "../modules/models_task.md" in workflow
        assert "../modules/schemas_task.md" in workflow

        lint_cmd.run(types.SimpleNamespace(src_dir=".", wiki_dir=str(wiki_dir)))


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
    def test_source_adapter_skips_agent_constraint_update(self, tmp_project, capsys):
        from llm_wiki_cli.commands import init_cmd
        import types

        init_cmd.run(types.SimpleNamespace(agent="claude", wiki_dir="docs/llm_wiki"))
        wiki_dir = tmp_project / "adapter_wiki"

        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir=str(wiki_dir), source_adapter=True)
        )

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        start = content.index("# --- LLM Wiki Maintainer Constraints ---")
        end = content.index("# --- End LLM Wiki Constraints ---") + len(
            "# --- End LLM Wiki Constraints ---"
        )
        block = content[start:end]
        assert "docs/llm_wiki" in block
        assert str(wiki_dir) not in block

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
        end = content.index("# --- End LLM Wiki Constraints ---") + len(
            "# --- End LLM Wiki Constraints ---"
        )
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

        data = json.loads(
            (wiki_dir / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
        )
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
            src_dir=".",
            wiki_dir=str(wiki_dir),
        )
        # Should not raise SystemExit
        sync_cmd.run(sync_args)


class TestBootstrapExternalSource:
    def test_allows_external_src_with_explicit_flag(
        self, tmp_path, monkeypatch, capsys
    ):
        workspace = tmp_path / "workspace"
        source = tmp_path / "source"
        workspace.mkdir()
        source.mkdir()
        (source / "app.py").write_text(
            "class ExternalApp:\n    pass\n", encoding="utf-8"
        )

        monkeypatch.chdir(workspace)
        bootstrap_cmd.run(
            _make_args(
                src_dir=str(source),
                wiki_dir="docs/llm_wiki",
                format="json",
                source_adapter=True,
                allow_external_src=True,
            )
        )

        data = json.loads(capsys.readouterr().out)
        assert data["src_dir"] == str(source)
        assert (workspace / "docs" / "llm_wiki" / "modules" / "app.md").exists()


class TestGenerateFlowMd:
    def test_renders_entry_modules_and_diagram(self):
        flow = {
            "entry": {"id": "api-run", "category": "api", "file": "pkg/api.py", "symbol": "run", "label": "run"},
            "steps": [
                {"depth": 0, "file": "pkg/api.py", "symbol": "run", "kind": "entry"},
                {"depth": 1, "file": "pkg/helper.py", "symbol": "work", "kind": "internal"},
                {"depth": 1, "file": None, "symbol": "getcwd", "kind": "external"},
            ],
            "modules_touched": ["pkg/api.py", "pkg/helper.py"],
            "truncated": True,
        }
        md = bootstrap_cmd._generate_flow_md(
            flow, {"pkg/api.py": "api", "pkg/helper.py": "helper"}
        )
        assert md.startswith("# run")
        assert "**Entry point:** `run` (`api`)" in md
        assert "[api](../modules/api.md)" in md
        assert "[helper](../modules/helper.md)" in md
        assert "sequenceDiagram" in md
        assert "-->>" in md  # external call rendered as a dashed arrow
        assert "truncated" in md
        assert "## Behavior" in md

    def test_no_calls_uses_placeholder(self):
        flow = {
            "entry": {"id": "api-x", "category": "api", "file": "m.py", "symbol": "x", "label": "x"},
            "steps": [{"depth": 0, "file": "m.py", "symbol": "x", "kind": "entry"}],
            "modules_touched": ["m.py"],
            "truncated": False,
        }
        md = bootstrap_cmd._generate_flow_md(flow, {"m.py": "m"})
        assert "No outbound calls detected" in md
        assert "sequenceDiagram" not in md


class TestBootstrapFlows:
    def _write_project(self, tmp_path):
        (tmp_path / "api.py").write_text(textwrap.dedent('''\
            __all__ = ["run"]

            def run():
                return _helper()

            def _helper():
                return 1
        '''))

    def test_generates_flow_page_with_sequence_diagram(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        flow_page = tmp_path / "wiki" / "flows" / "api-run.md"
        assert flow_page.exists()
        text = flow_page.read_text(encoding="utf-8")
        assert "```mermaid" in text
        assert "sequenceDiagram" in text
        assert "_helper" in text
        assert "## Behavior" in text

    def test_index_lists_user_flows(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "## User Flows" in index
        assert "[api-run](flows/api-run.md)" in index

    def test_skip_flows_writes_no_flow_pages(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki", skip_flows=True))
        assert list((tmp_path / "wiki" / "flows").glob("*.md")) == []

    def test_json_summary_counts_flows(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", format="json", source_adapter=True)
        )
        data = json.loads(capsys.readouterr().out)
        assert data["flows"] == 1


def _pymod(*imports, functions=None, module_calls=None):
    """A minimal deep-inventory Python entry for dependency analysis."""
    entry = {
        "language": "python",
        "imports": [{"module": m, "name": n} for m, n in imports],
        "classes": [],
        "functions": [{"name": f} for f in (functions or [])],
    }
    if module_calls:
        entry["module_calls"] = module_calls
    return entry


class TestGenerateDependenciesMd:
    def _analysis(self, tmp_path):
        inventory = {
            "pkg/a.py": _pymod(("pkg.b", "B"), ("requests", "get")),
            "pkg/b.py": _pymod(("pkg.a", "A")),
        }
        analysis = analyze_dependencies(inventory, str(tmp_path))
        return analysis, {"pkg/a.py": "a", "pkg/b.py": "b"}

    def test_renders_graph_cycles_metrics_and_external(self, tmp_path):
        analysis, page_map = self._analysis(tmp_path)
        md = bootstrap_cmd._generate_dependencies_md(analysis, page_map)
        assert md.startswith("# Dependencies")
        assert "```mermaid" in md and "flowchart TD" in md
        assert 'click n0 "modules/a.md"' in md  # node hyperlinks to its page
        assert "==>" in md  # the a⇄b cycle edges are highlighted
        assert "## Cycles" in md
        assert "[a](modules/a.md) ⇄ [b](modules/b.md)" in md
        assert "## Fan-in / Fan-out" in md
        assert "| [a](modules/a.md) |" in md
        assert "### python" in md
        assert "⚠️ **Undeclared:** `requests`" in md
        assert md.rstrip().endswith("Replace this placeholder._")
        assert "## Notes" in md

    def test_degrades_cleanly_without_cycles_or_external(self, tmp_path):
        inventory = {"solo.py": _pymod()}
        analysis = analyze_dependencies(inventory, str(tmp_path))
        md = bootstrap_cmd._generate_dependencies_md(analysis, {"solo.py": "solo"})
        assert "*No import cycles detected.*" in md
        assert "*No external dependencies detected.*" in md

    def test_package_detail_collapses_and_drops_links(self, tmp_path):
        analysis, page_map = self._analysis(tmp_path)
        md = bootstrap_cmd._generate_dependencies_md(analysis, page_map, detail="package")
        assert "Collapsed to top-level packages" in md
        assert 'n0["pkg"]' in md
        assert "click" not in md  # package nodes are not per-module links

    def test_is_deterministic(self, tmp_path):
        analysis, page_map = self._analysis(tmp_path)
        assert bootstrap_cmd._generate_dependencies_md(
            analysis, page_map
        ) == bootstrap_cmd._generate_dependencies_md(analysis, page_map)


class TestGenerateLoadOrderMd:
    def test_renders_order_side_effects_and_factories(self, tmp_path):
        inventory = {
            "pkg/a.py": _pymod(
                ("pkg.b", "B"),
                functions=["create_app"],
                module_calls=[{"name": "Flask", "target": "app", "line": 1}],
            ),
            "pkg/b.py": _pymod(),
        }
        analysis = analyze_dependencies(inventory, str(tmp_path))
        md = bootstrap_cmd._generate_load_order_md(
            analysis, {"pkg/a.py": "a", "pkg/b.py": "b"}
        )
        assert md.startswith("# Load order")
        # b loads before a because a imports b
        assert md.index("[b](modules/b.md)") < md.index("[a](modules/a.md)")
        assert "## Module-level side effects" in md
        assert "`app = Flask`" in md
        assert "## Factory / wiring" in md
        assert "`create_app`" in md
        assert "## Notes" in md

    def test_cyclic_group_marked_indeterminate(self, tmp_path):
        inventory = {"a.py": _pymod(("b", "x")), "b.py": _pymod(("a", "y"))}
        analysis = analyze_dependencies(inventory, str(tmp_path))
        md = bootstrap_cmd._generate_load_order_md(analysis, {"a.py": "a", "b.py": "b"})
        assert "Indeterminate (cyclic) groups" in md
        assert "[a](modules/a.md) ⇄ [b](modules/b.md)" in md

    def test_empty_sections_use_placeholders(self, tmp_path):
        analysis = analyze_dependencies({"solo.py": _pymod()}, str(tmp_path))
        md = bootstrap_cmd._generate_load_order_md(analysis, {"solo.py": "solo"})
        assert "*No import-time side effects detected.*" in md
        assert "*No factory or wiring functions detected.*" in md
        assert "Indeterminate (cyclic) groups" not in md


class TestBootstrapArchitecturePages:
    def _write_project(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "s"\nversion = "0.1.0"\ndependencies = ["requests"]\n'
        )
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text(
            "from pkg.b import work\nimport requests\n\n\ndef run():\n"
            "    return work()\n"
        )
        (pkg / "b.py").write_text("app = object()\n\n\ndef work():\n    return 1\n")

    def test_creates_both_pages_with_valid_mermaid(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        deps = (tmp_path / "wiki" / "dependencies.md").read_text(encoding="utf-8")
        load = (tmp_path / "wiki" / "load-order.md").read_text(encoding="utf-8")
        assert "```mermaid" in deps
        assert "## Load order" in load

    def test_index_has_architecture_section(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki"))
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "## Architecture" in index
        assert "[Dependencies](dependencies.md)" in index
        assert "[Load order](load-order.md)" in index

    def test_skip_dependencies_omits_pages_and_section(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki", skip_dependencies=True))
        assert not (tmp_path / "wiki" / "dependencies.md").exists()
        assert not (tmp_path / "wiki" / "load-order.md").exists()
        index = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
        assert "## Architecture" not in index

    def test_shallow_depth_skips_pages(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(_make_args(src_dir=".", wiki_dir="wiki", depth="shallow"))
        assert not (tmp_path / "wiki" / "dependencies.md").exists()

    def test_json_summary_reports_dependencies(self, tmp_path, monkeypatch, capsys):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(
                src_dir=".", wiki_dir="wiki", format="json", source_adapter=True
            )
        )
        data = json.loads(capsys.readouterr().out)
        assert data["dependencies"]["generated"] is True
        assert data["dependencies"]["modules"] >= 2
        assert data["dependencies"]["undeclared"] == 0  # requests is declared

    def test_dependency_graph_detail_package_collapses(
        self, tmp_path, monkeypatch, capsys
    ):
        self._write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        bootstrap_cmd.run(
            _make_args(src_dir=".", wiki_dir="wiki", dependency_graph_detail="package")
        )
        deps = (tmp_path / "wiki" / "dependencies.md").read_text(encoding="utf-8")
        assert "Collapsed to top-level packages" in deps
